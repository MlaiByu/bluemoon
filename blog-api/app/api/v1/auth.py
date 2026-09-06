"""认证接口"""
from datetime import datetime
from io import BytesIO
from pathlib import Path

from fastapi import APIRouter, Depends, File, Request, UploadFile
from PIL import Image
from sqlalchemy.orm import Session

from app.api.deps import get_current_admin, get_db
from app.core.config import settings
from app.core.exceptions import BizException
from app.core.response import success
from app.models.user import User
from app.schemas.user import ChangePasswordIn, LoginIn, UserOut, UserUpdateIn
from app.services import auth_service, image_service
from app.services.cache import K_PROFILE, K_SITE, cache, make_key

router = APIRouter(prefix="/auth", tags=["认证"])

# 头像最大边长（像素）
AVATAR_MAX_SIZE = 512
# 头像允许的格式
AVATAR_ALLOWED_EXT = {"jpg", "jpeg", "png", "gif", "webp"}
# 头像最大文件大小（字节）
AVATAR_MAX_BYTES = 5 * 1024 * 1024  # 5MB


def _process_avatar_image(content: bytes, ext: str) -> bytes:
    """缩放头像图片，保持宽高比，最大边不超过 AVATAR_MAX_SIZE。"""
    try:
        img = Image.open(BytesIO(content))

        # 处理 GIF：保留第一帧
        if img.format == "GIF":
            img = img.convert("RGBA")

        # 已经够小了，不处理
        if max(img.width, img.height) <= AVATAR_MAX_SIZE:
            return content

        # 计算缩放比例
        ratio = AVATAR_MAX_SIZE / max(img.width, img.height)
        new_size = (int(img.width * ratio), int(img.height * ratio))

        # 使用高质量缩放
        img = img.resize(new_size, Image.LANCZOS)

        # 根据扩展名保存
        output = BytesIO()
        save_format = "PNG" if ext in ("png", "gif") else "JPEG"
        if save_format == "JPEG" and img.mode in ("RGBA", "P"):
            img = img.convert("RGB")
        img.save(output, format=save_format, quality=90, optimize=True)
        return output.getvalue()
    except Exception:
        # 图片处理失败，返回原图
        return content


@router.post("/login", summary="管理员登录")
def login(
    payload: LoginIn,
    db: Session = Depends(get_db),
):
    result = auth_service.login(db, payload.username, payload.password)
    return success(
        {
            "access_token": result["access_token"],
            "token_type": result["token_type"],
            "expires_in": result["expires_in"],
            "user": UserOut.model_validate(result["user"]).model_dump(mode="json"),
        },
        msg="登录成功",
    )


@router.post("/logout", summary="退出登录")
def logout(
    request: Request,
    current_user: User = Depends(get_current_admin),
):
    auth_header = request.headers.get("authorization", "")
    token = auth_header[7:] if auth_header.lower().startswith("bearer ") else ""
    if token:
        auth_service.logout(token)
    return success(msg="已退出登录")


@router.get("/me", summary="当前登录用户")
def me(current_user: User = Depends(get_current_admin)):
    return success(UserOut.model_validate(current_user).model_dump(mode="json"))


@router.put("/me", summary="修改个人信息")
def update_me(
    payload: UserUpdateIn,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    data = payload.model_dump(exclude_unset=True)
    user = auth_service.update_user(db, current_user, data)
    return success(UserOut.model_validate(user).model_dump(mode="json"), msg="已保存")


@router.post("/avatar", summary="上传头像（管理员）")
async def upload_avatar(
    file: UploadFile = File(..., description="头像图片文件"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    """上传头像，自动缩放处理并更新用户头像字段。"""
    # 1. 格式校验
    ext = Path(file.filename or "").suffix.lower().lstrip(".")
    if ext not in AVATAR_ALLOWED_EXT:
        raise BizException(
            f"不支持的图片格式：{ext or '未知'}，允许：{', '.join(sorted(AVATAR_ALLOWED_EXT))}"
        )

    # 2. 读取文件并校验大小
    content = await file.read()
    if len(content) > AVATAR_MAX_BYTES:
        raise BizException(f"头像图片过大，不能超过 {AVATAR_MAX_BYTES // 1024 // 1024}MB")

    if not content:
        raise BizException("文件内容为空")

    # 3. 图片缩放处理
    processed = _process_avatar_image(content, ext)

    # 4. 保存文件（规范化扩展名 jpeg -> jpg；落盘规则与 upload 接口共用）
    now = datetime.now()
    save_ext = "jpg" if ext == "jpeg" else ext
    rel_dir = Path("uploads") / "avatars" / f"{now.year}" / f"{now.month:02d}"
    url, filename = image_service.store_image(processed, rel_dir, save_ext, prefix="avatar_")

    # 5. 保存旧头像 URL，更新后删除旧文件
    old_avatar_url = current_user.avatar

    # 6. 更新用户头像字段
    user = auth_service.update_user(db, current_user, {"avatar": url})

    # 7. 删除旧头像文件（如果存在且不是默认头像）。
    #    复用 image_service 的路径校验与空目录清理逻辑：
    #    resolve_image_path 会拦截非法 / 越界路径，避免误删 static 之外的文件
    if old_avatar_url and old_avatar_url != url:
        try:
            old_path = image_service.resolve_image_path(old_avatar_url)
            if old_path.is_file():
                old_path.unlink()
                avatar_root = settings.static_path / "uploads" / "avatars"
                image_service.cleanup_empty_dirs(old_path, avatar_root)
        except (BizException, OSError):
            # 路径非法或删除失败不影响主流程
            pass

    # 8. 清理站点缓存，确保前台头像同步更新
    if cache.available:
        cache.delete(make_key(K_PROFILE))
        cache.delete(make_key(K_SITE))

    return success(
        {
            "url": url,
            "filename": filename,
            "size": len(processed),
            "user": UserOut.model_validate(user).model_dump(mode="json"),
        },
        msg="头像已更新",
    )


@router.put("/password", summary="修改密码")
def change_password(
    payload: ChangePasswordIn,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    auth_service.change_password(db, current_user, payload.old_password, payload.new_password)
    return success(msg="密码已修改，请重新登录")
