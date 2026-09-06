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

/** 阅读时长（按每分钟 300 字估算，至少 1 分钟） */
export function readingMinutes(wordCount) {
  return Math.max(1, Math.ceil((wordCount || 0) / 300))
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
