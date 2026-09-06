<template>
  <!--
    悬挂式纸灯笼 · 拉绳切换日夜
    右上角垂下一根挂绳系着纸灯笼，整串以顶端为轴心做钟摆摆动：
    平时随微风轻轻摇摆；每隔一段不固定的时间刮过一阵风——
    摆幅短暂加大、灯笼随之轻晃，随后逐渐恢复平静。
    向下拉动灯笼下方的流苏拉绳（超过灯身 1/3 行程）即可切换日/夜模式，
    点击 / 空格 / 回车等效。状态与 useTheme 全局共享。
  -->
  <div
    ref="rootEl"
    class="lantern"
    :class="[`is-${machine.state.name}`, { lit: isDark, 'show-label': labelShown }]"
    :style="rootStyle"
  >
    <!-- 顶端挂钩（不随摆动旋转） -->
    <span class="ceiling-hook" aria-hidden="true"></span>

    <!-- 摆动体：挂绳 + 灯笼 + 拉绳，绕顶端旋转 -->
    <div class="swing">
      <!-- 挂绳 -->
      <span class="rope" aria-hidden="true"></span>

      <!-- 木纹横档 + 四角翘起古风小角 + 提梁 -->
      <div class="top-rail" aria-hidden="true">
        <span class="corner c1"></span>
        <span class="corner c2"></span>
        <span class="corner c3"></span>
        <span class="corner c4"></span>
        <span class="grain"></span>
        <span class="handle"></span>
      </div>

      <!-- 灯身：樱粉圆润灯罩 + 卡通波点 + 蕾丝花边 + 内部透光 -->
      <div class="body" aria-hidden="true">
        <span class="paper"></span>
        <span class="pattern"></span>
        <span class="frill"></span>
        <span class="inner-glow"></span>
        <!-- 颜文字太阳 / 月亮（SVG 手绘）：切换时旋转交叉过渡 -->
        <span class="body-icon">
          <transition name="icon-swap" mode="out-in">
            <svg
              v-if="!isDark"
              key="sun"
              class="icon-svg"
              viewBox="0 0 48 48"
              role="img"
              aria-label="太阳"
            >
              <g class="sun-rays" stroke="#ff9f43" stroke-width="3" stroke-linecap="round">
                <line x1="24" y1="3" x2="24" y2="9" />
                <line x1="24" y1="39" x2="24" y2="45" />
                <line x1="3" y1="24" x2="9" y2="24" />
                <line x1="39" y1="24" x2="45" y2="24" />
                <line x1="9.2" y1="9.2" x2="13.4" y2="13.4" />
                <line x1="34.6" y1="34.6" x2="38.8" y2="38.8" />
                <line x1="9.2" y1="38.8" x2="13.4" y2="34.6" />
                <line x1="34.6" y1="13.4" x2="38.8" y2="9.2" />
              </g>
              <circle cx="24" cy="24" r="12.5" fill="#ffd76e" />
              <path d="M18.6 22.6 q2.2 2.6 4.4 0" fill="none" stroke="#8a5a1f" stroke-width="1.7" stroke-linecap="round" />
              <path d="M25 22.6 q2.2 2.6 4.4 0" fill="none" stroke="#8a5a1f" stroke-width="1.7" stroke-linecap="round" />
              <path d="M21.6 26.6 q2.4 2.2 4.8 0" fill="none" stroke="#8a5a1f" stroke-width="1.7" stroke-linecap="round" />
              <circle cx="17.6" cy="25.4" r="1.9" fill="#ff9eb0" opacity="0.6" />
              <circle cx="30.4" cy="25.4" r="1.9" fill="#ff9eb0" opacity="0.6" />
            </svg>
            <svg
              v-else
              key="moon"
              class="icon-svg"
              viewBox="0 0 48 48"
              role="img"
              aria-label="月亮"
            >
              <defs>
                <clipPath id="bm-moon-clip">
                  <circle cx="24" cy="24" r="13" />
                </clipPath>
              </defs>
              <circle cx="24" cy="24" r="13" fill="#f4ecd4" />
              <g clip-path="url(#bm-moon-clip)">
                <circle cx="31.5" cy="21" r="11.5" fill="#e6d8ae" opacity="0.5" />
              </g>
              <path d="M18.4 23.4 q2.1 2.5 4.2 0" fill="none" stroke="#7c6a3f" stroke-width="1.7" stroke-linecap="round" />
              <path d="M25.4 23.4 q2.1 2.5 4.2 0" fill="none" stroke="#7c6a3f" stroke-width="1.7" stroke-linecap="round" />
              <path d="M21.4 27.4 q2.6 2.2 5.2 0" fill="none" stroke="#7c6a3f" stroke-width="1.7" stroke-linecap="round" />
              <circle cx="17.2" cy="26.4" r="1.8" fill="#ffb7c5" opacity="0.55" />
              <circle cx="30.2" cy="26.4" r="1.8" fill="#ffb7c5" opacity="0.55" />
              <path class="moon-star s1" d="M39 9 l1.1 2.6 2.6 1.1 -2.6 1.1 -1.1 2.6 -1.1 -2.6 -2.6 -1.1 2.6 -1.1 Z" fill="#f7dc6f" />
              <path class="moon-star s2" d="M41.5 30 l0.8 1.9 1.9 0.8 -1.9 0.8 -0.8 1.9 -0.8 -1.9 -1.9 -0.8 1.9 -0.8 Z" fill="#ffe9a8" />
              <path class="moon-star s3" d="M6.5 31 l0.7 1.7 1.7 0.7 -1.7 0.7 -0.7 1.7 -0.7 -1.7 -1.7 -0.7 1.7 -0.7 Z" fill="#ffe9a8" />
            </svg>
          </transition>
        </span>
      </div>

      <!-- 底箍 -->
      <div class="bottom-rim" aria-hidden="true"></div>

      <!-- 流苏拉绳（交互把手）：金色混樱花粉，末端琉璃珠 -->
      <button
        ref="btnEl"
        class="cord"
        type="button"
        role="switch"
        :aria-checked="isDark"
        :aria-label="isDark ? '熄灯' : '点灯'"
        :title="isDark ? '拉一下 · 熄灯' : '拉一下 · 点灯'"
        @click="onClick"
        @keydown.space.prevent="onClick"
        @keydown.enter.prevent="onClick"
        @pointerdown="onPointerDown"
      >
        <span class="cord-threads" aria-hidden="true">
          <span class="thread" v-for="i in 9" :key="i"></span>
        </span>
        <span class="cord-bead" aria-hidden="true"></span>
      </button>
    </div>

    <!-- 状态文案 + 颜文字：位于摆动子树之外，避免文字常驻旋转合成层导致发糊 -->
    <div class="lantern-label" aria-hidden="true">
      <span class="txt">{{ isDark ? '灯明' : '灯灭' }}</span>
      <span class="face">{{ isDark ? '(｡･ω･｡)' : '(´-ω-｀)' }}</span>
    </div>

    <!-- 灯亮时的柔和光晕（衬在灯身背后） -->
    <span class="aura" aria-hidden="true"></span>

    <!-- 粒子层：花瓣 / 萤火虫 / 切换星屑（Canvas） -->
    <canvas ref="fxEl" class="fx" aria-hidden="true"></canvas>
  </div>
</template>

<script setup>
/**
 * 悬挂式纸灯笼（右上角垂绳）· 日夜切换
 *
 * 摆动物理（rAF 自驱动）：
 *  - 钟摆弹簧：角加速度 = 刚度×(目标角-当前角) - 阻尼×角速度，欠阻尼参数，
 *    让灯笼像挂在真绳上一样带一点回摆。
 *  - 微风：两个慢正弦叠加的目标角（±3°），绳子始终轻轻摇。
 *  - 阵风：每 7~16s 不定期触发一次（初次 3.5~7.5s），包络为
 *    渐强—保持—渐弱，摆幅短暂加大到 6~10°，并叠加高频小幅
 *    「灯笼轻晃」，风停后自然衰减回平静；拖拽期间暂停阵风。
 *
 * 交互手感：
 *  - 拉绳橡皮筋阻力：拉得越深阻力越大，松手 spring 回弹；
 *    超过灯身 1/3 行程触发「点灯/熄灯」。
 *  - 点击 / 空格 / 回车等效一次拉灯；switching 期间锁输入防连击。
 *
 * 视觉：
 *  - 夜间（lit）：灯身暖黄透光 + 光晕 + 萤火虫粒子；日间飘花瓣。
 *  - 切换瞬间：日/月 SVG 旋转交叉 + 星屑爆发，配色经 theme-anim 平滑过渡。
 */
import { onBeforeUnmount, onMounted, reactive, ref } from 'vue'
import { useTheme } from '@/composables/useTheme'
import { useLampMachine } from '@/composables/useLampMachine'

const { isDark, toggle } = useTheme()

const rootEl = ref(null)
const btnEl = ref(null)
const fxEl = ref(null)

/* 拖拽显示的物理量（与状态机解耦，状态机只管是否触发切换） */
const phys = reactive({ displayDrag: 0, scale: 1 })

const rootStyle = reactive({})
function syncRootStyle() {
  rootStyle['--drag'] = `${phys.displayDrag}px`
  rootStyle['--scale'] = phys.scale
  rootStyle['--tilt'] = `${phys.displayDrag * 0.02}deg`
  rootStyle['--ang'] = `${sway.ang}deg`
  rootStyle['--shake'] = `${sway.shake}deg`
}

const machine = useLampMachine({
  onCommit: () => {
    toggle()
    breathe() // 灯亮/灭瞬间呼吸膨胀
    burst() // 星屑爆发：切换的高光时刻
    flashLabel() // 切换后短暂显示状态文案
  },
})

/* 状态文案短暂显示（切换反馈） */
const labelShown = ref(false)
let labelTimer = 0
function flashLabel() {
  labelShown.value = true
  clearTimeout(labelTimer)
  labelTimer = window.setTimeout(() => {
    labelShown.value = false
  }, 2200)
}

/* ------------------------------------------------------------------ */
/* 钟摆物理：微风 + 不定期阵风（rAF 自驱动）                           */
/* ------------------------------------------------------------------ */
const sway = reactive({
  ang: 0, // 当前摆角（deg）
  vel: 0, // 角速度（deg/s）
  shake: 0, // 阵风引起的高频轻晃（deg）
  dragging: false,
})
const REDUCED_MOTION =
  typeof window !== 'undefined' &&
  window.matchMedia?.('(prefers-reduced-motion: reduce)').matches

const swayRaf = { id: 0, last: 0, t0: 0 }
const gust = { nextAt: 0, startAt: 0, dur: 0, amp: 0, dir: 1 }

function scheduleGust(now, first = false) {
  // 不固定间隔：首次 3.5~7.5s，其后 7~16s
  gust.nextAt = now + (first ? 3500 + Math.random() * 4000 : 7000 + Math.random() * 9000)
}

/** 阵风包络：渐强 25% → 保持 30% → 渐弱 45%，返回 0~1 */
function gustEnv(now) {
  const t = (now - gust.startAt) / gust.dur
  if (t <= 0 || t >= 1) return 0
  if (t < 0.25) return t / 0.25
  if (t < 0.55) return 1
  return 1 - (t - 0.55) / 0.45
}

function swayStep(now) {
  swayRaf.id = requestAnimationFrame(swayStep)
  const dt = Math.min(0.05, (now - (swayRaf.last || now)) / 1000)
  swayRaf.last = now
  if (REDUCED_MOTION) return

  const t = (now - swayRaf.t0) / 1000

  // 微风：两个慢正弦叠加，目标角约 ±3°
  let target = 1.8 * Math.sin(t * 0.55) + 1.2 * Math.sin(t * 0.9 + 1.7)

  // 阵风：不定期触发；拖拽期间暂停（包络强制为 0）
  if (!sway.dragging && now >= gust.nextAt) {
    gust.startAt = now
    gust.dur = 2600 + Math.random() * 1200
    gust.amp = 6 + Math.random() * 4
    gust.dir = Math.random() > 0.5 ? 1 : -1
    scheduleGust(now)
  }
  const env = sway.dragging ? 0 : gustEnv(now)
  target += gust.dir * gust.amp * env
  target += gust.dir * 1.5 * env * Math.sin(t * 5) // 风里的二次抖动

  // 钟摆弹簧（欠阻尼，带一点回摆）
  const stiffness = 26
  const damping = 3.4
  sway.vel += (target - sway.ang) * stiffness * dt
  sway.vel *= Math.exp(-damping * dt)
  sway.ang += sway.vel * dt

  // 阵风期间灯笼高频轻晃
  sway.shake = env * (0.9 * Math.sin(t * 27) + 0.5 * Math.sin(t * 43))
  syncRootStyle()
}

function startSway() {
  if (swayRaf.id) return
  swayRaf.t0 = performance.now()
  swayRaf.last = swayRaf.t0
  scheduleGust(swayRaf.t0, true)
  swayRaf.id = requestAnimationFrame(swayStep)
}

function stopSway() {
  if (swayRaf.id) cancelAnimationFrame(swayRaf.id)
  swayRaf.id = 0
}

/* ------------------------------------------------------------------ */
/* 拖拽物理：橡皮筋阻力 + spring 回弹                                 */
/* ------------------------------------------------------------------ */
let startY = 0
let rawDrag = 0
let dragging = false
let lastMoveAt = 0
let animId = 0

/** 橡皮筋映射：输入位移 → 显示位移（越深阻力越大，收敛于 maxDrag） */
function rubberBand(x) {
  const max = 160 // 最大视觉行程
  if (x <= 0) return 0
  // 前 40px 1:1，之后阻尼递增，逼近 max
  return max * (1 - Math.exp((-x / max) * 1.6))
}

function onPointerDown(e) {
  if (!machine.start()) return
  dragging = true
  sway.dragging = true // 拉绳期间暂停阵风
  startY = e.clientY
  rawDrag = 0
  lastMoveAt = performance.now()
  btnEl.value?.setPointerCapture?.(e.pointerId)

  const move = (ev) => {
    if (!dragging) return
    const now = performance.now()
    if (now - lastMoveAt < 16) return // ~16ms 节流
    lastMoveAt = now
    rawDrag = ev.clientY - startY
    const display = rubberBand(rawDrag)
    phys.displayDrag = display
    syncRootStyle()
    // 只把「实际位移」交给状态机判断阈值
    machine.move(display)
  }
  const up = () => {
    if (!dragging) return
    dragging = false
    sway.dragging = false
    window.removeEventListener('pointermove', move)
    window.removeEventListener('pointerup', up)
    window.removeEventListener('pointercancel', up)

    const result = machine.end()
    if (result === 'commit') {
      snapThenRelease() // 吸附补完 → 回弹
    } else {
      springBack() // 未越阈值，弹回原位
    }
  }
  window.addEventListener('pointermove', move, { passive: true })
  window.addEventListener('pointerup', up)
  window.addEventListener('pointercancel', up)
}

/** 越过阈值：先拉到满行程，再缓慢回弹（阻尼感） */
function snapThenRelease() {
  phys.displayDrag = 150
  syncRootStyle()
  window.setTimeout(() => {
    animateTo(0, 260)
    machine.done()
  }, 110)
}

/** 未越阈值：spring 回弹复位 */
function springBack() {
  animateTo(0, 380)
}

/** 用 rAF + ease-out-back 曲线把显示位移动画回目标值 */
function animateTo(target, duration) {
  if (animId) cancelAnimationFrame(animId)
  const from = phys.displayDrag
  const start = performance.now()
  const easeOutBack = (t) => {
    const c1 = 1.70158
    const c3 = c1 + 1
    return 1 + c3 * Math.pow(t - 1, 3) + c1 * Math.pow(t - 1, 2)
  }
  function step(now) {
    const p = Math.min(1, (now - start) / duration)
    const eased = p === 1 ? 1 : easeOutBack(p)
    phys.displayDrag = from + (target - from) * eased
    syncRootStyle()
    if (p < 1) animId = requestAnimationFrame(step)
  }
  animId = requestAnimationFrame(step)
}

/* ------------------------------------------------------------------ */
/* 点击 / 键盘：等效一次拉灯                                            */
/* ------------------------------------------------------------------ */
function onClick() {
  if (machine.isBusy.value) return
  machine.start()
  machine.move(150)
  machine.end()
  phys.displayDrag = 150
  syncRootStyle()
  snapThenRelease()
}

/* ------------------------------------------------------------------ */
/* 呼吸动效：灯亮瞬间膨胀                                              */
/* ------------------------------------------------------------------ */
function breathe() {
  const seq = [
    { s: 1.08, d: 160 },
    { s: 1.0, d: 220 },
  ]
  let i = 0
  function next() {
    if (i >= seq.length) return
    const { s, d } = seq[i++]
    animateScale(s, d, next)
  }
  next()
}

function animateScale(target, duration, cb) {
  const from = phys.scale
  const start = performance.now()
  function step(now) {
    const p = Math.min(1, (now - start) / duration)
    // ease-out
    phys.scale = from + (target - from) * (1 - Math.pow(1 - p, 3))
    syncRootStyle()
    if (p < 1) requestAnimationFrame(step)
    else cb?.()
  }
  requestAnimationFrame(step)
}

/* ------------------------------------------------------------------ */
/* 粒子：花瓣（日间）/ 萤火虫（夜间），Canvas 绘制（>20 强制 Canvas）   */
/* 环境粒子常驻 ≤16，另有切换瞬间的星屑爆发（一次性，自动衰减）        */
/* ------------------------------------------------------------------ */
const PARTICLES = 16
const BURST_COUNT = 12
let fxRunning = false
let fxLoopActive = false
let fxTimer = 0
let fxCtx = null
let fxRect = null
const fxParts = []

/** 按当前控件尺寸重设画布（挂载与窗口 resize 时调用） */
function sizeFx() {
  const canvas = fxEl.value
  const root = rootEl.value
  if (!canvas || !root) return
  fxRect = root.getBoundingClientRect()
  const dpr = window.devicePixelRatio || 1
  canvas.width = fxRect.width * dpr
  canvas.height = fxRect.height * dpr
  canvas.style.width = `${fxRect.width}px`
  canvas.style.height = `${fxRect.height}px`
  fxCtx = canvas.getContext('2d')
  fxCtx.setTransform(dpr, 0, 0, dpr, 0, 0)
}

/** 确保 rAF 循环在跑（没有粒子时自动停机，省电） */
function ensureLoop() {
  if (fxLoopActive || !fxRunning) return
  fxLoopActive = true
  requestAnimationFrame(fxLoop)
}

/** 环境粒子投放：日间花瓣/光点，夜间萤火虫 */
function spawnAmbient() {
  if (!fxRunning || !fxRect) return
  if (fxParts.length < PARTICLES) {
    if (!isDark.value) {
      // 日间：飘落小花 / 蒲公英光点（暖色）
      fxParts.push({
        x: Math.random() * fxRect.width,
        y: -8,
        vx: (Math.random() - 0.5) * 0.4,
        vy: 0.5 + Math.random() * 0.8,
        r: 1.5 + Math.random() * 2.5,
        c: ['#ffd9a0', '#ffb7c5', '#f7dc6f'][(Math.random() * 3) | 0],
        kind: Math.random() > 0.5 ? 'dot' : 'petal',
        life: 1,
      })
    } else {
      // 夜间：萤火虫光点，带微光
      fxParts.push({
        x: Math.random() * fxRect.width,
        y: fxRect.height * (0.2 + Math.random() * 0.6),
        vx: (Math.random() - 0.5) * 0.6,
        vy: (Math.random() - 0.5) * 0.4,
        r: 1 + Math.random() * 2,
        c: '#c8ffb0',
        kind: 'firefly',
        life: 1,
      })
    }
  }
  fxTimer = window.setTimeout(spawnAmbient, 220)
  ensureLoop()
}

/** 切换瞬间：从灯身中心向外爆发一圈星屑（四芒星闪烁） */
function burst() {
  if (!fxCtx || !fxRect) return
  const cx = fxRect.width / 2
  const cy = fxRect.height * 0.42 // 约等于灯身中心
  for (let i = 0; i < BURST_COUNT; i++) {
    const a = Math.random() * Math.PI * 2
    const sp = 1.4 + Math.random() * 2.2
    fxParts.push({
      x: cx,
      y: cy,
      vx: Math.cos(a) * sp,
      vy: Math.sin(a) * sp - 0.6,
      r: 1.2 + Math.random() * 1.8,
      c: isDark.value ? '#c8ffb0' : '#ffd76e',
      kind: 'burst',
      life: 1,
      tw: Math.random() * Math.PI * 2,
    })
  }
  ensureLoop()
}

function fxLoop() {
  if (!fxRunning || !fxCtx || !fxRect) {
    fxLoopActive = false
    return
  }
  const ctx = fxCtx
  const { width, height } = fxRect
  ctx.clearRect(0, 0, width, height)
  for (let i = fxParts.length - 1; i >= 0; i--) {
    const p = fxParts[i]

    if (p.kind === 'burst') {
      // 星屑：向外扩散 + 轻微重力 + 四芒星闪烁，快速衰减
      p.x += p.vx
      p.y += p.vy
      p.vx *= 0.96
      p.vy = p.vy * 0.96 + 0.02
      p.life -= 0.028
      if (p.life <= 0) {
        fxParts.splice(i, 1)
        continue
      }
      ctx.globalAlpha = Math.max(0, p.life)
      ctx.strokeStyle = p.c
      ctx.lineWidth = 1.4
      ctx.lineCap = 'round'
      const s = p.r * (0.6 + 0.6 * Math.abs(Math.sin(p.tw + i * 0.3))) * p.life + 1
      ctx.beginPath()
      ctx.moveTo(p.x - s, p.y)
      ctx.lineTo(p.x + s, p.y)
      ctx.moveTo(p.x, p.y - s)
      ctx.lineTo(p.x, p.y + s)
      ctx.stroke()
      continue
    }

    p.x += p.vx
    p.y += p.vy
    p.life -= 0.004
    if (p.kind === 'firefly') {
      // 萤火虫闪烁
      p.alpha = 0.4 + 0.6 * Math.abs(Math.sin(i * 0.08))
    }
    if (p.y > height + 12 || p.life <= 0) {
      fxParts.splice(i, 1)
      continue
    }
    ctx.globalAlpha = p.kind === 'firefly' ? p.alpha : Math.max(0, p.life)
    ctx.fillStyle = p.c
    if (p.kind === 'petal') {
      ctx.save()
      ctx.translate(p.x, p.y)
      ctx.rotate(Math.sin(i * 0.1))
      ctx.fillRect(-p.r, -p.r * 0.5, p.r * 2, p.r)
      ctx.restore()
    } else {
      ctx.beginPath()
      ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2)
      ctx.fill()
    }
  }
  ctx.globalAlpha = 1
  if (fxParts.length) {
    requestAnimationFrame(fxLoop)
  } else {
    fxLoopActive = false
  }
}

function startFx() {
  if (fxRunning) return
  fxRunning = true
  sizeFx()
  spawnAmbient()
}

/* ------------------------------------------------------------------ */
/* 生命周期                                                            */
/* ------------------------------------------------------------------ */
onMounted(() => {
  machine.state.maxDrag = 160
  syncRootStyle()
  startSway()
  startFx()
  window.addEventListener('resize', sizeFx)
})

onBeforeUnmount(() => {
  if (animId) cancelAnimationFrame(animId)
  stopSway()
  clearTimeout(labelTimer)
  if (fxTimer) clearTimeout(fxTimer)
  fxRunning = false
  fxParts.length = 0
  window.removeEventListener('resize', sizeFx)
})
</script>

<style scoped>
/* ============ 根：右上角悬挂，容器不拦截点击 ============ */
.lantern {
  position: fixed;
  top: 0;
  right: 26px;
  z-index: 90;
  width: 96px;
  display: flex;
  flex-direction: column;
  align-items: center;
  pointer-events: none;
  user-select: none;
  /* 动态变量 */
  --drag: 0px;
  --scale: 1;
  --ang: 0deg;
  --shake: 0deg;
  --tilt: 0deg;
  --rope-h: 48px;
  /* 根容器不持有 transform/filter：避免整个子树常驻合成层与滤镜层导致文字发糊 */
}

/* 顶端挂钩（小圆座 + 金色吊环），不随摆动旋转 */
.ceiling-hook {
  position: absolute;
  top: -2px;
  left: 50%;
  transform: translateX(-50%);
  width: 18px;
  height: 8px;
  border-radius: 4px;
  background: linear-gradient(180deg, #ffeebc, #e0b264);
  box-shadow: 0 2px 4px rgba(224, 178, 100, 0.35);
  z-index: 2;
}
.ceiling-hook::after {
  content: '';
  position: absolute;
  left: 50%;
  top: 5px;
  transform: translateX(-50%);
  width: 4px;
  height: 7px;
  border-radius: 2px;
  background: var(--lantern-gold);
}

/* ============ 摆动体：绕顶端旋转的钟摆（缩放并入同一变换） ============ */
.swing {
  position: relative;
  display: flex;
  flex-direction: column;
  align-items: center;
  transform: rotate(var(--ang)) scale(var(--scale));
  transform-origin: 50% 0;
  will-change: transform;
}

/* ---- 挂绳：樱粉→薰衣草渐变彩绳 + 末端金环绳结 ---- */
.rope {
  position: relative;
  width: 3px;
  height: var(--rope-h);
  background: linear-gradient(to bottom, var(--lamp-sakura), var(--lamp-lavender));
  border-radius: 2px;
  box-shadow: 1px 0 2px rgba(214, 140, 180, 0.25);
  flex-shrink: 0;
}
.rope::after {
  content: '';
  position: absolute;
  bottom: -4px;
  left: 50%;
  transform: translateX(-50%);
  width: 9px;
  height: 7px;
  border-radius: 50%;
  background: radial-gradient(circle at 35% 30%, #ffe9b8, var(--lamp-gold));
}

/* ============ 顶部金黄圆顶盖 + 翘角装饰 ============ */
.top-rail {
  position: relative;
  width: 42px;
  height: 10px;
  margin-top: 3px;
  background: linear-gradient(180deg, #ffeebc, var(--lamp-gold));
  border-radius: 8px 8px 4px 4px;
  box-shadow: 0 2px 5px rgba(247, 190, 100, 0.35);
  flex-shrink: 0;
}
.grain {
  position: absolute;
  inset: 2px 6px;
  background: repeating-linear-gradient(
    90deg,
    rgba(255, 255, 255, 0.35) 0 2px,
    transparent 2px 5px
  );
  border-radius: 2px;
}
.corner {
  position: absolute;
  top: -3px;
  width: 7px;
  height: 7px;
  background: var(--lamp-gold);
  border-radius: 50%;
  box-shadow: 0 1px 3px rgba(247, 190, 100, 0.4);
}
.corner.c1 { left: -3px; }
.corner.c2 { right: -3px; }
.corner.c3 { left: 7px; opacity: 0.55; top: -4px; width: 5px; height: 5px; }
.corner.c4 { right: 7px; opacity: 0.55; top: -4px; width: 5px; height: 5px; }
.handle {
  position: absolute;
  top: -9px;
  left: 50%;
  width: 2px;
  height: 9px;
  margin-left: -1px;
  background: var(--lamp-gold);
  border-radius: 2px;
}

/* ============ 灯身：樱粉圆润灯罩 + 波点 + 花边 ============ */
.body {
  position: relative;
  width: 56px;
  height: 54px;
  border-radius: 50% 50% 48% 48% / 56% 56% 44% 44%;
  background: linear-gradient(165deg, #ffe6f1 0%, #ffc3d9 52%, #ff9fc4 100%);
  box-shadow: 0 6px 18px rgba(255, 159, 196, 0.42),
    inset 0 -4px 8px rgba(255, 130, 170, 0.22);
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
  transition: box-shadow 0.6s var(--bm-ease), background 0.6s var(--bm-ease);
  /* 拉拽倾斜 + 阵风轻晃叠加 */
  transform: rotate(calc(var(--tilt) + var(--shake)));
}
.paper {
  position: absolute;
  inset: 0;
  background: radial-gradient(circle at 50% 28%, rgba(255, 255, 255, 0.55), transparent 62%);
}
/* 卡通纹样：白色波点 + 一颗小星星 */
.pattern {
  position: absolute;
  inset: 0;
  border-radius: inherit;
  opacity: 0.65;
  background-image: radial-gradient(circle 2.4px at 22% 26%, rgba(255, 255, 255, 0.95) 98%, transparent),
    radial-gradient(circle 1.8px at 70% 20%, rgba(255, 255, 255, 0.85) 98%, transparent),
    radial-gradient(circle 2.2px at 80% 52%, rgba(255, 255, 255, 0.8) 98%, transparent),
    radial-gradient(circle 1.8px at 26% 62%, rgba(255, 255, 255, 0.85) 98%, transparent),
    radial-gradient(circle 1.4px at 52% 74%, rgba(255, 255, 255, 0.7) 98%, transparent);
}
/* 蕾丝花边：底部一圈半圆扇边 */
.frill {
  position: absolute;
  left: 10%;
  right: 10%;
  bottom: 4px;
  height: 6px;
  background: radial-gradient(circle 3.2px at 50% 0, rgba(255, 255, 255, 0.8) 97%, transparent)
    repeat-x;
  background-size: 9px 6px;
  opacity: 0.7;
}
.inner-glow {
  position: absolute;
  inset: 14%;
  border-radius: 50%;
  background: radial-gradient(circle, rgba(255, 244, 214, 0.55), transparent 70%);
  opacity: 0;
  transition: opacity 0.6s var(--bm-ease);
}

.body-icon {
  position: relative;
  z-index: 2;
  display: block;
  width: 27px;
  height: 27px;
}
.icon-svg {
  display: block;
  width: 100%;
  height: 100%;
}

/* 日/月图标旋转交叉过渡：旧图标旋出、新图标旋入，带弹簧回弹 */
.icon-swap-enter-active,
.icon-swap-leave-active {
  transition: transform 0.38s var(--bm-ease-spring), opacity 0.26s var(--bm-ease);
  transform-origin: center;
}
.icon-swap-enter-from {
  transform: rotate(140deg) scale(0.2);
  opacity: 0;
}
.icon-swap-leave-to {
  transform: rotate(-140deg) scale(0.2);
  opacity: 0;
}

/* 太阳光芒缓慢旋转（慵懒的午后感） */
.sun-rays {
  transform-origin: 24px 24px;
  animation: sun-rays-spin 14s linear infinite;
}
@keyframes sun-rays-spin {
  to {
    transform: rotate(360deg);
  }
}

/* 月亮旁的小星星：错峰眨眼 */
.moon-star {
  transform-box: fill-box;
  transform-origin: center;
  animation: star-blink 2.6s ease-in-out infinite;
}
.moon-star.s1 { animation-delay: 0s; }
.moon-star.s2 { animation-delay: 0.9s; }
.moon-star.s3 { animation-delay: 1.7s; }
@keyframes star-blink {
  0%, 100% { transform: scale(0.55); opacity: 0.4; }
  50% { transform: scale(1.1); opacity: 1; }
}

/* 夜间（灯亮）图标泛暖光 */
.lantern.lit .icon-svg {
  filter: drop-shadow(0 0 6px rgba(255, 235, 170, 0.8));
}

/* ============ 底座：金黄圆底盖 ============ */
.bottom-rim {
  width: 30px;
  height: 7px;
  margin-top: -1px;
  background: linear-gradient(180deg, var(--lamp-gold), #eba95c);
  border-radius: 4px 4px 7px 7px;
  flex-shrink: 0;
  box-shadow: 0 2px 4px rgba(235, 169, 92, 0.3);
}

/* ============ 流苏拉绳（交互把手） ============ */
.cord {
  position: relative;
  display: flex;
  flex-direction: column;
  align-items: center;
  border: none;
  background: transparent;
  padding: 0;
  cursor: grab;
  touch-action: none;
  -webkit-tap-highlight-color: transparent;
  outline: none;
  pointer-events: auto; /* 容器 pointer-events:none，仅拉绳可交互 */
  /* 拉绳随拖拽伸展：用 --drag 驱动高度 */
  height: calc(48px + var(--drag));
  min-width: 48px; /* 宽裕的点击热区 */
  transition: height 0.16s var(--bm-ease-spring-soft);
}
.cord:active {
  cursor: grabbing;
}

.cord-threads {
  position: absolute;
  top: 0;
  left: 50%;
  transform: translateX(-50%);
  width: 26px;
  height: 100%;
  display: flex;
  justify-content: center;
  gap: 2px;
  pointer-events: none;
}
.thread {
  width: 2px;
  height: 100%;
  border-radius: 2px;
  background: linear-gradient(
    to bottom,
    var(--lantern-gold),
    var(--lantern-cherry) 60%,
    var(--lantern-gold)
  );
  opacity: 0.85;
  transform-origin: top center;
}
.thread:nth-child(odd) {
  background: linear-gradient(
    to bottom,
    var(--lantern-cherry),
    var(--lantern-gold) 70%
  );
}

.cord-bead {
  position: absolute;
  bottom: 0;
  left: 50%;
  transform: translateX(-50%);
  width: 11px;
  height: 11px;
  border-radius: 50%;
  background: radial-gradient(circle at 35% 30%, #fff, #ffc9d9 55%, #f08fb4);
  box-shadow: 0 2px 6px rgba(240, 143, 180, 0.4);
}

/* 焦点态：琉璃珠发光 */
.cord:focus-visible .cord-bead {
  box-shadow: 0 0 0 3px var(--lantern-gold), 0 0 16px 4px rgba(247, 220, 111, 0.6);
}

/* ============ 状态文案 + 颜文字 ============ */
.lantern-label {
  margin-top: 8px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 2px;
  opacity: 0;
  transform: translateY(-4px);
  transition: opacity 0.25s var(--bm-ease), transform 0.25s var(--bm-ease);
}
/* 悬停/聚焦拉绳（hover 会沿祖先链上溯到根），或切换后的 2 秒内显示 */
.lantern:hover .lantern-label,
.lantern.show-label .lantern-label {
  opacity: 1;
  transform: translateY(0);
}
.lantern-label .txt {
  font-size: 12px;
  font-weight: 800;
  letter-spacing: 3px;
  color: #f77fa8;
  font-family: 'Zen Maru Gothic', 'Quicksand', sans-serif;
  white-space: nowrap;
  text-shadow: 0 1px 4px rgba(255, 176, 200, 0.45);
}
.lantern-label .face {
  font-size: 11px;
  color: var(--bm-text-sub);
  letter-spacing: 1px;
  white-space: nowrap;
}

/* ============ 灯亮光晕（粉金光晕，衬在灯身背后） ============ */
.aura {
  position: absolute;
  top: calc(var(--rope-h) + 38px);
  left: 50%;
  width: 110px;
  height: 110px;
  transform: translate(-50%, -50%);
  border-radius: 50%;
  background: radial-gradient(
    circle,
    rgba(255, 205, 130, 0.42) 0%,
    rgba(255, 176, 200, 0.22) 45%,
    transparent 70%
  );
  filter: blur(13px);
  opacity: 0;
  transition: opacity 0.6s var(--bm-ease);
  pointer-events: none;
}

/* ============ 粒子层 ============ */
.fx {
  position: absolute;
  top: -40px;
  left: -40px;
  width: calc(100% + 80px);
  height: calc(100% + 80px);
  pointer-events: none;
}

/* ============ 灯亮（夜间模式）状态：暖金灯罩 + 金粉光晕 ============ */
.lantern.lit .body {
  background: linear-gradient(165deg, #fff3c9 0%, #ffd28a 52%, #ffb05e 100%);
  box-shadow: 0 0 26px 8px rgba(255, 200, 110, 0.6),
    inset 0 -4px 8px rgba(255, 150, 80, 0.25);
}
.lantern.lit .inner-glow {
  opacity: 1;
}
.lantern.lit .aura {
  opacity: 1;
}
.lantern.lit .lantern-label .txt {
  color: var(--lantern-gold);
}

/* 根级 filter 亮度呼吸动画已移除：filter 会把整个子树压进一个滤镜合成层，
   灯笼文字因此常驻灰度抗锯齿（发糊），且每帧合成开销大、得不偿失 */

/* ============ 尊重「减少动态效果」 ============ */
@media (prefers-reduced-motion: reduce) {
  .lantern {
    transition: opacity 0.2s linear, background-color 0.2s linear;
  }
  .swing {
    transform: none;
  }
  .body {
    transform: none;
  }
  .cord {
    transition: opacity 0.2s linear;
  }
  .fx,
  .aura {
    display: none;
  }
  .sun-rays,
  .moon-star {
    animation: none;
  }
  .icon-swap-enter-active,
  .icon-swap-leave-active {
    transition: opacity 0.2s linear;
  }
  .icon-swap-enter-from,
  .icon-swap-leave-to {
    transform: none;
  }
}

/* ============ 移动端：灯笼缩小、贴边，保证 320px 可用 ============ */
@media (max-width: 480px) {
  .lantern {
    right: 8px;
    width: 84px;
    --rope-h: 40px;
  }
  .top-rail {
    width: 36px;
  }
  .body {
    width: 46px;
    height: 44px;
  }
  .body-icon {
    width: 23px;
    height: 23px;
  }
  .bottom-rim {
    width: 26px;
  }
  .cord {
    height: calc(44px + var(--drag));
    min-width: 44px; /* 移动端触控热区 ≥44px */
  }
  .cord-threads {
    width: 22px;
  }
  .aura {
    width: 92px;
    height: 92px;
    top: calc(var(--rope-h) + 30px);
  }
}
</style>
