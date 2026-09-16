<template>
  <section class="bm-module gallery-wall">
    <header class="bm-module__head">
      <h3 class="bm-module__title"><i class="bm-module__dot"></i>{{ title }}</h3>
      <span v-if="subtitle" class="bm-module__sub">{{ subtitle }}</span>
    </header>

    <div class="wall" :class="{ 'wall--empty': !tiles.length }">
      <figure
        v-for="(img, i) in tiles"
        :key="img.key"
        class="cell"
        :class="{ 'cell--tall': i === tallIndex, 'cell--ph': img.placeholder }"
        @click="open(img, i)"
      >
        <img
          v-if="!img.placeholder"
          :src="img.src"
          :alt="img.title || '相册图片'"
          class="cell__img"
          loading="lazy"
          decoding="async"
        />
        <div v-else class="cell__ph">
          <span>{{ img.title || '待补充' }}</span>
        </div>

        <!-- 光影遮罩：默认底部渐隐，悬停时提亮并上移 -->
        <span class="cell__mask"></span>
        <!-- 掠光：悬停时一道光斜扫而过 -->
        <span class="cell__shine"></span>

        <figcaption class="cell__cap">
          <span class="cell__title">{{ img.title || '未命名' }}</span>
          <span v-if="img.placeholder" class="cell__hint">图片位</span>
        </figcaption>
      </figure>
    </div>

    <!-- 轻量放大预览（不依赖第三方组件） -->
    <Teleport to="body">
      <div v-if="preview.url" class="lw-preview" @click="close">
        <img :src="preview.url" :alt="preview.title || '预览'" />
        <span class="lw-preview__cap">{{ preview.title }}</span>
        <button class="lw-preview__close" type="button" aria-label="关闭" @click.stop="close">×</button>
      </div>
    </Teleport>
  </section>
</template>

<script setup>
import { computed, onBeforeUnmount, ref, watch } from 'vue'

const props = defineProps({
  /** 图片数组：{ src, title }；不足 GRID_COUNT 时自动用占位格补齐 */
  images: { type: Array, default: () => [] },
  /** 竖向跨两行的格子下标 */
  tallIndex: { type: Number, default: 0 },
  title: { type: String, default: '光影相册' },
  subtitle: { type: String, default: '' },
})

const GRID_COUNT = 5

const tiles = computed(() => {
  const list = (props.images || [])
    .filter((it) => it && it.src)
    .slice(0, GRID_COUNT)
    .map((it, i) => ({ ...it, key: `${it.src}_${i}`, placeholder: false }))
  // 不足 5 张时用占位格补齐，保证版式稳定
  while (list.length < GRID_COUNT) {
    list.push({ key: `ph_${list.length}`, src: '', title: '待补充', placeholder: true })
  }
  return list
})

const preview = ref({ url: '', title: '' })

function open(img, i) {
  if (img.placeholder) return
  preview.value = { url: img.src, title: img.title || `图片 ${i + 1}` }
  document.body.style.overflow = 'hidden'
}
function close() {
  preview.value = { url: '', title: '' }
  document.body.style.overflow = ''
}
function onKey(e) {
  if (e.key === 'Escape') close()
}
watch(
  () => preview.value.url,
  (v) => {
    if (v) window.addEventListener('keydown', onKey)
    else window.removeEventListener('keydown', onKey)
  }
)
onBeforeUnmount(() => {
  window.removeEventListener('keydown', onKey)
  document.body.style.overflow = ''
})
</script>

<style scoped>
/* 版式：桌面 3 列 2 行，首格竖向跨两行；比例裁切，不变形 */
.wall {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  grid-auto-rows: 1fr;
  gap: var(--bm-module-gap);
  aspect-ratio: 3 / 2;
}

.cell {
  position: relative;
  margin: 0;
  overflow: hidden;
  border-radius: var(--bm-module-radius);
  background: var(--bm-primary-soft-2);
  box-shadow: var(--bm-shadow-card);
  cursor: pointer;
  isolation: isolate;
}

.cell--tall {
  grid-row: span 2;
}

.cell__img {
  width: 100%;
  height: 100%;
  object-fit: cover; /* 按比例裁切填充，不变形 */
  display: block;
  transition: transform 0.55s var(--bm-ease), filter 0.4s var(--bm-ease);
}

.cell__ph {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--bm-gradient-soft);
  color: var(--bm-text-mute);
  font-size: 12.5px;
  letter-spacing: 1px;
}

/* 光影遮罩 */
.cell__mask {
  position: absolute;
  inset: 0;
  background: linear-gradient(
    to top,
    rgba(20, 18, 32, 0.55) 0%,
    rgba(20, 18, 32, 0.12) 38%,
    transparent 62%
  );
  opacity: 0.75;
  transition: opacity 0.35s var(--bm-ease);
  pointer-events: none;
}

/* 掠光：默认移出视野，悬停斜扫 */
.cell__shine {
  position: absolute;
  top: -60%;
  left: -80%;
  width: 60%;
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

.cell:hover .cell__img {
  transform: scale(1.07);
  filter: saturate(1.08) brightness(1.03);
}

.cell:hover .cell__mask {
  opacity: 1;
}

.cell:hover .cell__shine {
  opacity: 1;
  animation: wall-shine 0.85s var(--bm-ease);
}

@keyframes wall-shine {
  from { left: -80%; }
  to { left: 130%; }
}

.cell__cap {
  position: absolute;
  left: 12px;
  right: 12px;
  bottom: 10px;
  display: flex;
  align-items: baseline;
  gap: 8px;
  color: #fff;
  font-size: 12.5px;
  text-shadow: 0 1px 6px rgba(0, 0, 0, 0.35);
  transform: translateY(6px);
  opacity: 0.9;
  transition: transform 0.35s var(--bm-ease), opacity 0.35s var(--bm-ease);
  pointer-events: none;
}

.cell:hover .cell__cap {
  transform: translateY(0);
  opacity: 1;
}

.cell__title {
  overflow: hidden;
  white-space: nowrap;
  text-overflow: ellipsis;
}

.cell__hint {
  flex: none;
  font-size: 11px;
  opacity: 0.8;
}

/* 平板：两列 */
@media (max-width: 900px) {
  .wall {
    grid-template-columns: repeat(2, 1fr);
    grid-auto-rows: 1fr;
    aspect-ratio: auto;
  }
  .cell {
    aspect-ratio: 1 / 1;
  }
  .cell--tall {
    grid-row: span 2;
    aspect-ratio: 1 / 2;
  }
}

/* 手机：单列，取消跨行，统一 4:3 */
@media (max-width: 520px) {
  .wall {
    grid-template-columns: 1fr;
  }
  .cell,
  .cell--tall {
    grid-row: auto;
    aspect-ratio: 4 / 3;
  }
}

/* 降低动效偏好 */
@media (prefers-reduced-motion: reduce) {
  .cell__img,
  .cell__mask,
  .cell__cap,
  .cell__shine {
    transition: none;
    animation: none;
  }
  .cell:hover .cell__img {
    transform: none;
  }
}

/* 预览层 */
.lw-preview {
  position: fixed;
  inset: 0;
  z-index: 3000;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  background: rgba(15, 14, 24, 0.82);
  padding: 24px;
  cursor: zoom-out;
}

.lw-preview img {
  max-width: min(92vw, 1000px);
  max-height: 78vh;
  border-radius: var(--bm-radius-sm);
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.45);
}

.lw-preview__cap {
  color: rgba(255, 255, 255, 0.86);
  font-size: 13px;
}

.lw-preview__close {
  position: absolute;
  top: 18px;
  right: 22px;
  width: 38px;
  height: 38px;
  border: none;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.16);
  color: #fff;
  font-size: 22px;
  line-height: 1;
  cursor: pointer;
}

.lw-preview__close:hover {
  background: rgba(255, 255, 255, 0.28);
}
</style>
