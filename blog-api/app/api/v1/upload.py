"""图片上传 / 图片管理

静态资源按"日期优先"层级目录存储，一天的资源集中在一个日期目录下：
- static/{Y}/{M:02d}/{D:02d}/uploads/post/...     文章图片：编辑器插入 / 封面上传，
  仅随所属文章展示，由文章的编辑 / 删除同步管理；
- static/{Y}/{M:02d}/{D:02d}/uploads/gallery/...  图库图片：管理员在图片后台上传，
  展示在网站图片栏（/images）；
- uploads/ 的兄弟位预留存放该日其他静态资源（如附件 files/）。
旧布局（uploads/{scope}/... 与 uploads/YYYY/...）的 URL 仍被识别，历史链接不受影响。

性能约定：图片引用检查一律走 image_service.build_reference_index()
（一次查询建内存索引），不要在循环里调用单张查询 —— 后者是
`content LIKE '%url%'` 全表扫描，图库列上百张图就会退化成上百次全表扫描。
"""
from datetime import datetime
from pathlib import Path
from typing import Dict, List

from fastapi import APIRouter, Depends, File, Query, UploadFile
from sqlalchemy.orm import Session

from app.api.deps import get_current_admin, get_db
from app.core.config import settings
from app.core.exceptions import BizException
from app.core.response import success
from app.models.user import User
from app.services.cache import K_IMAGE_LIST, cache, invalidate_image_list, make_key
from app.services.image_service import (
    PostRef,
    build_reference_index,
    date_upload_dir,
    delete_image_files,
    gallery_dir,
    indexed_references,
    is_derivative_name,
    is_long_term_asset,
    is_post_image,
    resolve_image_path,
    store_image,
    validate_image_bytes,
)

router = APIRouter(prefix="/upload", tags=["上传"])

# 图库列表需排除的作用域段（覆盖新 / 旧布局）：uploads 下的这些子目录不是图库
_NON_GALLERY_SCOPE_SEGMENTS = ("posts", "post", "avatars", "avatar")
# 站点级资产目录（头像等），与日期 / 图库无关，同样不在图库中展示
_SITE_ASSET_DIRS = ("avatar",)


def _guard_deletable(url: str):
    """图库删除接口的统一防护。

    - 文章图片：由所属文章管理生命周期，禁止在此删除；
    - 站点级长期资产（头像等）：有各自的归档与接口，绕过它们直接删文件
      会留下悬空的历史记录（如 user_avatars 指向已不存在的文件），同样禁止。
    """
    if is_post_image(url):
        raise BizException("文章图片由所属文章管理，不能在图库中删除")
    if is_long_term_asset(url):
        raise BizException("该图片属于站点长期资产（头像等），请在对应管理页操作")


def _read_upload(file: UploadFile, limit: int) -> bytes:
    """限制读取上限：超限立刻拒绝，不把超大文件整体读进内存。

    端点用同步 def（FastAPI 会放进线程池），因此这里直接读 file.file。
    """
    content = file.file.read(limit + 1)
    if len(content) > limit:
        raise BizException(f"文件过大，不能超过 {limit / 1024 / 1024:.0f}MB")
    if not content:
        raise BizException("文件内容为空")
    return content


@router.post("/image", summary="上传图片（管理员）")
def upload_image(
    file: UploadFile = File(...),
    scope: str = Query(
        "gallery",
        description="图片作用域：post=文章图片（随文存储，不进图库）；gallery=图库图片",
    ),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    if scope not in ("post", "gallery"):
        raise BizException("scope 仅支持 post（文章图片）或 gallery（图库图片）")

    ext = Path(file.filename or "").suffix.lower().lstrip(".")
    if ext not in settings.allowed_ext_set:
        raise BizException(
            f"不支持的图片格式：{ext or '未知'}，允许：{', '.join(sorted(settings.allowed_ext_set))}"
        )

    content = _read_upload(file, settings.MAX_UPLOAD_SIZE)
    # 校验真实格式 + 像素上限（只查后缀会被改名绕过）
    validate_image_bytes(content, ext)

    now = datetime.now()
    if scope == "post":
        # 文章图片属于当日博文资源，按日期目录组织，随文章生命周期清理
        rel_dir = date_upload_dir(now, "post")
    else:
        # 图库图片是长期资产：统一存入站点级 static/gallery/，
        # 不进日期目录，也不被任何自动清理任务删除（仅管理员可显式删除）
        rel_dir = gallery_dir()
    url, filename = store_image(content, rel_dir, ext)
    if scope == "gallery":
        invalidate_image_list()
    return success({"url": url, "filename": filename, "size": len(content)}, msg="上传成功")


@router.get("/images", summary="列出未引用的独立图片（公开）")
def list_images(db: Session = Depends(get_db)):
    """扫描 static 下所有图片（排除文章图片与头像作用域），返回未被任何文章
    引用的独立图片清单，按上传时间倒序。

    覆盖新日期布局（{Y}/{M}/{D}/uploads/gallery/）与旧布局
    （uploads/gallery/、遗留日期目录），保证历史图片不丢；
    - 已被文章引用（封面或正文）的图片不出现在此列表中，
      它们只随所属文章展示，与文章保持关联；
    - 图片被文章引用解除后会重新回到本列表（图库图片不随文删除）。

    该接口要扫盘 + 查引用，代价明显高于普通读接口，因此结果做短时缓存
    （CACHE_TTL_IMAGE_LIST，默认 60s）：首页也会调它取封面兜底图，
    不缓存的话每次访问首页都要全量扫一遍。
    """

    def _producer() -> List[Dict]:
        root = settings.static_path
        items: List[Dict] = []
        if not root.exists():
            return items

        # 一次建索引：引用检查在内存里比对，避免「每张图一次全表扫描」
        index = build_reference_index(db)

        for p in root.rglob("*"):
            if not p.is_file():
                continue
            # 衍生档不是独立图片：它随主图展示，不能单独出现在图库里
            if is_derivative_name(p.name):
                continue
            # 按路径段排除非图库作用域（新旧布局统一处理）
            parts = p.relative_to(root).parts
            if parts and parts[0] in _SITE_ASSET_DIRS:
                continue  # 站点级资产：头像等
            if "uploads" in parts:
                i = parts.index("uploads")
                if len(parts) > i + 1 and parts[i + 1] in _NON_GALLERY_SCOPE_SEGMENTS:
                    continue
            ext = p.suffix.lower().lstrip(".")
            if ext not in settings.allowed_ext_set:
                continue

            try:
                stat = p.stat()
            except OSError:
                continue

            # 上传时间：优先从文件名前缀 YYYYMMDDHHMMSS_ 解析，失败回退到文件修改时间
            ts_part = p.name.split("_", 1)[0]
            try:
                uploaded_at = datetime.strptime(ts_part, "%Y%m%d%H%M%S")
            except ValueError:
                uploaded_at = datetime.fromtimestamp(stat.st_mtime)

            url = f"/static/{p.relative_to(root).as_posix()}"
            # 已被文章引用的图片只随文展示，不进入图片列表
            if indexed_references(index, url):
                continue
            items.append(
                {
                    "url": url,
                    "name": p.name,
                    "size": stat.st_size,
                    "uploaded_at": uploaded_at.strftime("%Y-%m-%d %H:%M:%S"),
                }
            )
        items.sort(key=lambda x: x["uploaded_at"], reverse=True)
        return items

    return success(
        cache.get_or_set(
            make_key(K_IMAGE_LIST, scope="all"),
            _producer,
            ttl=settings.CACHE_TTL_IMAGE_LIST,
        )
    )


def _check_image_references(index: Dict[str, List[PostRef]], url: str) -> List[str]:
    """检查图库图片是否被文章引用，返回引用它的文章标题列表（走内存索引，不查库）。"""
    referenced = []
    for p in indexed_references(index, url):
        if not p.is_published:
            continue  # 与历史行为保持一致：仅统计已发布文章
        if p.cover == url:
            referenced.append(f"《{p.title}》（封面）")
        else:
            label = f"《{p.title}》（正文）"
            if label not in referenced:
                referenced.append(label)
    return referenced


@router.delete("/image", summary="删除单张图片（管理员）")
def delete_image(
    url: str = Query(..., description="图片 url，形如 /static/2026/09/07/uploads/gallery/xxx.jpg"),
    force: bool = Query(False, description="是否强制删除（忽略引用检查）"),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    _guard_deletable(url)
    target = resolve_image_path(url)

    if not target.exists() or not target.is_file():
        raise BizException("图片不存在或已被删除")

    # 引用检查
    if not force:
        refs = _check_image_references(build_reference_index(db), url)
        if refs:
            raise BizException(
                f"该图片仍被 {len(refs)} 篇文章引用：" + "、".join(refs[:3])
                + ("…" if len(refs) > 3 else "")
                + "，请先解除引用后再删除"
            )

    # 主图与全部衍生档一并删除（内部会清理空目录），避免留下孤儿衍生图
    if not delete_image_files(url):
        raise BizException("删除失败：文件无法移除")

    invalidate_image_list()
    return success(msg="已删除")


@router.post("/image/batch-delete", summary="批量删除图片（管理员）")
def batch_delete_images(
    body: dict,
    force: bool = Query(False, description="是否强制删除（忽略引用检查）"),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    urls = body.get("urls") or []
    if not urls:
        raise BizException("请选择要删除的图片")

    if any(is_post_image(u) for u in urls):
        raise BizException("文章图片由所属文章管理，不能在图库中删除")
    if any(is_long_term_asset(u) for u in urls):
        raise BizException("选中项包含站点长期资产（头像等），请在对应管理页操作")

    success_count = 0
    failed = []
    skipped_refs = []

    # 建一次索引供整批复用（原实现是每个 URL 各查一次库）
    index = build_reference_index(db) if not force else {}

    for url in urls:
        try:
            target = resolve_image_path(url)
        except BizException as e:
            failed.append({"url": url, "reason": str(e)})
            continue

        if not target.exists() or not target.is_file():
            failed.append({"url": url, "reason": "文件不存在"})
            continue

        # 引用检查
        if not force:
            refs = _check_image_references(index, url)
            if refs:
                skipped_refs.append({"url": url, "name": Path(url).name, "refs": refs})
                continue

        # 同上：走统一删除函数，主图 + 衍生档一起清掉
        if delete_image_files(url):
            success_count += 1
        else:
            failed.append({"url": url, "reason": "删除失败：文件无法移除"})

    if success_count:
        invalidate_image_list()

    result = {
        "success": success_count,
        "failed": failed,
        "skipped_refs": skipped_refs,
        "total": len(urls),
    }

    if success_count == 0 and not skipped_refs:
        return success(result, msg="没有图片被删除")

    msg = f"已删除 {success_count} 张"
    if failed:
        msg += f"，失败 {len(failed)} 张"
    if skipped_refs:
        msg += f"，{len(skipped_refs)} 张因被引用而跳过"

    return success(result, msg=msg)


@router.post("/image/check-refs", summary="检查图片引用情况（管理员）")
def check_image_references(
    body: dict,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    """批量检查图片是否被文章引用，用于删除前确认。整批只查一次库。"""
    urls: List[str] = body.get("urls") or []
    index = build_reference_index(db) if urls else {}
    results = []
    for url in urls:
        refs = _check_image_references(index, url)
        results.append({
            "url": url,
            "name": Path(url).name,
            "referenced": len(refs) > 0,
            "ref_count": len(refs),
            "ref_posts": refs[:5],  # 最多返回 5 篇
        })
    return success(results)
