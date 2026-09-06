<template>
  <div class="markdown-body" v-html="html"></div>
</template>

<script setup>
import { computed } from 'vue'
import MarkdownIt from 'markdown-it'
import hljs from 'highlight.js/lib/common'
import { resolveImageUrl } from '@/utils/format'

const props = defineProps({
  content: { type: String, default: '' },
})

/* md 实例与 hljs 在模块级别创建，所有 MarkdownView 共享同一份，
   避免每次组件挂载重建（含 180+ 语言正则注册）造成性能浪费。 */
const md = new MarkdownIt({
  html: true,
  linkify: true,
  breaks: false,
  typographer: false,
  highlight(str, lang) {
    if (lang && hljs.getLanguage(lang)) {
      try {
        return `<pre class="hljs"><code>${hljs.highlight(str, { language: lang, ignoreIllegals: true }).value}</code></pre>`
      } catch {
        /* fallthrough */
      }
    }
    return `<pre class="hljs"><code>${md.utils.escapeHtml(str)}</code></pre>`
  },
})

// 外链新窗口打开
const defaultLinkOpen = md.renderer.rules.link_open || ((tokens, idx, opts, _env, self) => self.renderToken(tokens, idx, opts))
md.renderer.rules.link_open = (tokens, idx, opts, env, self) => {
  const href = tokens[idx].attrGet('href') || ''
  if (/^https?:\/\//.test(href)) {
    tokens[idx].attrSet('target', '_blank')
    tokens[idx].attrSet('rel', 'noopener noreferrer')
  }
  return defaultLinkOpen(tokens, idx, opts, env, self)
}

// 图片路径统一处理 + 懒加载
const defaultImage = md.renderer.rules.image || ((tokens, idx, opts, _env, self) => self.renderToken(tokens, idx, opts))
md.renderer.rules.image = (tokens, idx, opts, env, self) => {
  const src = tokens[idx].attrGet('src') || ''
  tokens[idx].attrSet('src', resolveImageUrl(src))
  tokens[idx].attrSet('loading', 'lazy')
  // 增加加载失败占位（中性半透明，明暗模式通用）
  tokens[idx].attrSet('onerror', "this.style.opacity='0.3';this.style.background='rgba(128,132,160,0.18)'")
  return defaultImage(tokens, idx, opts, env, self)
}

const html = computed(() => md.render(props.content || ''))
</script>

<style scoped>
.markdown-body :deep(img) {
  max-width: 100%;
  border-radius: 8px;
  margin: 12px 0;
  transition: opacity 0.3s;
}
</style>
