<template>
  <section ref="rootRef" class="lsg" :class="{ 'is-in': shown, 'is-focus': activeIndex !== null }">
    <figure
      v-for="(img, i) in items"
      :key="img.key"
      class="lsg__cell"
      :style="{ '--i': i }"
      :class="{ 'is-active': activeIndex === i }"
      @mouseenter="activeIndex = i"
      @mouseleave="activeIndex = null"
      @click="open(i)"
    >
      <div class="lsg__media">
        <img
          v-if="img.url"
          :src="img.url"
          :alt="img.title"
          class="lsg__img"
          loading="lazy"
          decoding="async"
        />
        <div v-else class="lsg__ph" :style="{ background: img.bg }">
          <span class="lsg__ph-title">{{ img.title }}</span>
        </div>

        <!-- 底部光影遮罩（默认渐隐，聚焦时提亮） -->
        <span class="lsg__mask"></span>
        <!-- 掠光：聚焦时一道光斜扫而过 -->
        <span class="lsg__shine"></span>
      </div>

      <figcaption class="lsg__cap">
        <span class="lsg__title" :title="img.title">{{ img.title }}</span>
        <span v-if="img.desc" class="lsg__desc">{{ img.desc }}</span>
      </figcaption>
    </figure>

    <p v-if="!items.length" class="lsg__empty">暂无图片</p>

    <!-- 灯箱（由本组件统一管理，避免外部重复样板） -->
    <GalleryLightbox v-model="lightboxIndex" :images="items" />
  </section>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import GalleryLightbox from './GalleryLightbox.vue'

const props = defineProps({
  /** 真实图片：{ url, title, desc? }；url 为空时按 bg 渐变占位 */
  images: { type: Array, default: () => [] },
  /** 入场错峰间隔（毫秒） */
  stagger: { type: Number, default: 80 },
})

/* ---------- 示例占位：API 无图时填充，保证版式与描述完整 ---------- */
const SAMPLES = [
  { title: '晨雾小巷', desc: '青灰与晨光', bg: 'linear-gradient(135deg,#8ab6ff,#c3aed6)' },
  { title: '窗边午后', desc: '暖橘与白纱', bg: 'linear-gradient(135deg,#ffdf8a,#ffb0c8)' },
  { title: '暮色蓝紫', desc: '渐变天幕', bg: 'linear-gradient(135deg,#7aa5f7,#b892f6)' },
  { title: '樱花树下', desc: '粉与薄绿', bg: 'linear-gradient(135deg,#ffb0c8,#8fe0cf)' },
  { title: '海边灯塔', desc: '蓝白浪线', bg: 'linear-gradient(135deg,#a8d8ea,#7aa5f7)' },
  { title: '星空山脊', desc: '深蓝与星点', bg: 'linear-gradient(135deg,#2b2d42,#7aa5f7)' },
  { title: '秋日长街', desc: '琥珀与米', bg: 'linear-gradient(135deg,#f7dc6f,#f28a5b)' },
  { title: '夜窗灯火', desc: '墨蓝与暖黄', bg: 'linear-gradient(135deg,#1d2130,#ffdf8a)' },
]

/** 统一数据形态：真实图优先；为空时回退到示例占位（含标题/描述/渐变底） */
const items = computed(() => {
  const real = (props.images || [])
    .filter((it) => it && (it.url || it.bg))
    .map((it, i) => ({
      key: `${it.url || it.bg}_${i}`,
      url: it.url || '',
      bg: it.bg || '',
      title: it.title || it.name || `图片 ${i + 1}`,
      desc: it.desc || [it.size_label, it.uploaded_at].filter(Boolean).join(' · '),
    }))
  if (real.length) return real
  return SAMPLES.map((s, i) => ({ key: `sample_${i}`, url: '', ...s }))
})

/* ---------- 入场光影：进入视口后逐格点亮 ---------- */
const rootRef = ref(null)
const shown = ref(false)
let observer = null

onMounted(() => {
  if (typeof IntersectionObserver === 'undefined') {
    shown.value = true
    return
  }
  observer = new IntersectionObserver(
    (entries) => {
      for (const e of entries) {
        if (e.isIntersecting) {
          shown.value = true
          observer.disconnect()
          observer = null
        }
      }
    },
    { threshold: 0.15 }
  )
  observer.observe(rootRef.value)
})
onBeforeUnmount(() => observer && observer.disconnect())

/* ---------- 悬停聚焦：高亮当前、其余压暗 ---------- */
const activeIndex = ref(null)

/* ---------- 灯箱 ---------- */
const lightboxIndex = ref(null)
function open(i) {
  lightboxIndex.value = i
}
</script>

<style scoped>
.lsg {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
  gap: 16px;
}

.lsg__cell {
  position: relative;
  margin: 0;
  overflow: hidden;
  border-radius: var(--bm-radius);
  background: var(--bm-card);
  border: 1px solid var(--bm-border);
  box-shadow: var(--bm-shadow-card);
  cursor: pointer;
  isolation: isolate;
  /* 入场：默认暗 + 微缩，进入视口后逐格点亮（错峰由 --i 控制） */
  opacity: 0;
  transform: translateY(14px) scale(0.97);
  filter: brightness(0.55);
  transition: opacity 0.6s var(--bm-ease) calc(var(--i) * 80ms),
    transform 0.6s var(--bm-ease-bounce) calc(var(--i) * 80ms),
    filter 0.6s var(--bm-ease) calc(var(--i) * 80ms);
}

.lsg.is-in .lsg__cell {
  opacity: 1;
  transform: none;
  filter: brightness(1);
}

/* 聚焦态：非当前格压暗、轻微缩小，形成光影对比 */
.lsg.is-focus .lsg__cell:not(.is-active) {
  filter: brightness(0.62) saturate(0.85);
  transform: scale(0.985);
}

.lsg__cell.is-active {
  transform: scale(1.04);
  z-index: 2;
  box-shadow: 0 18px 40px var(--bm-shadow-color);
}

.lsg__cell.is-active .lsg__img,
.lsg__cell.is-active .lsg__ph {
  transform: scale(1.06);
  filter: brightness(1.05) saturate(1.06);
}

/* 媒体容器 */
.lsg__media {
  position: relative;
  width: 100%;
  aspect-ratio: 4 / 3;
  overflow: hidden;
}

.lsg__img,
.lsg__ph {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
  transition: transform 0.5s var(--bm-ease), filter 0.4s var(--bm-ease);
}

.lsg__ph {
  display: flex;
  align-items: center;
  justify-content: center;
  color: rgba(255, 255, 255, 0.92);
}

.lsg__ph-title {
  font-size: 14px;
  font-weight: 600;
  letter-spacing: 1px;
  text-shadow: 0 1px 6px rgba(0, 0, 0, 0.25);
}

/* 底部光影遮罩 */
.lsg__mask {
  position: absolute;
  inset: 0;
  background: linear-gradient(
    to top,
    rgba(18, 16, 30, 0.6) 0%,
    rgba(18, 16, 30, 0.12) 38%,
    transparent 62%
  );
  opacity: 0.8;
  transition: opacity 0.35s var(--bm-ease);
  pointer-events: none;
}

.lsg__cell.is-active .lsg__mask {
  opacity: 1;
}

/* 掠光 */
.lsg__shine {
  position: absolute;
  top: -60%;
  left: -80%;
  width: 55%;
  height: 220%;
  background: linear-gradient(
    100deg,
    transparent 0%,
    rgba(255, 255, 255, 0.42) 50%,
    transparent 100%
  );
  transform: rotate(18deg);
  opacity: 0;
  pointer-events: none;
  transition: opacity 0.3s var(--bm-ease);
}

.lsg__cell.is-active .lsg__shine {
  opacity: 1;
  animation: lsg-shine 0.85s var(--bm-ease);
}

@keyframes lsg-shine {
  from { left: -80%; }
  to { left: 130%; }
}

/* 文字 */
.lsg__cap {
  position: absolute;
  left: 14px;
  right: 14px;
  bottom: 12px;
  display: flex;
  flex-direction: column;
  gap: 2px;
  color: #fff;
  text-shadow: 0 1px 6px rgba(0, 0, 0, 0.35);
  transform: translateY(6px);
  opacity: 0.92;
  transition: transform 0.35s var(--bm-ease), opacity 0.35s var(--bm-ease);
  pointer-events: none;
}

.lsg__cell.is-active .lsg__cap {
  transform: translateY(0);
  opacity: 1;
}

.lsg__title {
  font-size: 13.5px;
  font-weight: 600;
  overflow: hidden;
  white-space: nowrap;
  text-overflow: ellipsis;
}

.lsg__desc {
  font-size: 11.5px;
  opacity: 0.85;
}

.lsg__empty {
  grid-column: 1 / -1;
  text-align: center;
  padding: 60px 0;
  color: var(--bm-text-mute);
  font-size: 13px;
}

/* 响应式：移动端两列 */
@media (max-width: 520px) {
  .lsg {
    grid-template-columns: repeat(2, 1fr);
    gap: 12px;
  }
}

/* 降低动效 */
@media (prefers-reduced-motion: reduce) {
  .lsg__cell,
  .lsg__img,
  .lsg__ph,
  .lsg__mask,
  .lsg__shine,
  .lsg__cap {
    transition: none;
    animation: none;
  }
  .lsg__cell {
    opacity: 1;
    transform: none;
    filter: none;
  }
}
</style>
