"""slug 生成工具（兼容中文标题）"""
import re
import unicodedata

# 允许出现在 slug 中的字符：字母数字、连字符、下划线，以及 CJK
_CJK = r"\u4e00-\u9fff\u3400-\u4dbf"
_SAFE_RE = re.compile(rf"[^0-9a-zA-Z\-_{_CJK}]+")
_MULTI_DASH = re.compile(r"-+")


def slugify(text: str, max_length: int = 80) -> str:
    """生成 URL 友好的 slug

    - 中文字符保留（URL 编码后可正常访问）
    - 其余字符转为 ASCII 近似，无法转换的丢弃
    """
    if not text:
        return ""
    text = unicodedata.normalize("NFKD", text.strip())
    text = text.encode("ascii", "ignore").decode("ascii") if _is_latin(text) else text
    slug = _SAFE_RE.sub("-", text)
    slug = _MULTI_DASH.sub("-", slug).strip("-").lower()
    if len(slug) > max_length:
        slug = slug[:max_length].rstrip("-")
    return slug


def _is_latin(text: str) -> bool:
    """判断文本是否基本为拉丁字符（含音标符号）"""
    return all(ord(ch) < 0x2E00 for ch in text)


def unique_slug(base: str, exists_fn) -> str:
    """若 slug 已存在，追加 -2 / -3 ... 直到唯一"""
    base = base or "post"
    slug = base
    i = 2
    while exists_fn(slug):
        slug = f"{base}-{i}"
        i += 1
        if i > 500:  # 兜底，避免死循环
            break
    return slug
