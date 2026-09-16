"""SEO 服务：服务端注入 HTML head 元信息 + sitemap 内容生成

为什么必须由服务端注入：
微信、QQ、Twitter 等抓取链接预览时**不执行 JavaScript**，SPA 在客户端设置的
OG 标签对它们完全不可见（它们拿到的是空壳 HTML）。所以在返回 index.html 之前，
按请求路径把真实的 title / description / og:image 写进 HTML。

与前端的关系：
客户端 `useSeo.js` 会在挂载后设置同样的标签（且用 querySelector 更新而非新建），
因此两者不冲突——服务端负责"抓取时可见"，客户端负责"SPA 内部导航时更新"。
"""
import html
import re
from pathlib import Path
from typing import Any

from app.core.config import settings

# blog-web/index.html 中的注入标记对。标记缺失时后端降级为原样返回。
SEO_MARKER_RE = re.compile(r"<!--seo-start-->.*?<!--seo-end-->", re.DOTALL)

SITE_NAME = "BlueMoonの博客"


def xml_escape(value: str | None) -> str:
    """XML 文本转义（用于 sitemap）"""
    if not value:
        return ""
    return (
        str(value)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&apos;")
    )


def _esc(value: Any) -> str:
    """HTML 属性值转义（含引号），防止标题/摘要里的特殊字符破坏标签结构"""
    return html.escape(str(value or ""), quote=True)


def _abs_url(url: str | None) -> str:
    """相对路径 → 站点绝对地址（OG 的 url / image 必须是绝对地址）"""
    if not url:
        return ""
    if url.startswith(("http://", "https://")):
        return url
    base = settings.FRONTEND_URL.rstrip("/")
    return f"{base}{url if url.startswith('/') else '/' + url}"


def has_marker(html_text: str) -> bool:
    """index.html 是否包含 SEO 注入标记（未包含说明构建产物过旧）"""
    return SEO_MARKER_RE.search(html_text) is not None


def _meta_block(
    *,
    title: str,
    description: str,
    url: str,
    og_type: str = "website",
    image: str = "",
) -> str:
    """生成完整的 head 元信息块（含 title，整体替换标记对）"""
    lines = [
        f'<meta name="description" content="{_esc(description)}" />',
        f"<title>{_esc(title)}</title>",
        f'<meta property="og:type" content="{_esc(og_type)}" />',
        f'<meta property="og:site_name" content="{_esc(SITE_NAME)}" />',
        f'<meta property="og:title" content="{_esc(title)}" />',
        f'<meta property="og:description" content="{_esc(description)}" />',
        f'<meta property="og:url" content="{_esc(url)}" />',
    ]
    if image:
        lines.append(f'<meta property="og:image" content="{_esc(image)}" />')
    lines.append(
        '<meta name="twitter:card" content="'
        + ("summary_large_image" if image else "summary")
        + '" />'
    )
    lines.append(f'<link rel="canonical" href="{_esc(url)}" />')
    return "\n    ".join(lines)


def site_meta(path: str = "") -> str:
    """站点级默认元信息（非文章页使用）

    :param path: 当前请求路径（不含前导斜杠）。canonical 必须指向本页自身 ——
                 若统一指向首页，搜索引擎会把 /archives、/about 等内页判为首页的
                 重复内容，反而比不写 canonical 更糟。传空字符串表示首页。
    """
    title = " · ".join(p for p in (settings.BLOG_TITLE, settings.BLOG_SUBTITLE) if p)
    base = settings.FRONTEND_URL.rstrip("/")
    url = f"{base}/{path.lstrip('/')}" if path else f"{base}/"
    return _meta_block(
        title=title or SITE_NAME,
        description=settings.BLOG_DESCRIPTION or settings.BLOG_SUBTITLE or "",
        url=url,
    )


def post_meta(post: Any) -> str:
    """文章级元信息（含 og:image，指向封面）"""
    title = f"{post.title} · {settings.BLOG_TITLE}" if settings.BLOG_TITLE else post.title
    return _meta_block(
        title=title,
        description=post.summary or settings.BLOG_DESCRIPTION or "",
        url=f"{settings.FRONTEND_URL.rstrip('/')}/post/{post.slug}",
        og_type="article",
        image=_abs_url(getattr(post, "cover", None)),
    )


def inject(html_text: str, meta: str) -> str:
    """把元信息块注入标记对之间；标记缺失时原样返回"""
    if not has_marker(html_text):
        return html_text
    return SEO_MARKER_RE.sub(lambda _m: meta, html_text, count=1)


def sitemap_xml(rows: list[tuple[str, Any]]) -> str:
    """生成 sitemap.xml 内容

    :param rows: [(slug, updated_at), ...] 已按发布时间倒序
    """
    site = settings.FRONTEND_URL.rstrip("/")
    urls = [
        f"  <url><loc>{xml_escape(site + '/')}</loc></url>",
        f"  <url><loc>{xml_escape(site + '/archives')}</loc></url>",
        f"  <url><loc>{xml_escape(site + '/categories')}</loc></url>",
        f"  <url><loc>{xml_escape(site + '/images')}</loc></url>",
        f"  <url><loc>{xml_escape(site + '/about')}</loc></url>",
    ]
    for slug, updated in rows:
        lastmod = f"<lastmod>{updated.strftime('%Y-%m-%d')}</lastmod>" if updated else ""
        urls.append(
            f"  <url><loc>{xml_escape(f'{site}/post/{slug}')}</loc>{lastmod}</url>"
        )
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        + "\n".join(urls)
        + "\n</urlset>\n"
    )


def robots_txt() -> str:
    """生成 robots.txt 内容"""
    site = settings.FRONTEND_URL.rstrip("/")
    return (
        "User-agent: *\n"
        "Disallow: /admin\n"
        "Disallow: /api/\n"
        f"Sitemap: {site}/sitemap.xml\n"
    )


def read_index(index_file: Path) -> str | None:
    """读取 index.html 文本；失败返回 None（交由调用方降级为 FileResponse）"""
    try:
        return index_file.read_text(encoding="utf-8")
    except OSError:
        return None
