"""文章图片（随文图片）的存储与同步清理逻辑。

设计：
- 新上传的文章图片（编辑器插入 / 封面上传）统一存放在 static/uploads/posts/ 下，
  与图库图片（static/uploads/gallery/）物理隔离；
- 历史遗留图片（static/uploads/YYYY/MM/DD/ 日期目录）虽与图库混放，
  但同样纳入随文生命周期管理：被文章引用、随后引用消失且无其他文章
  引用时，文件会被同步删除；
- 图库列表接口只返回图库图片与遗留目录图片，新文章图片不会出现在网站图片栏；
- 随文图片的生命周期跟随所属文章：
  - 编辑文章时，被移除引用且无其他文章引用的图片文件会被同步删除；
  - 删除文章时，该文章独占的图片文件会被同步删除；
  - 图片文件被多篇文章共用时，仅在最后一处引用消失后才删除文件；
  - gallery 作用域的图片由管理员在图库中管理，不随文章删除。
"""
import logging
import re
import uuid
from datetime import datetime
from pathlib import Path

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.exceptions import BizException
from app.models.post import Post

logger = logging.getLogger("bluemoon")

# 文章图片 URL 前缀（与 upload 接口的 post scope 保持一致）
POST_IMAGE_PREFIX = "/static/uploads/posts/"
GALLERY_IMAGE_PREFIX = "/static/uploads/gallery/"
AVATAR_IMAGE_PREFIX = "/static/uploads/avatars/"
UPLOAD_URL_PREFIX = "/static/uploads/"

# 从 Markdown 正文 / 封面中提取随文管理图片 URL：
# 覆盖新 posts 目录与历史遗留日期目录（uploads/YYYY/...）；
# gallery / avatars 作用域不在此列（文件名由服务端生成，字符集安全）
_POST_URL_RE = re.compile(r"/static/uploads/(?:posts|\d{4})/[A-Za-z0-9._\-/]+")


def is_post_image(url: str | None) -> bool:
    """判断 URL 是否属于新文章图片（posts 作用域）。

    仅用于图库删除防护：遗留目录图片仍允许管理员在图库中手动删除。
    """
    return bool(url) and url.startswith(POST_IMAGE_PREFIX)


def is_post_managed(url: str | None) -> bool:
    """判断 URL 是否纳入随文生命周期管理（posts 目录 + 历史遗留日期目录）。

    gallery / avatars 作用域不属于随文管理：图库图片由管理员维护，
    即使被文章引用后引用解除，文件也保留在图库中。
    """
    if not url or not url.startswith(UPLOAD_URL_PREFIX):
        return False
    return not (
        url.startswith(GALLERY_IMAGE_PREFIX) or url.startswith(AVATAR_IMAGE_PREFIX)
    )


def extract_post_image_urls(post: Post) -> set[str]:
    """提取文章引用的全部随文管理图片 URL（封面 + 正文）。"""
    urls: set[str] = set()
    if is_post_managed(post.cover):
        urls.add(post.cover)
    if post.content:
        urls.update(m.group(0) for m in _POST_URL_RE.finditer(post.content))
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


def store_image(content: bytes, rel_dir: Path, ext: str, prefix: str = "") -> tuple[str, str]:
    """把上传的图片写入 static 下指定相对目录（自动创建），返回 (url, filename)。

    文件名统一为 `[前缀]YYYYMMDDHHMMSS_<8位随机>.<ext>`，时间戳前缀可供图库列表解析上传时间。
    上传接口（upload / avatar）共用，保证命名与落盘规则一致。
    """
    now = datetime.now()
    filename = f"{prefix}{now.strftime('%Y%m%d%H%M%S')}_{uuid.uuid4().hex[:8]}.{ext}"
    abs_dir = settings.static_path / rel_dir
    abs_dir.mkdir(parents=True, exist_ok=True)
    (abs_dir / filename).write_bytes(content)
    url = f"/static/{(rel_dir / filename).as_posix()}"
    return url, filename


def referenced_by_posts(db: Session, url: str, exclude_post_id: int | None = None) -> list[Post]:
    """查询引用了指定图片 URL 的文章（封面或正文，含草稿）。"""
    q = db.query(Post).filter(or_(Post.cover == url, Post.content.like(f"%{url}%")))
    if exclude_post_id:
        q = q.filter(Post.id != exclude_post_id)
    return q.all()


# ---------------- 生命周期同步 ----------------
def _delete_file_for_url(url: str) -> bool:
    """删除 URL 对应的本地文件并清理空目录，文件不存在时静默跳过。"""
    try:
        target = resolve_image_path(url)
    except BizException:
        return False
    if not target.is_file():
        return False
    try:
        target.unlink()
    except OSError:
        return False
    cleanup_empty_dirs(target, settings.upload_path)
    return True


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
    for url in removed:
        if not is_post_managed(url):
            continue  # gallery 等作用域由管理员管理，不随文清理
        if referenced_by_posts(db, url):
            continue  # 其他文章仍在引用，保留
        if _delete_file_for_url(url):
            logger.info("cleaned orphan post image %s (post %s)", url, post.id)


def remove_post_images(db: Session, urls: set[str], post_id: int | None = None) -> None:
    """文章删除后调用：删除该文章引用的随文图片文件。

    仅删除已无任何其他文章引用的文件；图库图片（gallery 作用域）不受影响。
    """
    for url in urls:
        if not is_post_managed(url):
            continue  # 封面等可能指向图库图片，归图库管理
        if referenced_by_posts(db, url, exclude_post_id=post_id):
            continue  # 其他文章仍在引用，保留
        if _delete_file_for_url(url):
            logger.info(
                "removed post image %s after post %s deleted", url, post_id
            )
