import { fileURLToPath, URL } from 'node:url'
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import AutoImport from 'unplugin-auto-import/vite'
import Components from 'unplugin-vue-components/vite'
import { ElementPlusResolver } from 'unplugin-vue-components/resolvers'

export default defineConfig({
  plugins: [
    vue(),
    // Element Plus 按需引入：
    // 模板里的 el-* 组件与 v-loading 等指令由插件自动解析并局部 import，
    // 取代原先 main.js 的全量注册（全量方案会带来 1038KB JS + 356KB CSS 的首屏开销）。
    // 注意：命令式调用的 ElMessage / ElMessageBox 没有模板可供解析，
    // 其样式需在 main.js 手动引入。
    AutoImport({ resolvers: [ElementPlusResolver()], dts: false }),
    Components({ resolvers: [ElementPlusResolver()], dts: false }),
  ],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url)),
    },
  },
  server: {
    host: '0.0.0.0',
    port: 5173,
    strictPort: true, // 端口被占用时直接报错退出，避免静默漂移到 5174 导致 start-all 误判
    // 开发代理：/api 与 /static 转发到 FastAPI
    proxy: {
      '/api': { target: 'http://127.0.0.1:8000', changeOrigin: true },
      '/static': { target: 'http://127.0.0.1:8000', changeOrigin: true },
    },
  },
  build: {
    outDir: 'dist',
    // 回到 Vite 默认量级：此前调到 1500 会把超过 1MB 的 chunk 警告一并吞掉，
    // 等于关掉了这道体检（EP 全量引入时单 chunk 达 1038KB 却不告警）。
    chunkSizeWarningLimit: 500,
    rollupOptions: {
      output: {
        manualChunks(id) {
          if (!id.includes('node_modules')) return
          const p = id.replace(/\\/g, '/')
          // 关键：不要按 'element-plus' 做强制分组。
          // 强分组会把「后台才用的重型组件」（table / form / select / upload / dialog）
          // 与「首屏就要用的轻量组件」（input / button / icon）合并进同一 chunk；
          // 入口 chunk 依赖它 → index.html 会 modulepreload 整个包，
          // 结果是后台的几百 KB 组件在首屏就被下载。
          // 这里交由 Rollup 按动态导入边界自动分割，组件随用到它的路由按需加载。
          if (p.includes('markdown-it') || p.includes('highlight.js')) return 'markdown'
          // 用包目录精确匹配，避免 'vue' 子串把 @vueuse / vue-demi 等一并误捕
          if (/\/node_modules\/(vue|vue-router|pinia|axios|dayjs)\//.test(p)) return 'vendor'
          if (p.includes('/node_modules/@vue/')) return 'vendor'
        },
      },
    },
  },
})
