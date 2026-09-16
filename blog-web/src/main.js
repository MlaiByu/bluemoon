import { createApp } from 'vue'
import { createPinia } from 'pinia'
import { ElLoading } from 'element-plus/es/components/loading/index'

// Element Plus 采用按需引入（组件解析见 vite.config.js 的 ElementPlusResolver）。
// 模板里的 el-* 由插件自动引入，这里只处理插件覆盖不到的三件事：
import 'element-plus/theme-chalk/dark/css-vars.css' // 1. 暗色变量（跟随 html.dark）
import 'element-plus/es/components/loading/style/css' // 2. v-loading 指令样式
import 'element-plus/es/components/message/style/css' // 3. 命令式组件样式：ElMessage
import 'element-plus/es/components/message-box/style/css' //    ElMessageBox

import 'nprogress/nprogress.css'
import '@/styles/index.css'
import '@/styles/admin-common.css'
import '@/styles/layout-common.css'

import App from './App.vue'
import router from './router'
import { registerGlobalIcons } from '@/icons'
import { initTheme } from '@/composables/useTheme'

// 应用持久化的主题（在挂载前设置，避免深色模式首屏闪烁）
initTheme()

const app = createApp(App)

// v-loading 是指令而非组件，显式注册，不依赖插件的指令推断
app.directive('loading', ElLoading.directive)

// 全局图标：只注册项目实际用到的 26 个（原先是图标包全部 2000+ 个）
registerGlobalIcons(app)

app.use(createPinia())
app.use(router)
// 组件库的 locale 已改由 App.vue 的 <el-config-provider> 提供
app.mount('#app')
