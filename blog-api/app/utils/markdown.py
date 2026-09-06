"""Markdown 文本处理：摘要提取 / 字数统计"""
import re

# 代码块
_RE_CODE_BLOCK = re.compile(r"```.*?```", re.S)
# 行内代码
_RE_INLINE_CODE = re.compile(r"`[^`]*`")
# 图片 / 链接
_RE_IMAGE = re.compile(r"!\[[^\]]*\]\([^)]*\)")
_RE_LINK = re.compile(r"\[([^\]]*)\]\([^)]*\)")
# 标题、引用、分割线、列表符号、粗体斜体
_RE_HEADING = re.compile(r"^\s{0,3}#{1,6}\s+", re.M)
_RE_QUOTE = re.compile(r"^\s{0,3}>\s?", re.M)
_RE_HR = re.compile(r"^\s{0,3}([-*_])\s*(\1\s*){2,}$", re.M)
_RE_LIST = re.compile(r"^\s{0,3}[-*+]\s+", re.M)
_RE_EMPHASIS = re.compile(r"[*_~]{1,3}")
_RE_HTML = re.compile(r"<[^>]+>")
_RE_WS = re.compile(r"\s+")

_CJK_RE = re.compile(r"[\u4e00-\u9fff\u3400-\u4dbf]")
_WORD_RE = re.compile(r"[A-Za-z0-9]+")


def strip_markdown(md: str) -> str:
    """把 Markdown 转成纯文本（用于自动生成摘要）"""
    if not md:
        return ""
    text = _RE_CODE_BLOCK.sub(" ", md)
    text = _RE_INLINE_CODE.sub(" ", text)
    text = _RE_IMAGE.sub(" ", text)
    text = _RE_LINK.sub(r"\1", text)
    text = _RE_HEADING.sub("", text)
    text = _RE_QUOTE.sub("", text)
    text = _RE_HR.sub(" ", text)
    text = _RE_LIST.sub("", text)
    text = _RE_EMPHASIS.sub("", text)
    text = _RE_HTML.sub(" ", text)
    return _RE_WS.sub(" ", text).strip()


def make_summary(md: str, length: int = 120) -> str:
    """自动生成摘要"""
    text = strip_markdown(md)
    if len(text) <= length:
        return text
    return text[:length].rstrip() + "…"


def count_words(md: str) -> int:
    """字数统计：中文按字符计，英文按单词计"""
    if not md:
        return 0
    text = strip_markdown(md)
    cjk = len(_CJK_RE.findall(text))
    words = len(_WORD_RE.findall(text))
    return cjk + words
