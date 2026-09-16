"""静态资源的存储与生命周期管理逻辑。

目录原则（日期优先）：
- 一天的博客资源集中存放在 static/{Y}/{M:02d}/{D:02d}/ 目录下，
  其中图片统一放在该日目录的 uploads/ 子文件夹中，按作用域分类：
    static/2026/09/07/uploads/post/     文章图片（编辑器插入 / 封面上传）
    static/2026/09/07/uploads/gallery/  图库图片（后台图片管理上传）
  uploads/ 的兄弟位预留存放该日的其他静态资源（如未来的附件 files/）；
- 站点级资产与日期无关，单独存放，不随日期目录散落：
    static/avatar/                      头像（站点身份标识，非某日博文资源）
- 月 / 日补零，保证字典序与时间序一致，按日期浏览和归档更直观；
- 旧布局的 URL 仍被识别，历史文章中的旧链接（若文件尚存）不受影响：
    static/uploads/posts|gallery/YYYY/MM/DD/   （作用域优先，旧）
    static/uploads/YYYY/MM/DD/                 （最早的无作用域遗留目录）
- 作用域语义：
  - post：仅随所属文章展示，文章编辑 / 删除时同步清理；
  - gallery：由管理员在图库中管理，不随文章删除，引用解除后回到图片栏；
  - avatar：账号资料，更换头像时删除旧文件。
- 衍生档：post / gallery 上传时按主图额外生成 @1024 / @400 的 WebP 缩略图，
  原图保持原样作为无损存档。衍生档由主图文件名派生，因此删除主图时必须一并清理，
  统一入口是 delete_image_files()——任何删除入口都不要直接 Path.unlink()，否则会留下孤儿衍生图。
"""
import io
import logging
import re
import uuid
from datetime import datetime
from pathlib import Path
from typing import NamedTuple

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.exceptions import BizException
from app.models.post import Post, PostStatus

logger = logging.getLogger("bluemoon")

# 旧布局的 URL 前缀（仅用于识别历史数据，新上传不再产生）
POST_IMAGE_PREFIX = "/static/uploads/posts/"
GALLERY_IMAGE_PREFIX = "/static/uploads/gallery/"
AVATAR_IMAGE_PREFIX = "/static/uploads/avatars/"
UPLOAD_URL_PREFIX = "/static/uploads/"


# 站点级长期资产目录（与日期无关，不随日期目录散落，也不会被任何清理逻辑删除）
SITE_ASSET_DIR = Path("avatar")
GALLERY_ASSET_DIR = Path("gallery")


# ---------------- 衍生档（WebP 缩略图） ----------------
# 上传时按主图额外生成 WebP 衍生档：@400 供列表卡片，@1024 供首屏与正文。
# 原图保持原样不动，作为无损存档与「看大图」的来源。
#
# 命名规则：主图 xxx.jpg → xxx@1024.webp、xxx@400.webp。
# 衍生档完全由主图文件名派生，因此删除主图时能直接推导并一并清理 ——
# 这是「不留孤儿衍生图」的关键：所有删除入口都必须走 delete_image_files()，
# 不要在任何地方直接调用 Path.unlink()。
DERIVATIVE_SPECS: tuple[tuple[str, int], ...] = (("@1024", 1024), ("@400", 400))
DERIVATIVE_EXT = "webp"
# 不需要衍生档的格式：SVG 是矢量无需栅格化，GIF 转码会丢掉动画
_DERIVATIVE_SKIP_EXT = {".svg", ".gif"}
_DERIVATIVE_NAME_RE = re.compile(r"@(?:1024|400)\.webp$", re.IGNORECASE)


def is_derivative_name(name: str) -> bool:
    """文件名是否为衍生档。

    图库列表必须据此排除，否则同一张图会以「原图 + 两个衍生档」重复出现。
    """
    return bool(_DERIVATIVE_NAME_RE.search(name))


def derivative_paths(main_path: Path) -> list[Path]:
    """由主图路径推导出全部衍生档路径（只做推导，不判断是否存在）。"""
    return [
        main_path.with_name(f"{main_path.stem}{suffix}.{DERIVATIVE_EXT}")
        for suffix, _ in DERIVATIVE_SPECS
    ]


def needs_derivatives(path: Path) -> bool:
    """该文件是否参与衍生档生成。

    上传链路与历史回填脚本共用这一判断，避免两处规则各写一份后逐渐不同步。
    """
    return path.suffix.lower() not in _DERIVATIVE_SKIP_EXT


def date_upload_dir(now: datetime, scope: str) -> Path:
    """日期优先布局的资源相对目录：{Y}/{M:02d}/{D:02d}/uploads/{scope}。

    仅用于"当日博文资源"（目前为文章图片 post）；
    长期保存的资源请用 avatar_dir() / gallery_dir()。
    未来其他静态资源可在 uploads/ 同级扩展（如 files/）。
    """
    return Path(f"{now.year}") / f"{now.month:02d}" / f"{now.day:02d}" / "uploads" / scope


def avatar_dir() -> Path:
    """站点级头像目录：static/avatar/。

    不按日期分目录——头像是站点身份标识而非某日的博文资源；
    文件名仍带时间戳（avatar_YYYYMMDDHHMMSS_随机.jpg），
    换头像后 URL 变化，浏览器 / CDN 缓存天然失效；
    更换头像不删除旧文件，旧文件作为历史头像归档保留。
    """
    return SITE_ASSET_DIR


def gallery_dir() -> Path:
    """站点级图库目录：static/gallery/（长期存储）。

    图库图片是长期资产：不放在日期目录（避免被视为临时/当期产物），
    不参与随文生命周期清理，也不会被任何自动清理任务删除；
    只有管理员在后台显式删除时才会移除。
    """
    return GALLERY_ASSET_DIR


def latest_gallery_image() -> str | None:
    """图库中最新的一张主图 URL（供首页首屏 banner 提前下发）。

    只扫长期图库目录 static/gallery/，**不查数据库**：首页 banner 只需要一张图，
    而 API 层的 list_images 会对每张图执行一次 referenced_by_posts 查询，代价过高。

    :return: 形如 "/static/gallery/xxx.jpg" 的 URL；图库为空时返回 None
    """
    # gallery_dir() 返回的是相对 static 根的目录名，必须与 static_path 拼接
    # （与 store_image 内部 `settings.static_path / rel_dir` 是同一约定）
    root = settings.static_path / gallery_dir()
    if not root.is_dir():
        return None
    newest: Path | None = None
    newest_mtime = -1.0
    for p in root.rglob("*"):
        if not p.is_file() or is_derivative_name(p.name):
            continue
        if p.suffix.lower().lstrip(".") not in settings.allowed_ext_set:
            continue
        try:
            mtime = p.stat().st_mtime
        except OSError:
            continue
        if mtime > newest_mtime:
            newest_mtime = mtime
            newest = p
    if newest is None:
        return None
    return f"/static/{newest.relative_to(settings.static_path).as_posix()}"


def is_long_term_asset(url: str | None) -> bool:
    """判断 URL 是否属于长期保存的站点级资产（头像 / 图库）。"""
    if not url or not url.startswith("/static/"):
        return False
    return url.startswith("/static/avatar/") or url.startswith("/static/gallery/")


# 从 Markdown 正文 / 封面中提取随文管理图片 URL：
# 覆盖三代布局（新日期优先 / 旧作用域优先 / 最早遗留日期目录）；
# gallery / avatar 作用域不在此列（文件名由服务端生成，字符集安全）
_POST_URL_RES = (
    re.compile(r"/static/\d{4}/\d{2}/\d{2}/uploads/post/[A-Za-z0-9._\-/]+"),  # 新：日期优先
    re.compile(r"/static/uploads/posts/[A-Za-z0-9._\-/]+"),                   # 旧：作用域优先
    re.compile(r"/static/uploads/\d{4}/[A-Za-z0-9._\-/]+"),                   # 旧：遗留日期目录
)

# 文章图片作用域（post scope，新 / 旧布局）：用于图库删除防护
_POST_SCOPE_RES = (
    re.compile(r"^/static/\d{4}/\d{2}/\d{2}/uploads/post/"),
    re.compile(r"^/static/uploads/posts/"),
)

# 随文生命周期管理的作用域：post 作用域（新 / 旧）+ 遗留日期目录
_MANAGED_URL_RES = _POST_SCOPE_RES + (
    re.compile(r"^/static/uploads/\d{4}/"),
)


def is_post_image(url: str | None) -> bool:
    """判断 URL 是否属于文章图片（post 作用域，新 / 旧布局）。

    仅用于图库删除防护：遗留目录图片仍允许管理员在图库中手动删除。
    """
    return bool(url) and any(r.match(url) for r in _POST_SCOPE_RES)


def is_post_managed(url: str | None) -> bool:
    """判断 URL 是否纳入随文生命周期管理。

    覆盖新日期布局的 post 目录、旧 posts 目录与遗留日期目录；
    gallery / avatar 作用域不属于随文管理：图库图片由管理员维护，
    即使被文章引用后引用解除，文件也保留在图库中。
    """
    return bool(url) and any(r.match(url) for r in _MANAGED_URL_RES)


def extract_post_image_urls(post: Post) -> set[str]:
    """提取文章引用的全部随文管理图片 URL（封面 + 正文）。"""
    urls: set[str] = set()
    if is_post_managed(post.cover):
        urls.add(post.cover)
    if post.content:
        for pattern in _POST_URL_RES:
            urls.update(m.group(0) for m in pattern.finditer(post.content))
    return urls


# ---------------- 通用文件工具（upload 接口共用） ----------------
def resolve_image_path(url: str) -> Path:
    """将图片 URL 解析为本地绝对路径，并做路径穿越校验。"""
    if not url.startswith("/static/"):
        raise BizException("非法的图片地址")
    rel = url[len("/static/"):].lstrip("/")
    target = (settings.static_path / rel).resolve()
    static_root = settings.static_path.resolve()
    if target != static_root and static_root not in target.parents:
        raise BizException("非法的图片地址")
    return target


def cleanup_empty_dirs(path: Path, stop_at: Path):
    """自底向上清理空目录，直到 stop_at。"""
    current = path.parent
    stop_at_resolved = stop_at.resolve()
    while current.resolve() != stop_at_resolved and stop_at_resolved in current.resolve().parents:
        try:
            if any(current.iterdir()):
                break  # 目录非空，停止
            current.rmdir()
            current = current.parent
        except OSError:
            break  # 删除失败（权限等），停止


def _write_derivatives(main_abs: Path, content: bytes) -> None:
    """为主图生成 WebP 衍生档。

    失败只记日志不抛错：主图此时已落盘，衍生档缺失只影响加载体积，
    前端有 onerror 回退原图兜底，不该因此让整个上传失败。
    """
    if not needs_derivatives(main_abs):
        return
    try:
        from PIL import Image, ImageOps
    except ImportError:  # pragma: no cover - 环境缺 Pillow 时降级为不生成
        logger.warning("Pillow 不可用，跳过衍生档生成：%s", main_abs.name)
        return
    try:
        with Image.open(io.BytesIO(content)) as im:
            im = ImageOps.exif_transpose(im)  # 按 EXIF 摆正，避免手机竖拍图侧躺
            for suffix, box in DERIVATIVE_SPECS:
                out = im.copy()
                out.thumbnail((box, box), Image.LANCZOS)
                if out.mode not in ("RGB", "RGBA"):
                    out = out.convert("RGB")  # WebP 只接受 RGB / RGBA
                out.save(
                    main_abs.with_name(f"{main_abs.stem}{suffix}.{DERIVATIVE_EXT}"),
                    "WEBP",
                    quality=80,
                    method=5,
                )
    except Exception as exc:  # noqa: BLE001
        logger.warning("衍生档生成失败 %s: %s", main_abs.name, exc)


# ---------------- 上传内容校验 ----------------
# 允许的「扩展名 → 真实格式」映射：PIL 报的 format 名与扩展名需要对应，
# 否则改名绕过（把 .php/.svg/.html 改成 .jpg）就能混进 static。
_EXT_FORMAT_ALIASES = {
    "jpg": {"jpeg", "jpg"},
    "jpeg": {"jpeg", "jpg"},
    "png": {"png", "apng"},
    "gif": {"gif"},
    "webp": {"webp"},
    "bmp": {"bmp", "dib"},
}


def validate_image_bytes(content: bytes, ext: str) -> tuple[str, int, int]:
    """校验上传内容确实是图片，返回 (真实格式, 宽, 高)。

    两道防线：
    1. **真实格式**——只查扩展名可被改名绕过；这里用 Pillow 解码头部确认格式与扩展名一致；
    2. **解压炸弹**——宽×高超过 settings.IMAGE_MAX_PIXELS 直接拒绝
       （几十 KB 的 PNG 能解出几 GB 位图，瞬间打满内存）。

    校验失败抛 BizException（调用方直接 400，不做「回退原图」式兜底）。
    """
    try:
        from PIL import Image, UnidentifiedImageError
    except ImportError:  # pragma: no cover - 环境缺 Pillow 时只按扩展名放行
        logger.warning("Pillow 不可用，跳过图片内容校验：%s", ext)
        return (ext, 0, 0)

    try:
        with Image.open(io.BytesIO(content)) as im:
            fmt = (im.format or "").lower()
            width, height = im.size
    except UnidentifiedImageError:
        raise BizException("文件内容不是有效图片")
    except Image.DecompressionBombError:
        raise BizException("图片尺寸过大，请先压缩后再上传")
    except (OSError, ValueError) as exc:
        raise BizException(f"图片解析失败：{exc}")

    allowed_formats = _EXT_FORMAT_ALIASES.get(ext.lower())
    if allowed_formats and fmt not in allowed_formats:
        raise BizException(f"文件内容与扩展名不符（实际为 {fmt or '未知'}）")
    if width * height > settings.IMAGE_MAX_PIXELS:
        raise BizException(
            f"图片像素过大（{width}×{height}），上限 {settings.IMAGE_MAX_PIXELS // 10000} 万像素"
        )
    return (fmt, width, height)


def store_image(
    content: bytes,
    rel_dir: Path,
    ext: str,
    prefix: str = "",
    derivatives: bool = True,
) -> tuple[str, str]:
    """把上传的图片写入 static 下指定相对目录（自动创建），返回 (url, filename)。

    文件名统一为 `[前缀]YYYYMMDDHHMMSS_<8位随机>.<ext>`，时间戳前缀可供图库列表解析上传时间。
    上传接口（upload / avatar）共用，保证命名与落盘规则一致。

    derivatives=True 时额外生成 WebP 衍生档（见 DERIVATIVE_SPECS）；
    头像调用方传 False —— 头像在上游已用 PIL 裁切压缩过，再生成衍生档纯属冗余。
    """
    now = datetime.now()
    filename = f"{prefix}{now.strftime('%Y%m%d%H%M%S')}_{uuid.uuid4().hex[:8]}.{ext}"
    abs_dir = settings.static_path / rel_dir
    abs_dir.mkdir(parents=True, exist_ok=True)
    abs_path = abs_dir / filename
    abs_path.write_bytes(content)
    if derivatives:
        _write_derivatives(abs_path, content)
    url = f"/static/{(rel_dir / filename).as_posix()}"
    return url, filename


def referenced_by_posts(db: Session, url: str, exclude_post_id: int | None = None) -> list[Post]:
    """查询引用了指定图片 URL 的文章（封面或正文，含草稿）。

    ⚠️ 单次调用成本高（`content LIKE '%url%'` 前导通配符无法走索引 → TEXT 全表扫描）。
    批量场景（图库列表 / 批量删除 / 批量引用检查）请改用 build_reference_index()，
    一次查询建索引后在内存里比对，否则会退化成 N 次全表扫描。
    """
    from sqlalchemy import or_

    q = db.query(Post).filter(or_(Post.cover == url, Post.content.like(f"%{url}%")))
    if exclude_post_id:
        q = q.filter(Post.id != exclude_post_id)
    return q.all()


class PostRef(NamedTuple):
    """引用索引里的轻量文章记录（避免把整篇正文常驻内存）"""

    id: int
    title: str
    cover: str | None
    is_published: bool


# 正文里出现的任何站内静态资源 URL（含 gallery / avatar / 日期目录 / 衍生档 @1024）
_ALL_STATIC_URL_RE = re.compile(r"/static/[A-Za-z0-9._\-/@]+")


def build_reference_index(db: Session) -> dict[str, list[PostRef]]:
    """一次查询建立「图片 URL → 引用它的文章列表」索引。

    替代「每张图一次 referenced_by_posts」的 N 次全表扫描：
    图库一次列上百张图时，原本要对 posts.content 做上百次全表扫描。
    """
    rows = db.query(Post.id, Post.title, Post.cover, Post.content, Post.status).all()
    index: dict[str, list[PostRef]] = {}
    for pid, title, cover, content, status in rows:
        ref = PostRef(pid, title, cover, status == PostStatus.PUBLISHED)
        urls: set[str] = set()
        if cover and cover.startswith("/static/"):
            urls.add(cover)
        if content:
            urls.update(_ALL_STATIC_URL_RE.findall(content))
        for u in urls:
            index.setdefault(u, []).append(ref)
    return index


def indexed_references(
    index: dict[str, list[PostRef]], url: str, exclude_post_id: int | None = None
) -> list[PostRef]:
    """在内存索引里查引用（不碰数据库）"""
    refs = index.get(url) or []
    if exclude_post_id:
        return [r for r in refs if r.id != exclude_post_id]
    return list(refs)


# ---------------- 生命周期同步 ----------------
def delete_image_files(url: str) -> bool:
    """删除 URL 对应文件及其全部衍生档，并清理空目录。

    主图与衍生档必须在同一处删除，否则会留下孤儿衍生图 —— 因此图库删除
    （upload.py）与随文清理（sync_post_images / remove_post_images）都必须
    调用本函数，不要在任何地方直接调用 Path.unlink()。
    返回是否至少删掉了一个文件。
    """
    try:
        target = resolve_image_path(url)
    except BizException:
        return False

    removed = False
    for path in (target, *derivative_paths(target)):
        if not path.is_file():
            continue
        try:
            path.unlink()
            removed = True
        except OSError as exc:
            logger.warning("删除文件失败 %s: %s", path, exc)

    if removed:
        # 新布局日期目录可能整体变空，清理到 static 根为止（只删空目录，安全）
        cleanup_empty_dirs(target, settings.static_path)
    return removed


def sync_post_images(db: Session, post: Post, old_urls: set[str]) -> None:
    """文章更新后调用：清理不再被引用的随文图片文件。

    old_urls 为更新前提取的图片 URL 集合；更新提交后调用本函数，
    对"更新前有、更新后无"的图片，若已无任何其他文章引用则删除文件。
    仅处理随文管理作用域（posts / 遗留日期目录）；图库图片不随文删除。
    """
    new_urls = extract_post_image_urls(post)
    removed = old_urls - new_urls
    if not removed:
        return
    # 一次建索引，避免「每个被移除的图片各查一次全表」
    index = build_reference_index(db)
    for url in removed:
        if not is_post_managed(url):
            continue  # gallery 等作用域由管理员管理，不随文清理
        if indexed_references(index, url, exclude_post_id=post.id):
            continue  # 其他文章仍在引用，保留
        if delete_image_files(url):
            logger.info("cleaned orphan post image %s (post %s)", url, post.id)


def remove_post_images(db: Session, urls: set[str], post_id: int | None = None) -> None:
    """文章删除后调用：删除该文章引用的随文图片文件。

    仅删除已无任何其他文章引用的文件；图库图片（gallery 作用域）不受影响。
    与 sync_post_images 一样走「一次索引 + 内存比对」，不逐张查库。
    """
    index = build_reference_index(db)
    for url in urls:
        if not is_post_managed(url):
            continue  # 封面等可能指向图库图片，归图库管理
        if indexed_references(index, url, exclude_post_id=post_id):
            continue  # 其他文章仍在引用，保留
        if delete_image_files(url):
            logger.info(
                "removed post image %s after post %s deleted", url, post_id
            )
