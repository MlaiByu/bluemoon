<template>
  <div class="admin">
    <!-- 装饰背景 -->
    <div class="admin-deco" aria-hidden="true">
      <span class="orb orb-1"></span>
      <span class="orb orb-2"></span>
      <span class="orb orb-3"></span>
      <div class="grid-pattern"></div>
    </div>

    <!-- 侧边栏 -->
    <aside class="sidebar" :class="{ collapsed }">
      <div class="sidebar-bg" aria-hidden="true"></div>
      <div class="logo">
        <span v-show="!collapsed" class="text">BlueMoonの博客</span>
      </div>

      <div class="menu-section" v-show="!collapsed">管理台</div>

      <el-menu
        :default-active="activeMenu"
        :collapse="collapsed"
        :collapse-transition="false"
        router
        class="menu"
      >
        <el-menu-item index="/admin">
          <el-icon><DataLine /></el-icon>
          <template #title>仪表盘</template>
        </el-menu-item>
        <el-menu-item index="/admin/posts">
          <el-icon><Document /></el-icon>
          <template #title>文章管理</template>
        </el-menu-item>
        <el-menu-item index="/admin/posts/new">
          <el-icon><EditPen /></el-icon>
          <template #title>写文章</template>
        </el-menu-item>
        <el-menu-item index="/admin/categories">
          <el-icon><Folder /></el-icon>
          <template #title>分类管理</template>
        </el-menu-item>
        <el-menu-item index="/admin/images">
          <el-icon><Picture /></el-icon>
          <template #title>图片管理</template>
        </el-menu-item>

        <div v-show="!collapsed" class="menu-divider"></div>
        <div v-show="!collapsed" class="menu-section">系统</div>

        <el-menu-item index="/admin/profile">
          <el-icon><User /></el-icon>
          <template #title>站点设置</template>
        </el-menu-item>
      </el-menu>

      <!-- 侧边栏底部 -->
      <div class="sidebar-footer">
        <div v-show="!collapsed" class="version">v 1.0.0</div>
      </div>
    </aside>

    <!-- 主区域 -->
    <div class="main">
      <header class="topbar">
        <div class="topbar-bg" aria-hidden="true"></div>
        <div class="left">
          <el-button :icon="collapsed ? Expand : Fold" text @click="collapsed = !collapsed" class="collapse-btn" />
          <el-breadcrumb separator="/">
            <el-breadcrumb-item :to="{ path: '/admin' }">后台</el-breadcrumb-item>
            <el-breadcrumb-item>{{ route.meta.title }}</el-breadcrumb-item>
          </el-breadcrumb>
        </div>

        <div class="right">
          <el-tooltip content="查看前台" placement="bottom">
            <el-button :icon="View" text class="icon-btn" @click="goFront" />
          </el-tooltip>
          <div class="topbar-divider"></div>
          <el-dropdown trigger="click" @command="onCommand">
            <span class="user">
              <span class="avatar-ring">
                <el-avatar :size="32" :src="user?.avatar || ''">{{ (user?.nickname || 'A').slice(0, 1) }}</el-avatar>
              </span>
              <span class="user-info" v-show="true">
                <span class="uname">{{ user?.nickname || user?.username || '管理员' }}</span>
                <span class="urole">博主</span>
              </span>
              <el-icon class="arrow-icon"><ArrowDown /></el-icon>
            </span>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="front">查看前台</el-dropdown-item>
                <el-dropdown-item command="profile" divided>站点设置</el-dropdown-item>
                <el-dropdown-item command="logout" divided>退出登录</el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </header>

      <section class="page">
        <router-view v-slot="{ Component }">
          <transition name="page-fade" mode="out-in">
            <component :is="Component" />
          </transition>
        </router-view>
      </section>
    </div>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessageBox } from 'element-plus'
import { ArrowDown, DataLine, Document, EditPen, Expand, Fold, Folder, Picture, User, View } from '@element-plus/icons-vue'
import { useUserStore } from '@/stores/user'
import { logout as apiLogout } from '@/api'

const route = useRoute()
const router = useRouter()
const store = useUserStore()
const user = computed(() => store.user)

const collapsed = ref(false)
const activeMenu = computed(() => {
  if (route.path.startsWith('/admin/posts/new')) return '/admin/posts/new'
  if (route.path.startsWith('/admin/posts')) return '/admin/posts'
  return route.path
})

const goFront = () => router.push('/')

async function onCommand(cmd) {
  if (cmd === 'front') return goFront()
  if (cmd === 'profile') return router.push('/admin/profile')
  if (cmd === 'logout') {
    try {
      await ElMessageBox.confirm('确定要退出登录吗？', '提示', { type: 'warning' })
    } catch {
      return
    }
    try {
      await apiLogout()
    } catch {
      /* 忽略，仍本地登出 */
    }
    store.clear()
    router.push('/admin/login')
  }
}
</script>

<style scoped>
.admin {
  display: flex;
  min-height: 100vh;
  background: #f7f5fc;
  position: relative;
}

/* ============================ 装饰背景 ============================ */
.admin-deco {
  position: fixed;
  inset: 0;
  z-index: 0;
  pointer-events: none;
  overflow: hidden;
}

.orb {
  position: absolute;
  border-radius: 50%;
  filter: blur(90px);
  opacity: 0.4;
}

.orb-1 {
  width: 520px;
  height: 520px;
  top: -200px;
  right: -100px;
  background: radial-gradient(circle, var(--bm-glow-blue), transparent 70%);
  animation: drift-a 22s ease-in-out infinite;
}

.orb-2 {
  width: 420px;
  height: 420px;
  bottom: -120px;
  left: 300px;
  background: radial-gradient(circle, var(--bm-glow-pink), transparent 70%);
  animation: drift-b 26s ease-in-out infinite;
}

.orb-3 {
  width: 300px;
  height: 300px;
  top: 40%;
  right: 20%;
  background: radial-gradient(circle, var(--bm-glow-mint), transparent 70%);
  animation: drift-c 30s ease-in-out infinite;
  opacity: 0.25;
}

@keyframes drift-a {
  0%, 100% { transform: translate(0, 0); }
  50% { transform: translate(-40px, 30px); }
}

@keyframes drift-b {
  0%, 100% { transform: translate(0, 0); }
  50% { transform: translate(35px, -25px); }
}

@keyframes drift-c {
  0%, 100% { transform: translate(0, 0) scale(1); }
  33% { transform: translate(20px, -30px) scale(1.1); }
  66% { transform: translate(-25px, 15px) scale(0.95); }
}

/* 点阵网格背景 */
.grid-pattern {
  position: absolute;
  inset: 0;
  background-image: radial-gradient(circle, rgba(184, 146, 246, 0.12) 1px, transparent 1px);
  background-size: 24px 24px;
  mask-image: radial-gradient(ellipse at center, black 30%, transparent 80%);
  -webkit-mask-image: radial-gradient(ellipse at center, black 30%, transparent 80%);
  opacity: 0.6;
}

/* ============================ 侧边栏 ============================ */
.sidebar {
  width: 240px;
  flex-shrink: 0;
  position: relative;
  z-index: 10;
  display: flex;
  flex-direction: column;
  transition: width 0.28s var(--bm-ease);
}

.sidebar.collapsed {
  width: 72px;
}

.sidebar-bg {
  position: absolute;
  inset: 0;
  background: rgba(255, 255, 255, 0.85);
  backdrop-filter: blur(20px) saturate(180%);
  -webkit-backdrop-filter: blur(20px) saturate(180%);
  border-right: 1px solid var(--bm-border);
  box-shadow: 4px 0 24px rgba(122, 126, 247, 0.06);
}

/* Logo 区域（去图标后） */
.logo {
  display: flex;
  align-items: center;
  gap: 12px;
  height: 68px;
  padding: 0 22px;
  font-size: 18px;
  font-weight: 800;
  border-bottom: 1px solid var(--bm-border);
  overflow: hidden;
  white-space: nowrap;
  position: relative;
  z-index: 1;
}

.logo .text {
  background: var(--bm-gradient);
  -webkit-background-clip: text;
  background-clip: text;
  -webkit-text-fill-color: transparent;
  letter-spacing: 1.2px;
  font-weight: 800;
  filter: drop-shadow(0 2px 6px var(--bm-shadow-color));
}

/* 菜单分组标题 */
.menu-section {
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 2px;
  color: var(--bm-text-mute);
  text-transform: uppercase;
  padding: 16px 22px 8px;
  position: relative;
  z-index: 1;
}

.menu-divider {
  height: 1px;
  background: linear-gradient(to right, transparent, var(--bm-border), transparent);
  margin: 12px 16px;
  position: relative;
  z-index: 1;
}

/* 菜单 */
.menu {
  flex: 1;
  border-right: none;
  padding: 8px 14px 0;
  background: transparent;
  position: relative;
  z-index: 1;
}

.menu :deep(.el-menu-item) {
  height: 48px;
  line-height: 48px;
  border-radius: 12px;
  margin-bottom: 4px;
  transition: all 0.25s var(--bm-ease);
  font-weight: 500;
  color: var(--bm-text-sub);
}

.menu :deep(.el-menu-item:hover) {
  background: var(--bm-primary-soft);
  color: var(--bm-primary-2);
  transform: translateX(4px);
}

.menu :deep(.el-menu-item.is-active) {
  background: var(--bm-gradient);
  color: #fff;
  font-weight: 600;
  box-shadow: 0 10px 22px var(--bm-shadow-color);
  transform: translateX(0);
  position: relative;
}

.menu :deep(.el-menu-item.is-active::before) {
  content: '';
  position: absolute;
  left: -14px;
  top: 50%;
  transform: translateY(-50%);
  width: 4px;
  height: 22px;
  background: var(--bm-gradient);
  border-radius: 0 4px 4px 0;
}

.menu :deep(.el-menu-item.is-active .el-icon) {
  color: #fff;
}

.menu :deep(.el-icon) {
  font-size: 18px;
}

/* 侧边栏底部 */
.sidebar-footer {
  padding: 16px 22px;
  border-top: 1px solid var(--bm-border);
  position: relative;
  z-index: 1;
}

.version {
  font-size: 12px;
  color: var(--bm-text-mute);
  text-align: center;
  letter-spacing: 0.5px;
}

/* ============================ 主区域 ============================ */
.main {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  position: relative;
  z-index: 1;
}

/* ============================ 顶栏 ============================ */
.topbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 68px;
  padding: 0 24px;
  position: relative;
  z-index: 5;
}

.topbar-bg {
  position: absolute;
  inset: 0;
  background: rgba(255, 255, 255, 0.75);
  backdrop-filter: blur(20px) saturate(180%);
  -webkit-backdrop-filter: blur(20px) saturate(180%);
  border-bottom: 1px solid var(--bm-border);
}

.topbar .left {
  display: flex;
  align-items: center;
  gap: 16px;
  position: relative;
  z-index: 1;
}

.topbar .right {
  display: flex;
  align-items: center;
  gap: 8px;
  position: relative;
  z-index: 1;
}

.collapse-btn {
  width: 36px;
  height: 36px;
  border-radius: 10px !important;
  transition: all 0.25s var(--bm-ease) !important;
}

.collapse-btn:hover {
  background: var(--bm-primary-soft) !important;
  color: var(--bm-primary-2) !important;
}

.icon-btn {
  width: 36px;
  height: 36px;
  border-radius: 10px !important;
  transition: all 0.25s var(--bm-ease) !important;
}

.icon-btn:hover {
  background: var(--bm-primary-soft) !important;
  color: var(--bm-primary-2) !important;
}

.topbar-divider {
  width: 1px;
  height: 24px;
  background: var(--bm-border);
  margin: 0 8px;
}

/* 用户信息 */
.user {
  display: flex;
  align-items: center;
  gap: 10px;
  cursor: pointer;
  outline: none;
  padding: 6px 12px 6px 6px;
  border-radius: 999px;
  transition: all 0.25s var(--bm-ease);
}

.user:hover {
  background: var(--bm-primary-soft);
}

.avatar-ring {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
}

.avatar-ring::before {
  content: '';
  position: absolute;
  inset: -3px;
  border-radius: 50%;
  background: var(--bm-gradient);
  opacity: 0.6;
  z-index: -1;
  filter: blur(4px);
  transition: opacity 0.3s var(--bm-ease);
}

.user:hover .avatar-ring::before {
  opacity: 1;
}

.user-info {
  display: flex;
  flex-direction: column;
  line-height: 1.2;
}

.uname {
  font-size: 14px;
  font-weight: 600;
  color: var(--bm-text);
}

.urole {
  font-size: 11.5px;
  color: var(--bm-text-mute);
}

.arrow-icon {
  font-size: 12px;
  color: var(--bm-text-mute);
  transition: transform 0.25s var(--bm-ease);
}

.user:hover .arrow-icon {
  transform: translateY(2px);
  color: var(--bm-primary-2);
}

/* ============================ 页面内容区 ============================ */
.page {
  flex: 1;
  padding: 24px;
  overflow: auto;
  position: relative;
  z-index: 1;
}

/* 页面过渡动画 */
.page-fade-enter-active,
.page-fade-leave-active {
  transition: opacity 0.3s var(--bm-ease), transform 0.3s var(--bm-ease);
}

.page-fade-enter-from {
  opacity: 0;
  transform: translateY(16px) scale(0.995);
}

.page-fade-leave-to {
  opacity: 0;
  transform: translateY(-8px) scale(0.995);
}

/* ============================ 深色模式适配 ============================ */
html.dark .admin {
  background: var(--bm-bg);
}

html.dark .sidebar-bg {
  background: rgba(20, 22, 29, 0.88);
  backdrop-filter: blur(20px) saturate(180%);
  -webkit-backdrop-filter: blur(20px) saturate(180%);
  box-shadow: 4px 0 24px rgba(0, 0, 0, 0.2);
}

html.dark .topbar-bg {
  background: rgba(24, 27, 36, 0.78);
  backdrop-filter: blur(20px) saturate(180%);
  -webkit-backdrop-filter: blur(20px) saturate(180%);
}

html.dark .orb {
  opacity: 0.25;
}

html.dark .grid-pattern {
  opacity: 0.3;
}

html.dark .user:hover {
  background: var(--bm-primary-soft);
}

/* 减少动画偏好 */
@media (prefers-reduced-motion: reduce) {
  .orb {
    animation: none;
  }
}

/* 响应式 */
@media (max-width: 768px) {
  .sidebar {
    position: fixed;
    left: 0;
    top: 0;
    bottom: 0;
    transform: translateX(-100%);
    transition: transform 0.3s var(--bm-ease);
    z-index: 100;
  }

  .sidebar:not(.collapsed) {
    transform: translateX(0);
  }

  .user-info {
    display: none;
  }

  .page {
    padding: 16px;
  }
}
</style>
