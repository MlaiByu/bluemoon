/**
 * 主题（浅色 / 深色）组合式函数
 * 集中管理 html.dark 的读写、切换颜色过渡、跨标签页同步与切换音效。
 *
 * 设计要点：
 * - 单一事实源：html.dark 类 + localStorage('bm-theme')。
 * - 多标签页同步：监听 storage 事件，其它标签页切换时本页即时跟随。
 * - 音效：用 Web Audio API 合成二次元「咔嗒 + 铃铛」短音，无外部资源、可选。
 */
import { onMounted, onUnmounted, ref } from 'vue'

const STORAGE_KEY = 'bm-theme'

/** 挂载前调用，避免深色模式首屏闪烁（main.js 使用） */
export function initTheme() {
  const saved = localStorage.getItem(STORAGE_KEY)
  const dark = saved === 'dark'
  if (dark) document.documentElement.classList.add('dark')
  return dark
}

/* ------------------------------------------------------------------ */
/* 音效：Web Audio 合成「咔嗒」+ 短促「铃铛」，二次元风格               */
/* ------------------------------------------------------------------ */
let audioCtx = null

function getAudioCtx() {
  if (typeof window === 'undefined') return null
  const AC = window.AudioContext || window.webkitAudioContext
  if (!AC) return null
  if (!audioCtx) audioCtx = new AC()
  return audioCtx
}

/** 播放切换音效：先「咔嗒」（低频短促），再高频「叮」的铃铛余韵 */
function playChime() {
  const ctx = getAudioCtx()
  if (!ctx || ctx.state === 'suspended') {
    // 首次交互需 resume（浏览器自动播放策略）
    try {
      ctx?.resume()
    } catch {
      /* ignore */
    }
  }
  const now = ctx.currentTime

  // 咔嗒：快速衰减的方波，模拟机械拉绳声
  const click = ctx.createOscillator()
  const clickGain = ctx.createGain()
  click.type = 'triangle'
  click.frequency.setValueAtTime(180, now)
  click.frequency.exponentialRampToValueAtTime(90, now + 0.08)
  clickGain.gain.setValueAtTime(0.12, now)
  clickGain.gain.exponentialRampToValueAtTime(0.0001, now + 0.09)
  click.connect(clickGain).connect(ctx.destination)
  click.start(now)
  click.stop(now + 0.1)

  // 铃铛：双正弦叠加，清脆悦耳
  const chime = ctx.createOscillator()
  const chime2 = ctx.createOscillator()
  const chimeGain = ctx.createGain()
  chime.type = 'sine'
  chime.frequency.setValueAtTime(1318.5, now + 0.02) // E6
  chime2.type = 'sine'
  chime2.frequency.setValueAtTime(1975.5, now + 0.02) // B6
  chimeGain.gain.setValueAtTime(0.0001, now + 0.02)
  chimeGain.gain.exponentialRampToValueAtTime(0.06, now + 0.04)
  chimeGain.gain.exponentialRampToValueAtTime(0.0001, now + 0.5)
  chime.connect(chimeGain).connect(ctx.destination)
  chime2.connect(chimeGain).connect(ctx.destination)
  chime.start(now + 0.02)
  chime2.start(now + 0.02)
  chime.stop(now + 0.52)
  chime2.stop(now + 0.52)
}

/* ------------------------------------------------------------------ */
/* 组合式函数                                                          */
/* ------------------------------------------------------------------ */
export function useTheme() {
  const isDark = ref(document.documentElement.classList.contains('dark'))

  /** 静默应用主题（不播音效、不触发过渡），供跨标签同步与初始化使用 */
  function apply(dark, opts = {}) {
    isDark.value = dark
    document.documentElement.classList.toggle('dark', dark)
    localStorage.setItem(STORAGE_KEY, dark ? 'dark' : 'light')
    if (opts.animate) {
      document.documentElement.classList.add('theme-anim')
      window.setTimeout(() => {
        document.documentElement.classList.remove('theme-anim')
      }, 320)
    }
  }

  /** 用户主动切换：开启颜色过渡 + 播音效（全屏光波过场已按需求移除） */
  function toggle() {
    document.documentElement.classList.add('theme-anim')
    apply(!isDark.value)
    playChime()
    window.setTimeout(() => {
      document.documentElement.classList.remove('theme-anim')
    }, 320)
  }

  /* 跨标签页同步：其它标签页修改 bm-theme 时，本页跟随 */
  function onStorage(e) {
    if (e.key !== STORAGE_KEY) return
    const dark = e.newValue === 'dark'
    if (dark === isDark.value) return
    apply(dark, { animate: true })
  }

  onMounted(() => window.addEventListener('storage', onStorage))
  onUnmounted(() => window.removeEventListener('storage', onStorage))

  return { isDark, apply, toggle }
}
