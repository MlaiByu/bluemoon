<template>
  <!-- 空状态：全站统一的占位提示 -->
  <div class="empty-state">
    <div class="art" aria-hidden="true">
      <span class="ring"></span>
      <span class="emoji">{{ emoji }}</span>
    </div>
    <p class="text">{{ text }}</p>
    <p v-if="tip" class="tip">{{ tip }}</p>
    <slot />
  </div>
</template>

<script setup>
/**
 * 统一空状态组件（替换 Home / Images / SidePanel 中各自实现的一份）
 * @prop {String} emoji 装饰表情
 * @prop {String} text  主提示文案
 * @prop {String} tip   次级补充说明（可选）
 */
defineProps({
  emoji: { type: String, default: '🌙' },
  text: { type: String, default: '这里还没有内容～' },
  tip: { type: String, default: '' },
})
</script>

<style scoped>
.empty-state {
  text-align: center;
  padding: 56px 16px;
  color: var(--bm-text-sub);
}

.art {
  position: relative;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 84px;
  height: 84px;
  margin-bottom: 12px;
}

/* 装饰光环 */
.ring {
  position: absolute;
  inset: 0;
  border-radius: 50%;
  background: var(--bm-gradient-soft);
  animation: float 3.6s ease-in-out infinite;
}

.emoji {
  position: relative;
  font-size: 34px;
  filter: drop-shadow(0 4px 8px var(--bm-shadow-color));
}

.text {
  margin: 0;
  font-size: 14.5px;
  font-weight: 600;
  color: var(--bm-text-sub);
}

.tip {
  margin: 6px 0 0;
  font-size: 13px;
  color: var(--bm-text-mute);
}

@keyframes float {
  0%,
  100% {
    transform: translateY(0) scale(1);
  }
  50% {
    transform: translateY(-6px) scale(1.04);
  }
}
</style>
