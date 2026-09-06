<template>
  <div class="snow-fall" aria-hidden="true">
    <span
      v-for="flake in flakes"
      :key="flake.id"
      class="flake"
      :style="flakeStyle(flake)"
    ></span>
  </div>
</template>

<script setup>
import { onBeforeUnmount, onMounted, ref } from 'vue'

/**
 * 雪花飘落特效组件
 * - 全屏覆盖，不拦截交互（pointer-events: none）
 * - 随机大小 / 透明度 / 下落速度 / 左右摆动
 * - 循环播放，雪花从顶部持续生成、底部消失
 * - 适配深色模式与「减少动态效果」系统设置
 */

const props = defineProps({
  /** 雪花数量，不传则根据屏幕宽度自动计算 */
  count: { type: Number, default: 0 },
  /** 雪花基础颜色（可由外部覆盖） */
  color: { type: String, default: '' },
})

const flakes = ref([])
let rafId = null

/** 根据屏幕宽度计算合适的雪花数量 */
function calcCount() {
  if (props.count > 0) return props.count
  const w = window.innerWidth
  if (w < 640) return 16
  if (w < 1024) return 28
  return 44
}

/** 生成随机雪花配置 */
function generateFlakes() {
  const count = calcCount()
  const list = []
  for (let i = 0; i < count; i++) {
    list.push({
      id: i,
      // 水平位置（%）
      left: Math.random() * 100,
      // 大小（px）
      size: 2 + Math.random() * 7,
      // 透明度
      opacity: 0.25 + Math.random() * 0.65,
      // 下落时长（秒）——越小越快
      duration: 7 + Math.random() * 14,
      // 动画延迟（秒）——错开起始位置，避免同时出现
      delay: -Math.random() * 20,
      // 左右摆动幅度（px）
      sway: 18 + Math.random() * 42,
      // 摆动节奏（秒）——左右往返一次的时间
      swayDuration: 3 + Math.random() * 5,
    })
  }
  flakes.value = list
}

/** 生成单片雪花的内联样式 */
function flakeStyle(f) {
  const style = {
    left: `${f.left}%`,
    width: `${f.size}px`,
    height: `${f.size}px`,
    opacity: f.opacity,
    animationDuration: `${f.duration}s, ${f.swayDuration}s`,
    animationDelay: `${f.delay}s, ${f.delay * 0.6}s`,
    '--sway-x': `${f.sway}px`,
  }
  if (props.color) {
    style.background = props.color
    style.boxShadow = `0 0 ${f.size * 1.5}px ${props.color}`
  }
  return style
}

/** 监听窗口尺寸变化，重新生成雪花数量 */
function onResize() {
  if (rafId) cancelAnimationFrame(rafId)
  rafId = requestAnimationFrame(() => {
    generateFlakes()
  })
}

onMounted(() => {
  generateFlakes()
  window.addEventListener('resize', onResize, { passive: true })
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', onResize)
  if (rafId) cancelAnimationFrame(rafId)
})
</script>

<style scoped>
.snow-fall {
  position: fixed;
  inset: 0;
  z-index: 0;
  pointer-events: none;
  overflow: hidden;
}

.flake {
  position: absolute;
  top: -10px;
  border-radius: 50%;
  background: #eaf2ff;
  box-shadow: 0 0 6px rgba(200, 220, 255, 0.8);
  will-change: transform;
  /* 两个动画：下落 + 左右摆动；sway-x 由内联样式注入 */
  animation-name: snow-fall, snow-sway;
  animation-timing-function: linear, ease-in-out;
  animation-iteration-count: infinite, infinite;
  animation-direction: normal, alternate;
}

/* ---- 下落动画：从顶部到视窗底部外 ---- */
@keyframes snow-fall {
  0% {
    transform: translateY(-10vh);
  }
  100% {
    transform: translateY(110vh);
  }
}

/* ---- 左右摆动：用独立的 translate 属性（合成器动画，零布局开销）
   之前用 margin-left 会每帧触发布局重排，是雪天卡顿的元凶 ---- */
@keyframes snow-sway {
  0% {
    translate: calc(var(--sway-x) * -1) 0;
  }
  100% {
    translate: var(--sway-x) 0;
  }
}

/* 深色模式下调整雪花配色，更有层次感 */
html.dark .flake {
  background: #d8e6ff;
  box-shadow: 0 0 8px rgba(180, 200, 255, 0.7);
}

/* 移动端减少雪花尺寸与发光，降低合成开销 */
@media (max-width: 768px) {
  .flake {
    box-shadow: 0 0 4px rgba(200, 220, 255, 0.6);
  }
}

/* 尊重系统的「减少动态效果」设置 */
@media (prefers-reduced-motion: reduce) {
  .flake {
    animation: none;
    display: none;
  }
}
</style>
