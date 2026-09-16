import { onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { recordView } from '@/api'

/**
 * 有效阅读计时器
 *
 * 规则：用户进入文章后开始计时，页面切到后台 / 不可见时暂停，切回前台继续累计；
 *       累计「可见且停留」满 READ_THRESHOLD_MS 才上报一次阅读量。
 *
 * 防重复计数（三层）：
 * 1. 单页内：counted 标记 + 上报前先置位，保证一次进入最多上报一次；
 * 2. 跨刷新：localStorage 记录已上报的文章，LS_TTL_MS 内不再上报；
 * 3. 服务端：同一 IP 对同一文章在窗口内只计一次（真正的兜底，清缓存 / 换标签页也无效）。
 *
 * 计时用「时间戳差值」而非定时器累加：后台标签页的 setInterval 会被浏览器节流，
 * 单纯累加 tick 次数会严重低估停留时长。
 */

/** 有效阅读门槛：进入文章并持续阅读满 5 秒计一次阅读（与后端 VIEW_READ_THRESHOLD_SECONDS 对齐） */
export const READ_THRESHOLD_MS = 5 * 1000

const LS_KEY = 'bm:viewed-posts'
const LS_TTL_MS = 5 * 60 * 1000 // 与后端 VIEW_DEDUP_TTL_SECONDS 对齐

/* ---------------- localStorage 去重记录 ---------------- */

function getViewedMap() {
  try {
    const raw = localStorage.getItem(LS_KEY)
    return raw ? JSON.parse(raw) : {}
  } catch {
    return {}
  }
}

function markViewed(postId) {
  try {
    const map = getViewedMap()
    map[postId] = Date.now()
    const now = Date.now()
    for (const k of Object.keys(map)) {
      if (now - map[k] > LS_TTL_MS) delete map[k]
    }
    localStorage.setItem(LS_KEY, JSON.stringify(map))
  } catch {
    /* localStorage 不可用时忽略，还有后端兜底 */
  }
}

function hasViewed(postId) {
  const ts = getViewedMap()[postId]
  return !!ts && Date.now() - ts < LS_TTL_MS
}

/* ---------------- 计时器 ---------------- */

export function useReadingTimer(postIdRef) {
  const elapsed = ref(0) // 已确认累计的有效阅读时长（毫秒）
  const counted = ref(false) // 本次进入是否已上报
  const views = ref(null) // 后端回传的最新阅读数，用于校准页面展示

  let timer = null
  let segmentStart = 0 // 当前「可见段」起点时间戳，0 = 未在计时
  let currentId = null
  let listening = false

  const now = () => Date.now()

  /** 已累计 + 当前可见段进行中的时长 */
  function totalElapsed() {
    return elapsed.value + (segmentStart ? now() - segmentStart : 0)
  }

  /** 把进行中的可见段结算进 elapsed，并停掉定时器 */
  function freeze() {
    if (segmentStart) {
      elapsed.value += now() - segmentStart
      segmentStart = 0
    }
    if (timer) {
      clearInterval(timer)
      timer = null
    }
  }

  /** 开启一段新的可见计时 */
  function resume() {
    if (counted.value || !currentId || segmentStart) return
    segmentStart = now()
    if (!timer) timer = setInterval(tick, 500)
  }

  function tick() {
    if (counted.value) {
      freeze()
      return
    }
    // 兜底：定时器被节流 / 事件丢失时，这里也能感知到不可见状态
    if (document.visibilityState !== 'visible') {
      freeze()
      return
    }
    if (totalElapsed() >= READ_THRESHOLD_MS) {
      counted.value = true // 先置位，防止并发重复上报
      freeze()
      removeVisibility()
      report()
    }
  }

  function onVisibility() {
    if (document.visibilityState === 'visible') resume()
    else freeze()
  }

  function addVisibility() {
    if (listening) return
    document.addEventListener('visibilitychange', onVisibility)
    listening = true
  }

  function removeVisibility() {
    if (!listening) return
    document.removeEventListener('visibilitychange', onVisibility)
    listening = false
  }

  /** 上报一次有效阅读（失败不重试，避免刷量） */
  async function report() {
    const id = currentId
    if (!id) return
    try {
      const res = await recordView(id)
      if (res && typeof res.views === 'number') views.value = res.views
    } catch {
      /* 忽略：网络异常时宁可少计，也不重试刷量 */
    } finally {
      markViewed(id)
    }
  }

  /** 切换文章 / 首次拿到文章 ID 时重置状态 */
  function reset(id) {
    freeze()
    removeVisibility()
    elapsed.value = 0
    counted.value = false
    views.value = null
    currentId = id ?? null
    if (!currentId) return

    if (hasViewed(currentId)) {
      counted.value = true // 去重窗口内已计过，本次不再上报
      return
    }
    addVisibility()
    if (document.visibilityState === 'visible') resume()
  }

  // 文章是异步加载的，挂载时可能还没有 ID，靠 watch 补触发
  watch(postIdRef, (id) => {
    if (id !== currentId) reset(id)
  })

  onMounted(() => reset(postIdRef.value))
  onBeforeUnmount(() => {
    freeze()
    removeVisibility()
  })

  return { elapsed, counted, views }
}
