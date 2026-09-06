<template>
  <!-- 页头：渐变图标 pill + 标题 + 右侧计数 -->
  <h2 class="page-header">
    <span class="icon-pill">
      <el-icon><component :is="icon" /></el-icon>
    </span>
    <span class="txt">{{ title }}</span>
    <span v-if="count !== null && count !== undefined" class="count">{{ count }}</span>
    <span class="sparkle" aria-hidden="true"></span>
  </h2>
</template>

<script setup>
/**
 * 统一页头组件
 * 原 Archive / Categories / Tags / Images 各写了一份 .bm-page-title 结构，此处收敛为一处。
 * @prop {Object|String} icon  Element Plus 图标组件（必填）
 * @prop {String}       title  标题文案
 * @prop {String|Number} count 右侧计数（可选），传字符串可直接带上单位，如 "共 12 篇"
 */
defineProps({
  icon: { type: [Object, String], required: true },
  title: { type: String, required: true },
  count: { type: [String, Number], default: null },
})
</script>

<style scoped>
.page-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin: 0 0 22px;
  padding-bottom: 16px;
  border-bottom: 1px solid var(--bm-border);
  font-size: 21px;
  font-weight: 800;
  letter-spacing: 0.5px;
  position: relative;
}

.icon-pill {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 38px;
  height: 38px;
  border-radius: 13px;
  background: var(--bm-gradient);
  color: #fff;
  font-size: 18px;
  box-shadow: 0 8px 18px var(--bm-shadow-color);
  transition: transform var(--bm-ease-bounce);
}

.page-header:hover .icon-pill {
  transform: rotate(-8deg) scale(1.08);
}

.txt {
  background: var(--bm-gradient);
  -webkit-background-clip: text;
  background-clip: text;
  -webkit-text-fill-color: transparent;
  color: transparent;
}

.count {
  margin-left: auto;
  font-size: 13px;
  font-weight: 500;
  color: var(--bm-text-sub);
  background: var(--bm-primary-soft);
  padding: 3px 12px;
  border-radius: 999px;
}

/* 装饰性小星点 */
.sparkle {
  position: absolute;
  left: 0;
  bottom: -1px;
  width: 54px;
  height: 2px;
  border-radius: 2px;
  background: var(--bm-gradient);
}

@media (max-width: 640px) {
  .page-header {
    font-size: 18px;
  }
  .icon-pill {
    width: 32px;
    height: 32px;
    font-size: 15px;
  }
}
</style>
