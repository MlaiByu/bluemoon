import { createRouter, createWebHistory } from 'vue-router'
import NProgress from 'nprogress'
import { useUserStore } from '@/stores/user'

const routes = [
  {
    path: '/',
    component: () => import('@/layouts/FrontLayout.vue'),
    children: [
      { path: '', name: 'home', component: () => import('@/views/Home.vue'), meta: { title: '首页' } },
      { path: 'post/:slug', name: 'post', component: () => import('@/views/PostDetail.vue'), meta: { title: '文章' } },
      { path: 'archives', name: 'archives', component: () => import('@/views/Archive.vue'), meta: { title: '归档' } },
      { path: 'categories', name: 'categories', component: () => import('@/views/Categories.vue'), meta: { title: '分类' } },
      { path: 'images', name: 'images', component: () => import('@/views/Images.vue'), meta: { title: '图片' } },
      { path: 'about', name: 'about', component: () => import('@/views/About.vue'), meta: { title: '关于我' } },
      { path: 'search', name: 'search', component: () => import('@/views/Home.vue'), meta: { title: '搜索' } },
    ],
  },
  {
    path: '/admin/login',
    name: 'admin-login',
    component: () => import('@/views/admin/Login.vue'),
    meta: { title: '后台登录' },
  },
  {
    path: '/admin',
    component: () => import('@/layouts/AdminLayout.vue'),
    meta: { requiresAuth: true },
    children: [
      { path: '', name: 'admin-dashboard', component: () => import('@/views/admin/Dashboard.vue'), meta: { title: '仪表盘' } },
      { path: 'posts', name: 'admin-posts', component: () => import('@/views/admin/PostsAdmin.vue'), meta: { title: '文章管理' } },
      { path: 'posts/new', name: 'admin-post-new', component: () => import('@/views/admin/PostEdit.vue'), meta: { title: '写文章' } },
      { path: 'posts/:id', name: 'admin-post-edit', component: () => import('@/views/admin/PostEdit.vue'), meta: { title: '编辑文章' } },
      { path: 'categories', name: 'admin-categories', component: () => import('@/views/admin/CategoriesAdmin.vue'), meta: { title: '分类管理' } },
      { path: 'images', name: 'admin-images', component: () => import('@/views/admin/ImagesAdmin.vue'), meta: { title: '图片管理' } },
      { path: 'profile', name: 'admin-profile', component: () => import('@/views/admin/ProfileAdmin.vue'), meta: { title: '站点设置' } },
    ],
  },
  { path: '/:pathMatch(.*)*', name: 'not-found', component: () => import('@/views/NotFound.vue'), meta: { title: '页面不存在' } },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
  // 保留浏览器前进/后退的位置恢复；新导航回到顶部
  scrollBehavior: (to, from, savedPosition) => savedPosition || { top: 0 },
})

router.beforeEach(async (to) => {
  NProgress.start()
  const store = useUserStore()

  // 已登录用户访问登录页时直接回仪表盘
  if (to.name === 'admin-login' && store.token) return { name: 'admin-dashboard' }

  if (to.meta.requiresAuth) {
    if (!store.token) return { name: 'admin-login', query: { redirect: to.fullPath } }
    if (!store.user) {
      // fetchMe 失败时 store 内部已清除失效 token
      const user = await store.fetchMe()
      if (!user) return { name: 'admin-login' }
      if (to.meta.roles && !to.meta.roles.includes(user.role)) return { name: 'home' }
    } else if (to.meta.roles && !to.meta.roles.includes(store.user.role)) {
      return { name: 'home' }
    }
  }
  const title = to.meta.title
  document.title = title ? `${title} · Bluemoon` : 'Bluemoon · 个人博客'
})

router.afterEach(() => NProgress.done())

export default router
