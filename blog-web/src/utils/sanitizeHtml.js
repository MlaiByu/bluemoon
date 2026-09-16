/**
 * 正文原始 HTML 清洗（防存储型 XSS）
 *
 * 背景：MarkdownView 为了兼容既有文章里的富文本（视频外链、折叠块、表格等）
 * 必须开启 markdown-it 的 `html: true`，而渲染结果又是 `v-html` 注入，
 * 于是文章正文里的原始 HTML 会被原样执行 —— `<img src=x onerror=…>`、
 * `<svg onload=…>`、`<iframe srcdoc=…>` 都能读到 localStorage 里的登录 token。
 *
 * 策略：**只针对原始 HTML token 做最小必要清洗**，不动 Markdown 语法本身，
 * 也不做整篇 HTML 重排（避免破坏既有排版）：
 *   1. 删除 <script>/<style>/<object>/<embed>/<link>/<meta>/<base>/<form> 等可执行/可加载标签
 *   2. 删除全部内联事件处理器（onclick / onerror / onload …）
 *   3. 删除 iframe 的 srcdoc（允许正常 iframe 外链嵌入，如视频）
 *   4. 把 javascript: / vbscript: / data:text/html 协议改写为 #
 *
 * 注意：本函数只处理 markdown-it 的 html_block / html_inline token，
 * 代码块（fenced code）内容不经过这里，不会误伤示例代码。
 */

/** 成对出现的危险标签（含内容一起删） */
const PAIRED_DANGEROUS = /<\s*(script|style|object|embed|applet|form|noscript)\b[^>]*>[\s\S]*?<\s*\/\s*\1\s*>/gi
/** 自闭合 / 未闭合的危险标签 */
const SOLO_DANGEROUS = /<\s*\/?\s*(script|style|object|embed|applet|link|meta|base|frame|frameset|form|noscript)\b[^>]*>/gi
/** 内联事件处理器：onclick="…" / onclick='…' / onclick=bare */
const INLINE_HANDLER_QUOTED = /\son[a-z]+\s*=\s*(?:"[^"]*"|'[^']*')/gi
const INLINE_HANDLER_BARE = /\son[a-z]+\s*=\s*[^\s>]+/gi
/** iframe 的 srcdoc（可执行任意 HTML） */
const SRCDOC = /\ssrcdoc\s*=\s*(?:"[^"]*"|'[^']*'|[^\s>]+)/gi
/** 危险协议（带引号 / 不带引号两种写法） */
const BAD_PROTO_QUOTED = /\s(href|src|xlink:href|action|formaction|poster)\s*=\s*(["'])\s*(?:javascript|vbscript|data\s*:\s*text\/html)[^"']*\2/gi
const BAD_PROTO_BARE = /\s(href|src|xlink:href|action|formaction|poster)\s*=\s*(?:javascript|vbscript)[^\s>]*/gi

/**
 * 清洗一段原始 HTML
 * @param {string} html
 * @returns {string}
 */
export function sanitizeRawHtml(html) {
  if (!html) return html
  let out = String(html)
  out = out.replace(PAIRED_DANGEROUS, '')
  out = out.replace(SOLO_DANGEROUS, '')
  out = out.replace(INLINE_HANDLER_QUOTED, '')
  out = out.replace(INLINE_HANDLER_BARE, '')
  out = out.replace(SRCDOC, '')
  out = out.replace(BAD_PROTO_QUOTED, ' $1="#"')
  out = out.replace(BAD_PROTO_BARE, ' $1="#"')
  return out
}
