"""图片上传 / 图片管理

图片按作用域（scope）物理分目录存储，互不干扰：
- post    → static/uploads/posts/...   文章图片：编辑器插入 / 封面上传，
            仅随所属文章展示，由文章的编辑 / 删除同步管理；
- gallery → static/uploads/gallery/... 图库图片：管理员在图片后台上传，
            展示在网站图片栏（/images）。
"""
from datetime import datetime
from pathlib import Path
from typing import List

from fastapi import APIRouter, Depends, File, Query, UploadFile
from sqlalchemy.orm import Session

from app.api.deps import get_current_admin, get_db
from app.core.config import settings
from app.core.exceptions import BizException
from app.core.response import success
from app.models.post import Post
from app.models.user import User
from app.services.image_service import (
    cleanup_empty_dirs,
    is_post_image,
    referenced_by_posts,
    resolve_image_path,
    store_image,
)

router = APIRouter(prefix="/upload", tags=["上传"])


def _guard_not_post_image(url: str):
    """图库删除接口的防护：文章图片由所属文章管理生命周期，禁止在此删除。"""
    if is_post_image(url):
        raise BizException("文章图片由所属文章管理，不能在图库中删除")


@router.post("/image", summary="上传图片（管理员）")
async def upload_image(
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

    content = await file.read()
    if len(content) > settings.MAX_UPLOAD_SIZE:
        limit_mb = settings.MAX_UPLOAD_SIZE / 1024 / 1024
        raise BizException(f"图片过大，不能超过 {limit_mb:.0f}MB")

    now = datetime.now()
    # 按作用域分目录存储：文章图片与图库图片物理隔离
    scope_dir = "posts" if scope == "post" else "gallery"
    rel_dir = Path("uploads") / scope_dir / f"{now.year}" / f"{now.month:02d}" / f"{now.day:02d}"
    url, filename = store_image(content, rel_dir, ext)
    return success({"url": url, "filename": filename, "size": len(content)}, msg="上传成功")


@router.get("/images", summary="列出未引用的独立图片（公开）")
async def list_images(db: Session = Depends(get_db)):
    """扫描图库目录（uploads/gallery 及历史遗留日期目录），返回未被任何文章
    引用的独立图片清单，按上传时间倒序。

    - 已被文章引用（封面或正文）的图片不出现在此列表中，
      它们只随所属文章展示，与文章保持关联；
    - 文章图片（uploads/posts/）与头像（uploads/avatars/）同样不在此列；
    - 图片被文章引用解除后会重新回到本列表（图库图片不随文删除）。
    """
    root = settings.static_path
    upload_root = settings.upload_path
    items = []
    if upload_root.exists():
        for p in upload_root.rglob("*"):
            if not p.is_file():
                continue
            rel_parts = p.relative_to(upload_root).parts
            if rel_parts and rel_parts[0] in ("avatars", "posts"):
                continue
            ext = p.suffix.lower().lstrip(".")
            if ext not in settings.allowed_ext_set:
                continue
            # 上传时间：优先从文件名前缀 YYYYMMDDHHMMSS_ 解析，失败回退到文件修改时间
            uploaded_at = None
            ts_part = p.name.split("_", 1)[0]
            try:
                uploaded_at = datetime.strptime(ts_part, "%Y%m%d%H%M%S")
            except ValueError:
                uploaded_at = datetime.fromtimestamp(p.stat().st_mtime)
            rel = p.relative_to(root).as_posix()
            url = f"/static/{rel}"
            # 已被文章引用的图片只随文展示，不进入图片列表
            if referenced_by_posts(db, url):
                continue
            items.append(
                {
                    "url": url,
                    "name": p.name,
                    "size": p.stat().st_size,
                    "uploaded_at": uploaded_at.strftime("%Y-%m-%d %H:%M:%S"),
                }
            )
    items.sort(key=lambda x: x["uploaded_at"], reverse=True)
    return success(items)


def _check_image_references(db: Session, url: str) -> List[str]:
    """检查图库图片是否被文章引用，返回引用它的文章标题列表。"""
    referenced = []
    for p in referenced_by_posts(db, url):
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
async def delete_image(
    url: str = Query(..., description="图片 url，形如 /static/uploads/gallery/2026/09/xxx.jpg"),
    force: bool = Query(False, description="是否强制删除（忽略引用检查）"),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    _guard_not_post_image(url)
    target = resolve_image_path(url)

    if not target.exists() or not target.is_file():
        raise BizException("图片不存在或已被删除")

    # 引用检查
    if not force:
        refs = _check_image_references(db, url)
        if refs:
            raise BizException(
                f"该图片仍被 {len(refs)} 篇文章引用：" + "、".join(refs[:3])
                + ("…" if len(refs) > 3 else "")
                + "，请先解除引用后再删除"
            )

    try:
        target.unlink()
    except OSError as e:
        raise BizException(f"删除失败：{e}")

    # 清理空目录
    cleanup_empty_dirs(target, settings.upload_path)

    return success(msg="已删除")


@router.post("/image/batch-delete", summary="批量删除图片（管理员）")
async def batch_delete_images(
    body: dict,
    force: bool = Query(False, description="是否强制删除（忽略引用检查）"),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    urls = body.get("urls") or []
    if not urls:
        raise BizException("请选择要删除的图片")

    post_urls = [u for u in urls if is_post_image(u)]
    if post_urls:
        raise BizException("文章图片由所属文章管理，不能在图库中删除")

    success_count = 0
    failed = []
    skipped_refs = []

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
            refs = _check_image_references(db, url)
            if refs:
                skipped_refs.append({"url": url, "name": Path(url).name, "refs": refs})
                continue

        try:
            target.unlink()
            cleanup_empty_dirs(target, settings.upload_path)
            success_count += 1
        except OSError as e:
            failed.append({"url": url, "reason": f"删除失败：{e}"})

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
async def check_image_references(
    body: dict,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    """批量检查图片是否被文章引用，用于删除前确认。"""
    urls = body.get("urls") or []
    results = []
    for url in urls:
        refs = _check_image_references(db, url)
        results.append({
            "url": url,
            "name": Path(url).name,
            "referenced": len(refs) > 0,
            "ref_count": len(refs),
            "ref_posts": refs[:5],  # 最多返回 5 篇
        })
    return success(results)
