import { onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { recordView } from '@/api'

/**
 * 有效阅读计时器：
 * - 用户进入文章页后开始计时
 * - 页面切到后台或不可见时暂停，切回前台继续累计
 * - 累计阅读满 READ_THRESHOLD_MS 后上报一次阅读量
 * - localStorage 记录已上报的文章，5 分钟内不重复上报（前端层面防刷）
 * - 后端也有 IP + 文章 ID 的 5 分钟防刷锁，双重保障
 */

const READ_THRESHOLD_MS = 10 * 1000 // 10 秒
const LS_KEY = 'bm:viewed-posts'
const LS_TTL_MS = 5 * 60 * 1000 // 5 分钟

/** 读取 localStorage 中已阅读的文章记录 */
function getViewedMap() {
  try {
    const raw = localStorage.getItem(LS_KEY)
    return raw ? JSON.parse(raw) : {}
  } catch {
    return {}
  }
}

/** 写入 localStorage 中已阅读的文章记录 */
function setViewed(postId) {
  try {
    const map = getViewedMap()
    map[postId] = Date.now()
    // 清理过期条目
    const now = Date.now()
    for (const k of Object.keys(map)) {
      if (now - map[k] > LS_TTL_MS) {
        delete map[k]
      }
    }
    localStorage.setItem(LS_KEY, JSON.stringify(map))
  } catch {
    /* ignore */
  }
}

/** 检查文章是否已在有效期内上报过 */
function hasViewed(postId) {
  const map = getViewedMap()
  const ts = map[postId]
  if (!ts) return false
  return Date.now() - ts < LS_TTL_MS
}

export function useReadingTimer(postIdRef) {
  const elapsed = ref(0) // 已累计阅读时长（毫秒）
  const counted = ref(false) // 是否已上报过
  const isVisible = ref(true) // 页面是否可见

  let timer = null
  let lastTick = 0

  /** 开始计时 */
  function start() {
    if (timer) return
    lastTick = Date.now()
    timer = setInterval(tick, 1000)
  }

  /** 暂停计时 */
  function pause() {
    if (timer) {
      clearInterval(timer)
      timer = null
    }
  }

  /** 每次 tick 累加经过的时间 */
  function tick() {
    if (!isVisible.value || counted.value) return
    const now = Date.now()
    const delta = now - lastTick
    lastTick = now
    elapsed.value += delta

    if (elapsed.value >= READ_THRESHOLD_MS && !counted.value) {
      counted.value = true
      pause()
      doReport()
    }
  }

  /** 上报阅读量 */
  async function doReport() {
    const postId = postIdRef.value
    if (!postId) return
    try {
      await recordView(postId)
      setViewed(postId)
    } catch {
      // 上报失败也不重试，避免刷量
      counted.value = true // 标记为已上报，不再重复请求
    }
  }

  /** 页面可见性变化 */
  function onVisibilityChange() {
    const visible = document.visibilityState === 'visible'
    isVisible.value = visible
    if (visible) {
      lastTick = Date.now()
    }
  }

  /** 初始化 */
  function init() {
    const postId = postIdRef.value
    if (!postId) return

    // 如果已经在本地记录中上报过，直接标记为已计数
    if (hasViewed(postId)) {
      counted.value = true
      return
    }

    // 监听页面可见性
    document.addEventListener('visibilitychange', onVisibilityChange)
    isVisible.value = document.visibilityState === 'visible'

    // 开始计时
    start()
  }

  /** 清理 */
  function cleanup() {
    pause()
    document.removeEventListener('visibilitychange', onVisibilityChange)
  }

  // 监听 postId 变化（切换文章时重置）
  watch(postIdRef, (newId, oldId) => {
    if (newId !== oldId) {
      cleanup()
      elapsed.value = 0
      counted.value = false
      if (newId) {
        if (hasViewed(newId)) {
          counted.value = true
        } else {
          start()
        }
      }
    }
  })

  onMounted(init)
  onBeforeUnmount(cleanup)

  return {
    elapsed,
    counted,
    isVisible,
  }
}
