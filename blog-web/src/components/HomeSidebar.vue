<template>
  <!-- 首页左侧栏：博主信息 + 分类导航 -->
  <aside class="sidebar">
    <el-avatar :size="84" :src="avatar || ''" class="avatar">
      {{ avatarText }}
    </el-avatar>
    <div class="author-name">{{ title }}</div>
    <div class="author-bio">{{ bio }}</div>

    <div class="divider"></div>

    <div class="nav-title">导航</div>
    <ul class="nav-menu">
      <li :class="{ active: cat === 'all' }" @click="emit('select-cat', 'all')">
        <span class="dot"></span>全部文章
      </li>
      <li
        v-for="c in categories"
        :key="c.id"
        :class="{ active: cat === c.id }"
        @click="emit('select-cat', c.id)"
      >
        <span class="dot"></span>{{ c.name }}
        <span class="cnt">{{ c.post_count }}</span>
      </li>
    </ul>
  </aside>
</template>

<script setup>
import { computed } from 'vue'

/** 侧边栏组件：纯展示，选中状态由父组件传入，点击通过事件上抛 */
const props = defineProps({
  site: { type: Object, default: () => ({}) },
  avatar: { type: String, default: '' },
  avatarText: { type: String, default: 'B' },
  categories: { type: Array, default: () => [] },
  cat: { type: [String, Number], default: 'all' },
})

const emit = defineEmits(['select-cat'])

const title = computed(() => props.site.title || 'BlueMoonの博客')
const bio = computed(
  () => props.site.description || '一个喜欢折腾前端与 Python 的技术人'
)
</script>

<style scoped>
.sidebar {
  flex: 0 0 20%;
  max-width: 20%;
  /* 顶部透明羽化，与 Hero 衔接处不出现硬边 */
  background: linear-gradient(
    to bottom,
    transparent 0%,
    rgba(255, 255, 255, 0.62) 56px,
    var(--bm-card) 120px
  );
  border: 1px solid var(--bm-border);
  border-radius: var(--bm-radius);
  padding: 28px 22px;
  position: sticky;
  top: 84px;
  box-shadow: var(--bm-shadow-card);
}

.avatar {
  display: block !important;
  margin: 0 auto 16px;
  background: var(--bm-gradient) !important;
  color: #fff !important;
  font-size: 34px !important;
  font-weight: 800;
  letter-spacing: 1px;
  box-shadow: 0 10px 24px var(--bm-shadow-color);
  transition: transform 0.4s var(--bm-ease-bounce);
}

.avatar:hover {
  transform: scale(1.06) rotate(-5deg);
}

.author-name {
  text-align: center;
  font-size: 22px;
  font-weight: 800;
  letter-spacing: 0.6px;
}

.author-bio {
  text-align: center;
  color: var(--bm-text-sub);
  font-size: 13.5px;
  margin-top: 6px;
}

.divider {
  height: 1px;
  background: var(--bm-border);
  margin: 22px 0;
}

.nav-title,
.cloud-title {
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 1.5px;
  color: var(--bm-text-mute);
  text-transform: uppercase;
  margin-bottom: 12px;
}

.nav-menu {
  list-style: none;
  padding: 0;
  margin: 0;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.nav-menu li {
  padding: 10px 14px;
  border-radius: 999px;
  cursor: pointer;
  font-size: 14.5px;
  color: var(--bm-text-sub);
  transition: all 0.25s var(--bm-ease);
  display: flex;
  align-items: center;
  gap: 10px;
  user-select: none;
}

.nav-menu li .dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: #d9d4ee;
  transition: all 0.25s var(--bm-ease);
  flex-shrink: 0;
}

.nav-menu li .cnt {
  margin-left: auto;
  font-size: 12px;
  color: var(--bm-text-mute);
}

.nav-menu li:hover {
  background: var(--bm-primary-soft);
  color: var(--bm-text);
  transform: translateX(3px);
}

.nav-menu li.active {
  background: var(--bm-gradient);
  color: #fff;
  font-weight: 700;
  box-shadow: 0 8px 18px var(--bm-shadow-color);
}

.nav-menu li.active .dot {
  background: #fff;
  transform: scale(1.2);
}

.nav-menu li.active .cnt {
  color: rgba(255, 255, 255, 0.85);
}

html.dark .sidebar {
  background: linear-gradient(
    to bottom,
    transparent 0%,
    rgba(20, 18, 31, 0.62) 56px,
    var(--bm-card) 120px
  );
}

@media (max-width: 900px) {
  .sidebar {
    max-width: 100%;
    width: 100%;
    position: static;
  }
}
</style>
