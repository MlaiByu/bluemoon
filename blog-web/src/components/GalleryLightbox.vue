<template>
  <Teleport to="body">
    <Transition name="glb-fade">
      <div
        v-if="modelValue !== null && modelValue >= 0"
        class="glb"
        role="dialog"
        aria-modal="true"
        aria-label="图片预览"
        @click.self="close"
      >
        <button class="glb__btn glb__close" type="button" aria-label="关闭" @click="close">×</button>

        <button
          v-if="total > 1"
          class="glb__btn glb__nav glb__nav--prev"
          type="button"
          aria-label="上一张"
          @click="step(-1)"
        >‹</button>

        <div class="glb__stage" @click.self="close">
          <Transition name="glb-xfade" mode="out-in">
            <figure :key="modelValue" class="glb__fig">
              <img
                v-if="current.url"
                :src="current.url"
                :alt="current.title || '图片预览'"
                class="glb__img"
              />
              <div
                v-else
                class="glb__ph"
                :style="{ background: current.bg }"
              >
                <span>{{ current.title || '占位' }}</span>
              </div>

              <figcaption class="glb__cap">
                <span class="glb__cap-title">{{ current.title || '未命名' }}</span>
                <span v-if="current.desc" class="glb__cap-desc">{{ current.desc }}</span>
              </figcaption>
            </figure>
          </Transition>
        </div>

        <button
          v-if="total > 1"
          class="glb__btn glb__nav glb__nav--next"
          type="button"
          aria-label="下一张"
          @click="step(1)"
        >›</button>

        <div v-if="total > 1" class="glb__counter">{{ modelValue + 1 }} / {{ total }}</div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup>
import { computed, onBeforeUnmount, watch } from 'vue'

const props = defineProps({
  /** 图片数组，元素形如 { url, title, desc, bg }；url 为空时按 bg 渐变占位 */
  images: { type: Array, required: true },
})

/** 当前索引（v-model）；null 或 -1 表示关闭 */
const modelValue = defineModel({ type: Number, default: null })

const total = computed(() => props.images.length)
const current = computed(() => props.images[modelValue.value] || { url: '', title: '', desc: '', bg: '' })

function close() {
  modelValue.value = null
}
function step(delta) {
  if (total.value <= 1) return
  modelValue.value = (modelValue.value + delta + total.value) % total.value
}

function onKey(e) {
  if (modelValue.value === null) return
  if (e.key === 'Escape') close()
  else if (e.key === 'ArrowLeft') step(-1)
  else if (e.key === 'ArrowRight') step(1)
}

watch(
  () => modelValue.value,
  (v) => {
    if (v !== null && v >= 0) {
      window.addEventListener('keydown', onKey)
      document.body.style.overflow = 'hidden'
    } else {
      window.removeEventListener('keydown', onKey)
      document.body.style.overflow = ''
    }
  }
)
onBeforeUnmount(() => {
  window.removeEventListener('keydown', onKey)
  document.body.style.overflow = ''
})
</script>

<style scoped>
.glb {
  position: fixed;
  inset: 0;
  z-index: 3000;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px;
  background: rgba(12, 11, 20, 0.86);
  backdrop-filter: blur(6px);
}

.glb__stage {
  flex: 1;
  min-width: 0;
  max-width: 1000px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.glb__fig {
  margin: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  max-width: 100%;
  max-height: 82vh;
}

.glb__img {
  max-width: min(92vw, 1000px);
  max-height: 74vh;
  border-radius: var(--bm-radius-sm);
  box-shadow: 0 24px 70px rgba(0, 0, 0, 0.55);
  object-fit: contain;
}

.glb__ph {
  width: min(80vw, 720px);
  height: 56vh;
  border-radius: var(--bm-radius-sm);
  display: flex;
  align-items: center;
  justify-content: center;
  color: rgba(255, 255, 255, 0.9);
  font-size: 14px;
  letter-spacing: 1px;
  box-shadow: 0 24px 70px rgba(0, 0, 0, 0.45);
}

.glb__cap {
  text-align: center;
  color: rgba(255, 255, 255, 0.92);
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.glb__cap-title {
  font-size: 14px;
  font-weight: 600;
}

.glb__cap-desc {
  font-size: 12px;
  opacity: 0.75;
}

.glb__btn {
  position: absolute;
  border: none;
  color: #fff;
  background: rgba(255, 255, 255, 0.14);
  cursor: pointer;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: background 0.2s var(--bm-ease), transform 0.2s var(--bm-ease);
}

.glb__btn:hover {
  background: rgba(255, 255, 255, 0.28);
}

.glb__close {
  top: 18px;
  right: 22px;
  width: 40px;
  height: 40px;
  font-size: 24px;
  line-height: 1;
}

.glb__nav {
  top: 50%;
  transform: translateY(-50%);
  width: 46px;
  height: 46px;
  font-size: 28px;
  line-height: 1;
}

.glb__nav--prev { left: 18px; }
.glb__nav--next { right: 18px; }
.glb__nav--prev:hover { transform: translateY(-50%) translateX(-2px); }
.glb__nav--next:hover { transform: translateY(-50%) translateX(2px); }

.glb__counter {
  position: absolute;
  bottom: 22px;
  left: 50%;
  transform: translateX(-50%);
  color: rgba(255, 255, 255, 0.82);
  font-size: 13px;
  font-variant-numeric: tabular-nums;
}

/* 背景淡入 */
.glb-fade-enter-active,
.glb-fade-leave-active {
  transition: opacity 0.3s var(--bm-ease);
}
.glb-fade-enter-from,
.glb-fade-leave-to {
  opacity: 0;
}

/* 图片交叉淡化 */
.glb-xfade-enter-active,
.glb-xfade-leave-active {
  transition: opacity 0.28s var(--bm-ease), transform 0.28s var(--bm-ease);
}
.glb-xfade-enter-from {
  opacity: 0;
  transform: scale(1.02);
}
.glb-xfade-leave-to {
  opacity: 0;
  transform: scale(0.99);
}

@media (prefers-reduced-motion: reduce) {
  .glb-fade-enter-active,
  .glb-fade-leave-active,
  .glb-xfade-enter-active,
  .glb-xfade-leave-active {
    transition: none;
  }
}
</style>
