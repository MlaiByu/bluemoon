<template>
  <div class="md-editor">
    <div class="toolbar">
      <el-button-group size="small">
        <el-button title="加粗" @click="wrap('**', '**')"><b>B</b></el-button>
        <el-button title="斜体" @click="wrap('*', '*')"><i>I</i></el-button>
        <el-button title="删除线" @click="wrap('~~', '~~')"><s>S</s></el-button>
      </el-button-group>
      <el-button-group size="small">
        <el-button @click="prefix('## ')">H2</el-button>
        <el-button @click="prefix('### ')">H3</el-button>
        <el-button @click="prefix('> ')">引用</el-button>
        <el-button @click="prefix('- ')">列表</el-button>
      </el-button-group>
      <el-button-group size="small">
        <el-button @click="insert('```\n', '\n```', '代码')">代码块</el-button>
        <el-button @click="insert('[', '](https://)', '链接文本')">链接</el-button>
        <el-button @click="insertTable">表格</el-button>
        <el-button @click="insert('---\n', '', '')">分割线</el-button>
      </el-button-group>

      <el-upload
        class="uploader"
        :show-file-list="false"
        :http-request="onUpload"
        accept="image/*"
      >
        <el-button size="small" :icon="Picture" :loading="uploading">插入图片</el-button>
      </el-upload>

      <div class="spacer"></div>
      <el-button size="small" :type="preview ? 'primary' : 'default'" @click="preview = !preview">
        {{ preview ? '编辑' : '预览' }}
      </el-button>
    </div>

    <div class="panes">
      <textarea
        ref="textareaRef"
        v-model="model"
        class="input"
        :placeholder="placeholder"
        @keydown.tab.prevent="insert('  ', '', '')"
      ></textarea>
      <div v-show="preview" class="preview">
        <MarkdownView :content="model" />
        <div v-if="!model.trim()" class="preview-empty">暂无内容</div>
      </div>
    </div>

    <div class="status">
      <span>{{ wordCount }} 字</span>
      <span>{{ model.length }} 字符</span>
    </div>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue'
import { ElMessage } from 'element-plus/es/components/message/index'
import { Picture } from '@element-plus/icons-vue'
import MarkdownView from './MarkdownView.vue'
import { uploadImage } from '@/api'

const props = defineProps({
  placeholder: { type: String, default: '用 Markdown 书写…' },
})
const model = defineModel({ type: String, default: '' }) // Vue 3.4+ defineModel

const textareaRef = ref(null)
const preview = ref(false)
const uploading = ref(false)

const wordCount = computed(() => {
  const text = (model.value || '')
    .replace(/```[\s\S]*?```/g, ' ')
    .replace(/[#>*`\-[\]()]/g, ' ')
  const cjk = (text.match(/[\u4e00-\u9fff]/g) || []).length
  const words = (text.match(/[A-Za-z0-9]+/g) || []).length
  return cjk + words
})

function getSelectionRange() {
  const el = textareaRef.value
  if (!el) return [0, 0]
  return [el.selectionStart, el.selectionEnd]
}

function replaceRange(start, end, text, selStart, selEnd) {
  const el = textareaRef.value
  const value = model.value || ''
  model.value = value.slice(0, start) + text + value.slice(end)
  requestAnimationFrame(() => {
    el.focus()
    if (selStart != null) el.setSelectionRange(selStart, selEnd ?? selStart)
  })
}

function wrap(left, right) {
  const [s, e] = getSelectionRange()
  const selected = (model.value || '').slice(s, e) || '文本'
  replaceRange(s, e, `${left}${selected}${right}`, s + left.length, s + left.length + selected.length)
}

function prefix(mark) {
  const [s, e] = getSelectionRange()
  const value = model.value || ''
  const lineStart = value.lastIndexOf('\n', s - 1) + 1
  const selected = value.slice(lineStart, e) || '标题'
  replaceRange(lineStart, e, mark + selected, lineStart + mark.length, lineStart + mark.length + selected.length)
}

function insert(before, after, placeholderText) {
  const [s, e] = getSelectionRange()
  const selected = (model.value || '').slice(s, e) || placeholderText || ''
  const text = before + selected + after
  replaceRange(s, e, text, s + before.length, s + before.length + selected.length)
}

function insertTable() {
  const table = '\n| 列1 | 列2 |\n| --- | --- |\n| 内容 | 内容 |\n'
  const el = textareaRef.value
  const pos = el ? el.selectionEnd : (model.value || '').length
  replaceRange(pos, pos, table, pos + table.length)
}

async function onUpload({ file }) {
  uploading.value = true
  try {
    // scope=post：文章图片仅随文章展示，不进入网站图片栏
    const { url } = await uploadImage(file, 'post')
    insert(`![${file.name}](${url})`, '', '')
    ElMessage.success('图片已插入')
  } catch {
    /* 拦截器已提示 */
  } finally {
    uploading.value = false
  }
}

defineExpose({ focus: () => textareaRef.value?.focus() })
</script>

<style scoped>
/* 容器与所有面板背景均使用主题令牌，明暗模式自动适配
   —— 之前硬编码 #fff / #fafbfc / #fcfcfd 导致暗色下出现刺眼的白条 */
.md-editor {
  border: 1px solid var(--bm-border);
  border-radius: 8px;
  overflow: hidden;
  background: var(--bm-card);
}

.toolbar {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px;
  padding: 8px 10px;
  background: var(--bm-primary-soft);
  border-bottom: 1px solid var(--bm-border);
}

.uploader {
  display: inline-flex;
}

.spacer {
  flex: 1;
}

.panes {
  display: flex;
  min-height: 420px;
}

.input {
  flex: 1;
  min-width: 0;
  padding: 14px 16px;
  border: none;
  outline: none;
  resize: vertical;
  font-family: 'JetBrains Mono', Consolas, Monaco, monospace;
  font-size: 14px;
  line-height: 1.8;
  color: var(--bm-text);
  background: var(--bm-card); /* 显式声明：避免继承或浏览器默认白底 */
}

.preview {
  flex: 1;
  min-width: 0;
  padding: 14px 20px;
  border-left: 1px solid var(--bm-border);
  overflow-y: auto;
  max-height: 620px;
  background: var(--bm-bg); /* 预览面板与页面背景一致 */
}

.preview-empty {
  color: var(--bm-text-mute);
  font-size: 14px;
}

.status {
  display: flex;
  gap: 16px;
  padding: 6px 14px;
  font-size: 12px;
  color: var(--bm-text-sub);
  background: var(--bm-primary-soft); /* 与工具栏一致，方便视觉统一 */
  border-top: 1px solid var(--bm-border);
}

@media (max-width: 900px) {
  .panes {
    flex-direction: column;
  }
  .preview {
    border-left: none;
    border-top: 1px solid var(--bm-border);
  }
}
</style>
