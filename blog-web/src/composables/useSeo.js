/**
 * 页面级 SEO 元信息统一出口（title / description / Open Graph / Twitter Card / canonical）
 *
 * 为什么需要它：
 * - 此前 document.title 在 router/index.js 与 PostDetail.vue 两处分别赋值，页面级
 *   meta（OG / canonical）则完全缺失。集中到此处，避免后续再出现"两处各写一半"。
 * - SPA 切换页面时，上一个页面写入的 OG 标签不会被浏览器清除。若从文章页跳回首页，
 *   分享出去仍会显示上一篇文章的标题。因此路由守卫在每次导航开始时先 resetSeo()
 *   恢复站点默认，页面再按需覆盖。
 *
 * 注意：canonical 只做动态设置，index.html 里不放静态 canonical —— SPA 所有路径
 * 返回同一份 HTML，静态 canonical 会让 /post/xxx 等内页被判为首页的重复内容。
 */

const SITE_NAME = 'BlueMoonの博客'
const DEFAULT_DESCRIPTION = '一个安静写字的地方'
const TITLE_SUFFIX = 'Bluemoon'
const FALLBACK_TITLE = 'Bluemoon · 个人博客'

/** 相对路径 → 绝对 URL（OG 的 url/image 必须是绝对地址） */
function toAbsolute(url) {
  if (!url) return ''
  if (/^https?:\/\//i.test(url)) return url
  return location.origin + (url.startsWith('/') ? url : `/${url}`)
}

function upsertMeta(attr, key, content) {
  if (!content) return
  let el = document.head.querySelector(`meta[${attr}="${key}"]`)
  if (!el) {
    el = document.createElement('meta')
    el.setAttribute(attr, key)
    document.head.appendChild(el)
  }
  el.setAttribute('content', content)
}

function upsertCanonical(href) {
  let el = document.head.querySelector('link[rel="canonical"]')
  if (!el) {
    el = document.createElement('link')
    el.setAttribute('rel', 'canonical')
    document.head.appendChild(el)
  }
  el.setAttribute('href', href)
}

/**
 * 设置标签页标题（统一出口，页面不要再直接写 document.title）
 * @param {string} [title] 页面标题；缺省时回退到站点默认标题
 */
export function setTitle(title) {
  document.title = title ? `${title} · ${TITLE_SUFFIX}` : FALLBACK_TITLE
}

/**
 * 恢复站点级默认 SEO。
 * 应在每次路由导航开始时（router.beforeEach）调用，防止上一页的 OG 残留。
 * @param {{title?: string, description?: string, subtitle?: string}} [site] 可选站点信息
 */
export function resetSeo(site) {
  const notice = site || {}
  const title = notice.title || SITE_NAME
  const description = notice.description || notice.subtitle || DEFAULT_DESCRIPTION
  // canonical 必须指向本页自身：统一指向首页会让 /archives、/about 等内页
  // 被判为首页的重复内容。去掉 query 与 hash。
  const url = location.origin + location.pathname

  upsertMeta('name', 'description', description)
  upsertMeta('property', 'og:type', 'website')
  upsertMeta('property', 'og:site_name', SITE_NAME)
  upsertMeta('property', 'og:title', title)
  upsertMeta('property', 'og:description', description)
  upsertMeta('property', 'og:url', url)
  upsertMeta('name', 'twitter:card', 'summary_large_image')
  upsertCanonical(url)
}

/**
 * 文章详情页 SEO。
 * @param {object} post 文章对象（需含 title / slug / summary / cover）
 * @param {{site?: object, resolveImage?: (url: string) => string}} [options]
 */
export function applyPostSeo(post, options) {
  if (!post) return
  const opts = options || {}
  const site = opts.site || {}

  const title = post.title || ''
  const description = post.summary || site.description || DEFAULT_DESCRIPTION
  const url = `${location.origin}/post/${post.slug}`
  const cover = opts.resolveImage ? opts.resolveImage(post.cover) : post.cover
  const image = toAbsolute(cover)

  setTitle(title)
  upsertMeta('name', 'description', description)
  upsertMeta('property', 'og:type', 'article')
  upsertMeta('property', 'og:title', title)
  upsertMeta('property', 'og:description', description)
  upsertMeta('property', 'og:url', url)
  upsertMeta('name', 'twitter:card', image ? 'summary_large_image' : 'summary')
  if (image) upsertMeta('property', 'og:image', image)
  upsertCanonical(url)
}
