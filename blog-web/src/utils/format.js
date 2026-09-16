/**
 * 通用格式化工具
 * 抽自 PostCard / PostDetail / Home / PostsAdmin 中重复实现的逻辑。
 */
import dayjs from 'dayjs'

/** 日期格式化：默认 YYYY-MM-DD；空值返回 fallback（默认空字符串） */
export function formatDate(d, fmt = 'YYYY-MM-DD', fallback = '') {
  return d ? dayjs(d).format(fmt) : fallback
}

/** 后台 / 详情页常用完整时间：YYYY-MM-DD HH:mm，空值默认显示 - */
export function formatDateTime(d, fallback = '-') {
  return formatDate(d, 'YYYY-MM-DD HH:mm', fallback)
}

/** 归档列表用的「月-日」 */
export function formatDay(d) {
  return d ? dayjs(d).format('MM-DD') : ''
}

/** 字节数转可读体积（图片管理页使用） */
export function formatSize(bytes) {
  if (bytes === 0) return '0 B'
  if (!bytes) return ''
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / 1024 / 1024).toFixed(2)} MB`
}

/**
 * 统一处理图片 URL
 * - 外链（http/https 开头）直接返回
 * - /static/ 开头的相对路径原样返回（开发环境走 vite 代理，生产环境走同域静态资源）
 * - 空值返回空字符串
 */
export function resolveImageUrl(url) {
  if (!url) return ''
  if (/^https?:\/\//i.test(url)) return url
  if (url.startsWith('/static/')) return url
  if (url.startsWith('data:')) return url
  // 其他情况补全路径
  return url.startsWith('/') ? url : `/static/${url}`
}

/**
 * 取图片的 WebP 衍生档地址（列表卡片用 400，首屏与正文用 1024）。
 *
 * 上传时后端会按主图生成 `xxx@400.webp` / `xxx@1024.webp`（见
 * image_service.DERIVATIVE_SPECS），文件名由主图派生，所以这里按规则直接拼出。
 *
 * 以下情况原样返回（不拼衍生档），由调用方的 onerror 兜底：
 * - 外链图片（对方服务器不受我们控制）
 * - SVG / GIF（后端不生成衍生档）
 * - 非站内路径
 */
export function resolveImageVariant(url, size = 1024) {
  const full = resolveImageUrl(url)
  if (!full.startsWith('/static/')) return full
  // 头像走独立处理（上游已用 PIL 裁切压缩），不生成衍生档
  if (full.startsWith('/static/avatar/')) return full
  // 已经是衍生档时不要二次拼接（防 a@400@400.webp）
  if (/@(?:1024|400)\.webp$/i.test(full)) return full
  // SVG 是矢量、GIF 转码会丢动画，后端都不生成衍生档
  if (!/\.(jpe?g|png|webp|bmp)$/i.test(full)) return full
  return full.replace(/\.[a-z0-9]+$/i, `@${size}.webp`)
}

/**
 * 衍生档加载失败时回退原图的通用处理器。
 *
 * 用 data-original 承载原图地址、data-fb 做一次性标记，
 * 避免回退目标也失败时陷入无限 onerror 循环。
 * 用法：<img :src="thumb" :data-original="original" @error="onImageError">
 */
export function onImageError(e) {
  const img = e.target
  const original = img.dataset.original
  if (!original || img.dataset.fb) return
  img.dataset.fb = '1'
  img.src = original
}
