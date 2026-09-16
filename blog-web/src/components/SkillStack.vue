<template>
  <section ref="rootRef" class="bm-module skill-stack">
    <header class="bm-module__head">
      <h3 class="bm-module__title"><i class="bm-module__dot"></i>{{ title }}</h3>
      <span v-if="subtitle" class="bm-module__sub">{{ subtitle }}</span>
    </header>

    <ul class="skills">
      <li
        v-for="(s, i) in skills"
        :key="s.name"
        class="skill"
        :class="{ 'is-in': visible }"
        :style="{ '--delay': `${i * stagger}ms`, '--bar-dur': `${duration}ms` }"
      >
        <div class="skill__top">
          <span class="skill__name">{{ s.name }}</span>
          <span class="skill__value">{{ shown[i] }}%</span>
        </div>
        <div
          class="skill__track"
          role="progressbar"
          :aria-label="s.name"
          :aria-valuenow="shown[i]"
          aria-valuemin="0"
          aria-valuemax="100"
        >
          <span class="skill__bar" :style="{ width: `${visible ? s.percent : 0}%` }"></span>
        </div>
      </li>
    </ul>
  </section>
</template>

<script setup>
import { onBeforeUnmount, onMounted, ref, watch } from 'vue'

const props = defineProps({
  /** 技能数组：{ name, percent }，默认提供 8 条示例 */
  skills: {
    type: Array,
    default: () => [
      { name: 'Vue 3 / 组合式 API', percent: 92 },
      { name: 'JavaScript / TypeScript', percent: 88 },
      { name: 'CSS / 动画与响应式', percent: 85 },
      { name: 'Vite / 前端工程化', percent: 80 },
      { name: 'FastAPI / Python', percent: 78 },
      { name: 'MySQL / Redis', percent: 72 },
      { name: 'Git / 协作流程', percent: 75 },
      { name: 'UI 设计 / 交互细节', percent: 70 },
    ],
  },
  /** 条目之间的错峰延迟（毫秒） */
  stagger: { type: Number, default: 90 },
  /** 单条进度增长时长（毫秒） */
  duration: { type: Number, default: 900 },
  title: { type: String, default: '技能栈' },
  subtitle: { type: String, default: '' },
})

const rootRef = ref(null)
const visible = ref(false)
const shown = ref(props.skills.map(() => 0))

let rafId = 0
let observer = null
const reduceMotion =
  typeof window !== 'undefined' &&
  window.matchMedia &&
  window.matchMedia('(prefers-reduced-motion: reduce)').matches

/** 数值由 0 递增到目标值，与进度条同频（每条按 stagger 错峰） */
function countUp() {
  const targets = props.skills.map((s) => Math.max(0, Math.min(100, Number(s.percent) || 0)))
  if (reduceMotion) {
    shown.value = targets
    return
  }
  const start = performance.now()
  const step = (now) => {
    const elapsed = now - start
    shown.value = targets.map((v, i) => {
      const t = Math.min(1, Math.max(0, (elapsed - i * props.stagger) / props.duration))
      const eased = 1 - Math.pow(1 - t, 3) // easeOutCubic
      return Math.round(v * eased)
    })
    if (elapsed < props.duration + props.stagger * (targets.length - 1)) {
      rafId = requestAnimationFrame(step)
    } else {
      shown.value = targets
    }
  }
  rafId = requestAnimationFrame(step)
}

onMounted(() => {
  if (typeof IntersectionObserver === 'undefined') {
    visible.value = true
    countUp()
    return
  }
  observer = new IntersectionObserver(
    (entries) => {
      for (const entry of entries) {
        if (entry.isIntersecting) {
          visible.value = true
          countUp()
          observer.disconnect()
          observer = null
        }
      }
    },
    { threshold: 0.25 }
  )
  observer.observe(rootRef.value)
})

watch(
  () => props.skills,
  (val) => {
    shown.value = val.map(() => 0)
    if (visible.value) countUp()
  }
)

onBeforeUnmount(() => {
  if (observer) observer.disconnect()
  if (rafId) cancelAnimationFrame(rafId)
})
</script>

<style scoped>
.skills {
  list-style: none;
  margin: 0;
  padding: 0;
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 14px var(--bm-module-gap);
}

.skill {
  opacity: 0;
  transform: translateY(10px);
  transition: opacity 0.5s var(--bm-ease) var(--delay),
    transform 0.5s var(--bm-ease-bounce) var(--delay);
}

.skill.is-in {
  opacity: 1;
  transform: none;
}

.skill__top {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 10px;
  margin-bottom: 7px;
  font-size: 13px;
}

.skill__name {
  color: var(--bm-text);
  font-weight: 600;
  overflow: hidden;
  white-space: nowrap;
  text-overflow: ellipsis;
}

.skill__value {
  flex: none;
  font-size: 12.5px;
  font-weight: 700;
  color: var(--bm-primary-2);
  font-variant-numeric: tabular-nums;
}

.skill__track {
  position: relative;
  height: 10px;
  border-radius: 999px;
  background: var(--bm-primary-soft);
  overflow: hidden;
}

.skill__bar {
  display: block;
  height: 100%;
  width: 0;
  border-radius: 999px;
  background: var(--bm-gradient);
  box-shadow: 0 2px 10px var(--bm-shadow-color);
  /* 由左向右增长，错峰由 --delay 控制 */
  transition: width var(--bar-dur, 0.9s) var(--bm-ease) var(--delay);
}

.skill__bar::after {
  /* 高光条：入场后才有光泽流动，避免未进入视口就开始动画 */
  content: '';
  position: absolute;
  inset: 0;
  border-radius: 999px;
  background: linear-gradient(
    100deg,
    transparent 0%,
    rgba(255, 255, 255, 0.35) 48%,
    transparent 100%
  );
  transform: translateX(-100%);
}

.skill.is-in .skill__bar::after {
  animation: bar-shine 2.8s var(--bm-ease) var(--delay) infinite;
}

@keyframes bar-shine {
  0% { transform: translateX(-100%); }
  60%, 100% { transform: translateX(220%); }
}

/* 移动端：单列 */
@media (max-width: 640px) {
  .skills {
    grid-template-columns: 1fr;
  }
}

@media (prefers-reduced-motion: reduce) {
  .skill {
    opacity: 1;
    transform: none;
    transition: none;
  }
  .skill__bar {
    transition: none;
  }
  .skill__bar::after {
    animation: none;
  }
}
</style>
