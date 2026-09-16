"""认证接口"""
from io import BytesIO
from pathlib import Path

from fastapi import APIRouter, Depends, File, Request, UploadFile
from PIL import Image
from sqlalchemy.orm import Session

from app.api.deps import client_ip, get_current_admin, get_db
from app.core.exceptions import BizException
from app.core.response import success
from app.models.user import User
from app.schemas.user import ChangePasswordIn, LoginIn, UserOut, UserUpdateIn
from app.services import auth_service, avatar_service, image_service
from app.services.cache import K_PROFILE, K_SITE, cache, make_key

router = APIRouter(prefix="/auth", tags=["认证"])

# 头像最大边长（像素）
AVATAR_MAX_SIZE = 512
# 头像允许的格式（不含 svg：与站点同源托管会变成存储型 XSS 载体）
AVATAR_ALLOWED_EXT = {"jpg", "jpeg", "png", "gif", "webp"}
# 头像最大文件大小（字节）
AVATAR_MAX_BYTES = 5 * 1024 * 1024  # 5MB


def _process_avatar_image(content: bytes, ext: str) -> bytes:
    """缩放头像图片，保持宽高比，最大边不超过 AVATAR_MAX_SIZE。

    处理失败直接抛错，**不**回退原图落盘 —— 回退等于让一张畸形图片
    绕过 512px 限制（上传 8000×8000 的图就能塞进头像目录）。
    """
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


@router.post("/login", summary="管理员登录")
def login(
    payload: LoginIn,
    db: Session = Depends(get_db),
    ip: str = Depends(client_ip),
):
    result = auth_service.login(db, payload.username, payload.password, ip=ip)
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
def upload_avatar(
    file: UploadFile = File(..., description="头像图片文件"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    """上传头像，自动缩放处理并更新用户头像字段。

    同步端点（Pillow 缩放与磁盘写入会阻塞事件循环，交给 FastAPI 的线程池执行）。
    """
    # 1. 格式校验
    ext = Path(file.filename or "").suffix.lower().lstrip(".")
    if ext not in AVATAR_ALLOWED_EXT:
        raise BizException(
            f"不支持的图片格式：{ext or '未知'}，允许：{', '.join(sorted(AVATAR_ALLOWED_EXT))}"
        )

    # 2. 限长读取（超限不整体读进内存）
    content = file.file.read(AVATAR_MAX_BYTES + 1)
    if len(content) > AVATAR_MAX_BYTES:
        raise BizException(f"头像图片过大，不能超过 {AVATAR_MAX_BYTES // 1024 // 1024}MB")
    if not content:
        raise BizException("文件内容为空")

    # 3. 校验真实格式 + 像素上限（防改名绕过与解压炸弹）
    image_service.validate_image_bytes(content, ext)

    # 4. 图片缩放处理（失败即拒绝，不回退原图）
    try:
        processed = _process_avatar_image(content, ext)
    except Exception as exc:  # noqa: BLE001
        raise BizException(f"头像处理失败：{exc}")

    # 5. 保存文件（规范化扩展名 jpeg -> jpg；落盘规则与 upload 接口共用）
    #    头像是站点级资产，统一放在 static/avatar/，不随日期目录散落
    save_ext = "jpg" if ext == "jpeg" else ext
    rel_dir = image_service.avatar_dir()
    # 头像在上游已用 PIL 裁切压缩，无需再生成衍生档（derivatives=False）
    url, filename = image_service.store_image(
        processed, rel_dir, save_ext, prefix="avatar_", derivatives=False
    )

    # 6. 归档：新头像写入历史并设为当前使用，旧头像保留为历史（不删除文件）
    avatar_item = avatar_service.add_avatar(db, current_user, url, filename, len(processed))
    user = current_user

    # 7. 清理站点缓存，确保前台头像同步更新
    if cache.available:
        cache.delete(make_key(K_PROFILE))
        cache.delete(make_key(K_SITE))

    return success(
        {
            "url": url,
            "filename": filename,
            "size": len(processed),
            "avatar": avatar_item,
            "user": UserOut.model_validate(user).model_dump(mode="json"),
        },
        msg="头像已更新，旧头像已存入历史",
    )


@router.get("/avatars", summary="历史头像列表（管理员）")
def list_avatars(current_user: User = Depends(get_current_admin), db: Session = Depends(get_db)):
    """查询当前用户的历史头像，按上传时间倒序；is_current 标记当前使用的一张。"""
    return success(avatar_service.list_avatars(db, current_user))


@router.post("/avatar/restore", summary="从历史头像恢复（管理员）")
def restore_avatar(
    body: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    """把某张历史头像恢复为当前头像（原头像仍保留在历史中）。"""
    avatar_id = body.get("id")
    if not avatar_id:
        raise BizException("请选择要恢复的头像")
    item = avatar_service.restore_avatar(db, current_user, int(avatar_id))

    if cache.available:
        cache.delete(make_key(K_PROFILE))
        cache.delete(make_key(K_SITE))

    return success(
        {"avatar": item, "user": UserOut.model_validate(current_user).model_dump(mode="json")},
        msg="已恢复该头像",
    )


@router.delete("/avatar/{avatar_id}", summary="删除历史头像（管理员）")
def delete_avatar(
    avatar_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    """删除一条历史头像（当前使用的那张不可删除）。"""
    avatar_service.delete_avatar(db, current_user, avatar_id)
    return success(msg="已删除该历史头像")


@router.put("/password", summary="修改密码")
def change_password(
    payload: ChangePasswordIn,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    auth_service.change_password(db, current_user, payload.old_password, payload.new_password)
    return success(msg="密码已修改，请重新登录")
