<template>
  <!--
    图片加载失败统一用「捕获阶段的委托」处理：
    正文里的 <img> 是 v-html 注入的，逐个绑定既不现实、也没法用内联 onerror（等于往
    HTML 属性里拼 JS 字符串）。error 事件不冒泡但会进入捕获阶段，父级监听即可兜住全部子图。
  -->
  <div class="markdown-body" v-html="html" @error.capture="onImgError"></div>
</template>

<script setup>
import { computed } from 'vue'
import MarkdownIt from 'markdown-it'
import hljs from 'highlight.js/lib/common'
import { resolveImageUrl, resolveImageVariant } from '@/utils/format'
import { sanitizeRawHtml } from '@/utils/sanitizeHtml'

const props = defineProps({
  content: { type: String, default: '' },
})

/* md 实例与 hljs 在模块级别创建，所有 MarkdownView 共享同一份，
   避免每次组件挂载重建（含 180+ 语言正则注册）造成性能浪费。 */
const md = new MarkdownIt({
  // html: true 兼容既有文章中的富文本；原始 HTML 由下方 sanitize 规则兜底
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

// 原始 HTML token 清洗：只动 html_block / html_inline，代码块不受影响
md.core.ruler.push('bm_sanitize_raw_html', (state) => {
  for (const token of state.tokens) {
    if (token.type === 'html_block') {
      token.content = sanitizeRawHtml(token.content)
    } else if (token.type === 'inline' && token.children) {
      for (const child of token.children) {
        if (child.type === 'html_inline') {
          child.content = sanitizeRawHtml(child.content)
        }
      }
    }
  }
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

// 图片路径统一处理 + 衍生档 + 懒加载
// 失败回退交给父级 @error.capture，这里只声明 data-original（不再拼内联 JS）
const defaultImage = md.renderer.rules.image || ((tokens, idx, opts, _env, self) => self.renderToken(tokens, idx, opts))
md.renderer.rules.image = (tokens, idx, opts, env, self) => {
  const src = tokens[idx].attrGet('src') || ''
  const full = resolveImageUrl(src)
  const variant = resolveImageVariant(full, 1024)
  tokens[idx].attrSet('src', variant)
  tokens[idx].attrSet('loading', 'lazy')
  tokens[idx].attrSet('decoding', 'async')
  if (variant !== full) {
    // 站内位图走 1024 衍生档；衍生档缺失（如历史图未回填）由 onImgError 回退原图，
    // 原图也失败才退回中性占位。data-fb 保证只回退一次，避免 onerror 循环。
    tokens[idx].attrSet('data-original', full)
  }
  return defaultImage(tokens, idx, opts, env, self)
}

/** 衍生档 → 原图 → 中性占位，最多两步 */
function onImgError(e) {
  const img = e.target
  if (!(img instanceof HTMLImageElement)) return
  const original = img.dataset.original
  if (original && !img.dataset.fb) {
    img.dataset.fb = '1'
    img.src = original
    return
  }
  img.style.opacity = '0.3'
  img.style.background = 'rgba(128,132,160,0.18)'
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
