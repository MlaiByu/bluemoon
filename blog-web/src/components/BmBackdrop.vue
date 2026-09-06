<template>
  <!-- 全站装饰背景：柔和光斑 + 几何点缀 + 夜间星空（纯 CSS，不参与交互） -->
  <div class="bm-backdrop" :class="{ night: isDark }" aria-hidden="true">
    <span class="orb orb-a"></span>
    <span class="orb orb-b"></span>
    <span class="orb orb-c"></span>
    <span class="dots"></span>
    <!-- 夜间模式专属：缓慢闪烁的星星（日间透明隐藏） -->
    <span
      v-for="s in stars"
      :key="s.id"
      class="star"
      :style="starStyle(s)"
    ></span>
  </div>
</template>

<script setup>
/**
 * 装饰性背景组件
 * 原 FrontLayout 与 PostDetail 各写了一份 .bg-deco，此处统一，
 * 便于全站统一光斑配色并随主题变量联动。
 *
 * 夜间模式（html.dark）：追加一层闪烁星空，营造「深邃夜空」氛围；
 * 日间星星层完全透明，不产生任何视觉与性能负担。
 */
import { onMounted, ref } from 'vue'
import { useTheme } from '@/composables/useTheme'

const { isDark } = useTheme()

/* 星星数量随屏宽收缩，移动端更少以保性能 */
const stars = ref([])
function generateStars() {
  const w = window.innerWidth
  const count = w < 640 ? 14 : w < 1024 ? 22 : 32
  const list = []
  for (let i = 0; i < count; i++) {
    list.push({
      id: i,
      left: Math.random() * 100,
      top: Math.random() * 82, // 集中在上部 82% 区域
      size: 1 + Math.random() * 1.8,
      opacity: 0.45 + Math.random() * 0.5,
      duration: 2.4 + Math.random() * 3.6,
      delay: -Math.random() * 5,
    })
  }
  stars.value = list
}

function starStyle(s) {
  return {
    left: `${s.left}%`,
    top: `${s.top}%`,
    width: `${s.size}px`,
    height: `${s.size}px`,
    '--o': s.opacity,
    '--dur': `${s.duration}s`,
    '--delay': `${s.delay}s`,
  }
}

onMounted(generateStars)
</script>

<style scoped>
.bm-backdrop {
  position: fixed;
  inset: 0;
  z-index: 0;
  pointer-events: none;
  overflow: hidden;
}

/* ---- 柔和光斑 ---- */
.orb {
  position: absolute;
  border-radius: 50%;
  filter: blur(80px);
  opacity: 0.55;
  will-change: transform;
}

.orb-a {
  width: 460px;
  height: 460px;
  top: -150px;
  left: -120px;
  background: radial-gradient(circle, var(--bm-glow-blue), transparent 70%);
  animation: drift-a 18s ease-in-out infinite;
}

.orb-b {
  width: 500px;
  height: 500px;
  bottom: -190px;
  right: -140px;
  background: radial-gradient(circle, var(--bm-glow-pink), transparent 70%);
  animation: drift-b 22s ease-in-out infinite;
}

.orb-c {
  width: 320px;
  height: 320px;
  top: 38%;
  left: 46%;
  background: radial-gradient(circle, var(--bm-glow-mint), transparent 70%);
  animation: drift-c 26s ease-in-out infinite;
}

/* ---- 几何点缀：细点阵 ---- */
.dots {
  position: absolute;
  inset: 0;
  background-image: radial-gradient(var(--bm-dot) 1px, transparent 1px);
  background-size: 26px 26px;
  opacity: 0.5;
  mask-image: radial-gradient(ellipse at 50% 0%, #000 20%, transparent 78%);
  -webkit-mask-image: radial-gradient(ellipse at 50% 0%, #000 20%, transparent 78%);
}

/* ---- 夜间星空：仅深色模式显现，缓慢明暗闪烁 ---- */
.star {
  position: absolute;
  border-radius: 50%;
  background: #fff;
  opacity: 0;
  box-shadow: 0 0 6px 1px rgba(255, 255, 255, 0.5);
  transition: opacity 0.9s var(--bm-ease);
  pointer-events: none;
}

.night .star {
  opacity: var(--o, 0.7);
  animation: star-twinkle var(--dur, 3s) ease-in-out var(--delay, 0s) infinite alternate;
}

@keyframes star-twinkle {
  from {
    opacity: calc(var(--o, 0.7) * 0.3);
  }
  to {
    opacity: var(--o, 0.7);
  }
}

@keyframes drift-a {
  0%,
  100% {
    transform: translate(0, 0);
  }
  50% {
    transform: translate(38px, 26px);
  }
}

@keyframes drift-b {
  0%,
  100% {
    transform: translate(0, 0);
  }
  50% {
    transform: translate(-34px, -24px);
  }
}

@keyframes drift-c {
  0%,
  100% {
    transform: translate(0, 0) scale(1);
  }
  50% {
    transform: translate(-20px, 30px) scale(1.08);
  }
}

/* 移动端：减少装饰元素数量，降低合成开销 */
@media (max-width: 768px) {
  .orb-c {
    display: none;
  }
  .orb {
    filter: blur(60px);
    opacity: 0.42;
  }
}

/* 尊重系统的「减少动态效果」设置 */
@media (prefers-reduced-motion: reduce) {
  .orb {
    animation: none;
  }
  .night .star {
    animation: none;
    opacity: calc(var(--o, 0.7) * 0.6);
  }
}
</style>
