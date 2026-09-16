<template>
  <div class="front">
    <BmBackdrop />
    <SnowFall />
    <!-- 顶部导航 -->
    <header class="header" :class="{ scrolled }">
      <div class="bm-container header-inner">
        <router-link to="/" class="brand">
          <span class="name">BlueMoonの博客</span>
        </router-link>

        <nav class="nav" aria-label="主导航">
          <router-link to="/">首页</router-link>
          <router-link to="/archives">归档</router-link>
          <router-link to="/categories">分类</router-link>
          <router-link to="/images">图片</router-link>
          <router-link to="/about">关于我</router-link>
        </nav>

        <div class="actions">
          <el-input
            v-model="keyword"
            placeholder="搜索文章…"
            size="small"
            clearable
            class="search"
            aria-label="搜索文章"
            @keyup.enter="doSearch"
            @clear="doSearch"
          >
            <template #prefix><el-icon><Search /></el-icon></template>
          </el-input>
          <el-button
            class="menu-btn"
            circle
            size="small"
            :aria-label="mobileMenu ? '关闭菜单' : '打开菜单'"
            :aria-expanded="mobileMenu"
            aria-controls="mobile-nav"
            @click="mobileMenu = !mobileMenu"
          >
            <el-icon><component :is="mobileMenu ? Close : Menu" /></el-icon>
          </el-button>
        </div>
      </div>

      <!-- 移动端展开菜单 -->
      <transition name="slide-down">
        <nav v-show="mobileMenu" id="mobile-nav" class="mobile-nav" aria-label="移动端导航">
          <router-link to="/" @click="mobileMenu = false">首页</router-link>
          <router-link to="/archives" @click="mobileMenu = false">归档</router-link>
          <router-link to="/categories" @click="mobileMenu = false">分类</router-link>
          <router-link to="/images" @click="mobileMenu = false">图片</router-link>
          <router-link to="/about" @click="mobileMenu = false">关于我</router-link>
        </nav>
      </transition>
    </header>

    <!-- 内容区 -->
    <main class="main">
      <router-view v-slot="{ Component }">
        <transition name="fade" mode="out-in">
          <component :is="Component" />
        </transition>
      </router-view>
    </main>

    <!-- 页脚 -->
    <footer class="footer">
      <div class="bm-container">
        <p class="copy">
          © {{ year }} {{ site.title || 'Bluemoon' }} · {{ site.description || '' }}
        </p>
        <p class="meta">
          <span>Powered by Vue 3 + FastAPI + MySQL + Redis</span>
          <span v-if="site.icp">{{ site.icp }}</span>
          <span>共 {{ site.total_views || 0 }} 次阅读</span>
        </p>
      </div>
    </footer>

    <el-backtop :right="28" :bottom="28" />

    <!-- 右侧拉灯控件：日夜模式切换 -->
    <ThemeSwitch />
  </div>
</template>

<script setup>
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { Close, Menu } from '@element-plus/icons-vue'
import BmBackdrop from '@/components/BmBackdrop.vue'
import SnowFall from '@/components/SnowFall.vue'
import ThemeSwitch from '@/components/ThemeSwitch.vue'
import { useSiteStore } from '@/stores/site'

const router = useRouter()
const siteStore = useSiteStore()
const site = computed(() => siteStore.site || {})
const year = new Date().getFullYear()

const keyword = ref('')
const scrolled = ref(false)
const mobileMenu = ref(false)

const onScroll = () => {
  scrolled.value = window.scrollY > 10
}

onMounted(() => {
  siteStore.load()
  onScroll()
  window.addEventListener('scroll', onScroll, { passive: true })
})
onUnmounted(() => window.removeEventListener('scroll', onScroll))

const doSearch = () => {
  router.push({ name: 'search', query: { q: keyword.value || '' } })
}
</script>

<style scoped>
.front {
  position: relative;
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

/* 装饰背景已抽到 <BmBackdrop /> 组件，全站复用 */

.main,
.footer {
  position: relative;
  z-index: 1;
}

/* ========== 顶部导航：玻璃拟态 + 边缘羽化 ========== */
.header {
  position: sticky;
  top: 0;
  z-index: 100;
  background: linear-gradient(
    to bottom,
    rgba(255, 255, 255, 0.62) 0%,
    rgba(255, 255, 255, 0.42) 70%,
    rgba(255, 255, 255, 0.12) 100%
  );
  backdrop-filter: blur(18px) saturate(160%);
  -webkit-backdrop-filter: blur(18px) saturate(160%);
  border-bottom: none;
  box-shadow: none;
  transition: background 0.3s var(--bm-ease), box-shadow 0.3s var(--bm-ease);
}

/* 滚动后顶部增加一道极细渐变描边，且左右两端羽化消失 */
.header.scrolled {
  box-shadow: 0 4px 18px rgba(44, 47, 58, 0.05);
}

.header.scrolled::after {
  content: '';
  position: absolute;
  left: 8%;
  right: 8%;
  bottom: 0;
  height: 1.5px;
  background: var(--bm-gradient);
  border-radius: 2px;
  opacity: 0.55;
  mask-image: linear-gradient(to right, transparent 0%, #000 50%, transparent 100%);
  -webkit-mask-image: linear-gradient(to right, transparent 0%, #000 50%, transparent 100%);
}

.header-inner {
  display: flex;
  align-items: center;
  gap: 24px;
  height: 64px;
}

.brand {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 18px;
  font-weight: 700;
  flex-shrink: 0;
  transition: transform 0.3s var(--bm-ease-bounce);
}

.brand:hover {
  transform: scale(1.02);
}

/* 去除小图标后的站名样式：直接呈现文字 */
.brand .name {
  font-size: 18px;
  font-weight: 800;
  letter-spacing: 1.2px;
  background: var(--bm-gradient);
  -webkit-background-clip: text;
  background-clip: text;
  -webkit-text-fill-color: transparent;
  color: transparent;
  filter: drop-shadow(0 2px 6px var(--bm-shadow-color));
  transition: filter 0.3s var(--bm-ease);
}

.brand:hover .name {
  filter: drop-shadow(0 4px 10px var(--bm-shadow-color));
}

.nav {
  display: flex;
  gap: 6px;
  font-size: 15px;
}

/* 胶囊导航：悬停淡入底色，选中渐变高亮 */
.nav a {
  position: relative;
  padding: 7px 16px;
  border-radius: 999px;
  color: var(--bm-text);
  font-weight: 600;
  transition: all 0.28s var(--bm-ease-bounce);
}

.nav a:hover {
  background: var(--bm-primary-soft);
  color: var(--bm-primary-2);
  transform: translateY(-2px);
}

.nav a.router-link-exact-active {
  color: #fff;
  background: var(--bm-gradient);
  font-weight: 700;
  box-shadow: 0 8px 18px var(--bm-shadow-color);
}

.actions {
  margin-left: auto;
  display: flex;
  align-items: center;
  gap: 10px;
}

.search {
  width: 190px;
}

.search :deep(.el-input__wrapper) {
  border-radius: 999px;
  background: #f4f6fb;
  box-shadow: none;
}

.search :deep(.el-input__wrapper.is-focus) {
  box-shadow: 0 0 0 1px var(--bm-primary) inset;
  background: #fff;
}

.main {
  /* 首页（.home）使用负 margin 把 Hero 上提到 header 下方，所以这里只需要保留底部呼吸 */
  flex: 1;
  padding: 0 0 44px;
}

/* ========== 页脚：玻璃拟态 + 边缘羽化，与背景无缝融合 ========== */
.footer {
  padding: 28px 0;
  background: linear-gradient(
    to bottom,
    rgba(255, 255, 255, 0) 0%,
    rgba(255, 255, 255, 0.5) 35%,
    rgba(255, 255, 255, 0.7) 100%
  );
  backdrop-filter: blur(14px) saturate(150%);
  -webkit-backdrop-filter: blur(14px) saturate(150%);
  text-align: center;
  font-size: 13px;
  color: var(--bm-text-sub);
  position: relative;
  border-top: none;
  box-shadow: 0 -8px 24px -16px rgba(44, 47, 58, 0.18);
}

/* 页脚顶部渐变线：左右两端羽化透明，仅中间可见一段 */
.footer::before {
  content: '';
  position: absolute;
  top: 0;
  left: 15%;
  right: 15%;
  height: 1.5px;
  background: var(--bm-gradient);
  border-radius: 2px;
  opacity: 0.45;
  mask-image: linear-gradient(to right, transparent 0%, #000 50%, transparent 100%);
  -webkit-mask-image: linear-gradient(to right, transparent 0%, #000 50%, transparent 100%);
}

.footer .copy {
  margin: 0 0 8px;
  color: var(--bm-text);
  font-weight: 600;
}

.footer .meta {
  display: flex;
  justify-content: center;
  flex-wrap: wrap;
  gap: 16px;
  margin: 0;
  font-size: 12.5px;
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.18s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

/* ---------- 深色模式适配（本布局作用域） ---------- */
html.dark .header {
  background: linear-gradient(
    to bottom,
    rgba(20, 18, 31, 0.62) 0%,
    rgba(20, 18, 31, 0.42) 70%,
    rgba(20, 18, 31, 0.12) 100%
  );
}

html.dark .header.scrolled {
  box-shadow: 0 4px 18px rgba(0, 0, 0, 0.32);
}

html.dark .search :deep(.el-input__wrapper) {
  background: #23262f;
}

html.dark .search :deep(.el-input__wrapper.is-focus) {
  background: #1c1f27;
}

html.dark .footer {
  background: #14161d;
}

/* 移动端汉堡菜单按钮（仅移动端显示） */
.menu-btn {
  display: none;
}

.mobile-nav {
  display: none;
}

/* 移动端展开菜单过渡动画 */
.slide-down-enter-active,
.slide-down-leave-active {
  transition: opacity 0.25s var(--bm-ease), transform 0.25s var(--bm-ease);
}

.slide-down-enter-from,
.slide-down-leave-to {
  opacity: 0;
  transform: translateY(-10px);
}

@media (max-width: 860px) {
  .nav {
    display: none;
  }
  .search {
    width: 120px;
  }
  .menu-btn {
    display: inline-flex;
  }
  .mobile-nav {
    display: flex;
    flex-direction: column;
    gap: 2px;
    padding: 10px 16px 14px;
    background: linear-gradient(to bottom, rgba(255, 255, 255, 0.86), rgba(255, 255, 255, 0.62));
    backdrop-filter: blur(18px) saturate(160%);
    -webkit-backdrop-filter: blur(18px) saturate(160%);
    border-bottom: none;
  }
  .mobile-nav a {
    padding: 10px 14px;
    border-radius: 999px;
    font-size: 15px;
    font-weight: 600;
    color: var(--bm-text);
    transition: all 0.2s var(--bm-ease);
  }
  .mobile-nav a:hover,
  .mobile-nav a.router-link-exact-active {
    background: var(--bm-gradient);
    color: #fff;
  }
}

html.dark .mobile-nav {
  background: linear-gradient(to bottom, rgba(20, 18, 31, 0.86), rgba(20, 18, 31, 0.62));
}
</style>
