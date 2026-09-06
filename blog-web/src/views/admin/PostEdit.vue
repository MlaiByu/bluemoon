<template>
  <div v-loading="pageLoading" class="post-edit bm-fade-up">
    <div class="head">
      <h2 class="title">
        <span class="title-icon"><el-icon><EditPen /></el-icon></span>
        {{ isEdit ? '编辑文章' : '写文章' }}
      </h2>
      <div class="ops">
        <el-button @click="$router.push('/admin/posts')">返回列表</el-button>
        <el-button v-if="isEdit" :icon="View" @click="preview">前台查看</el-button>
        <el-button :icon="DocumentAdd" :loading="saving" @click="save(0)">存为草稿</el-button>
        <el-button type="primary" :icon="Promotion" :loading="saving" @click="save(1)">
          {{ isEdit ? '保存修改' : '发布文章' }}
        </el-button>
      </div>
    </div>

    <el-row :gutter="16">
      <el-col :xs="24" :lg="17">
        <div class="bm-card panel editor-panel">
          <el-input v-model="form.title" placeholder="请输入文章标题..." class="title-input" maxlength="200" show-word-limit />
          <MarkdownEditor v-model="form.content" class="editor" />
        </div>
      </el-col>

      <el-col :xs="24" :lg="7">
        <!-- 发布设置 -->
        <div class="bm-card panel side-panel">
          <h3 class="panel-title"><span class="dot"></span>发布设置</h3>
          <el-form label-position="top" size="default">
            <el-form-item label="URL 别名（slug）">
              <el-input v-model="form.slug" placeholder="留空则自动生成" clearable />
              <div class="hint">用于文章链接，建议使用英文或拼音</div>
            </el-form-item>

            <el-form-item label="分类">
              <el-select v-model="form.category_id" placeholder="选择分类" clearable filterable allow-create
                         default-first-option class="full" @change="onCategoryChange">
                <el-option v-for="c in categories" :key="c.id" :label="c.name" :value="c.id" />
              </el-select>
            </el-form-item>

            <el-form-item label="摘要">
              <el-input v-model="form.summary" type="textarea" :rows="4" maxlength="500" show-word-limit
                        placeholder="留空则自动从正文提取前 120 字" />
            </el-form-item>

            <el-form-item>
              <el-checkbox v-model="form.is_top" class="top-checkbox">
                <span class="checkbox-text">置顶该文章</span>
                <el-icon class="pin-icon"><Star /></el-icon>
              </el-checkbox>
            </el-form-item>
          </el-form>
        </div>

        <!-- 封面 -->
        <div class="bm-card panel side-panel">
          <h3 class="panel-title"><span class="dot"></span>封面图</h3>
          <el-upload
            class="cover-uploader"
            drag
            :show-file-list="false"
            :http-request="onCoverUpload"
            :disabled="coverUploading"
            accept="image/jpeg,image/png,image/gif,image/webp,image/bmp"
          >
            <div v-loading="coverUploading" element-loading-text="封面上传中…" class="cover-wrapper">
              <template v-if="form.cover">
                <img :src="form.cover" class="cover" alt="封面" />
                <div class="cover-mask">
                  <span class="mask-tip">
                    <el-icon><Refresh /></el-icon>
                    点击或拖拽图片替换
                  </span>
                </div>
              </template>
              <div v-else class="placeholder">
                <div class="ph-icon">
                  <el-icon :size="28"><Plus /></el-icon>
                </div>
                <span class="ph-text">点击或拖拽上传封面</span>
                <span class="ph-hint">支持 jpg / png / gif / webp / bmp，单张 ≤ 5MB</span>
              </div>
            </div>
          </el-upload>
          <div v-if="form.cover" class="cover-ops">
            <span class="cover-hint">封面随文章保存，不会进入图片栏</span>
            <el-button size="small" text type="danger" :icon="Delete" @click="removeCover">
              删除封面
            </el-button>
          </div>
        </div>

        <!-- 文章信息 -->
        <div v-if="isEdit" class="bm-card panel side-panel">
          <h3 class="panel-title"><span class="dot"></span>文章信息</h3>
          <ul class="meta-list">
            <li>
              <span class="meta-label">ID</span>
              <b class="meta-value">{{ form.id }}</b>
            </li>
            <li>
              <span class="meta-label">状态</span>
              <b class="meta-value">
                <el-tag :type="form.status === 1 ? 'success' : 'info'" size="small" effect="light" round>
                  {{ form.status === 1 ? '已发布' : '草稿' }}
                </el-tag>
              </b>
            </li>
            <li>
              <span class="meta-label">阅读量</span>
              <b class="meta-value">{{ form.views ?? 0 }}</b>
            </li>
            <li>
              <span class="meta-label">字数</span>
              <b class="meta-value">{{ form.word_count ?? 0 }}</b>
            </li>
            <li>
              <span class="meta-label">创建时间</span>
              <b class="meta-value">{{ formatDateTime(form.created_at) }}</b>
            </li>
            <li>
              <span class="meta-label">更新时间</span>
              <b class="meta-value">{{ formatDateTime(form.updated_at) }}</b>
            </li>
          </ul>
        </div>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Delete, DocumentAdd, EditPen, Plus, Promotion, Refresh, Star, View } from '@element-plus/icons-vue'
import MarkdownEditor from '@/components/MarkdownEditor.vue'
import { createCategory, createPost, getCategories, getPostById, updatePost, uploadImage } from '@/api'
import { formatDateTime } from '@/utils/format'

const route = useRoute()
const router = useRouter()

const isEdit = computed(() => !!route.params.id)
const pageLoading = ref(false)
const saving = ref(false)

const categories = ref([])
const tags = ref([])

const form = reactive({
  id: null,
  title: '',
  slug: '',
  summary: '',
  content: '',
  cover: '',
  status: 1,
  is_top: false,
  category_id: null,
  tag_ids: [],
  views: 0,
  word_count: 0,
  created_at: null,
  updated_at: null,
})

async function loadOptions() {
  categories.value = await getCategories() || []
}

async function loadPost() {
  pageLoading.value = true
  try {
    const p = await getPostById(route.params.id)
    Object.assign(form, {
      id: p.id,
      title: p.title,
      slug: p.slug,
      summary: p.summary || '',
      content: p.content || '',
      cover: p.cover || '',
      status: p.status,
      is_top: !!p.is_top,
      category_id: p.category_id,
      views: p.views,
      word_count: p.word_count,
      created_at: p.created_at,
      updated_at: p.updated_at,
    })
  } finally {
    pageLoading.value = false
  }
}

async function save(status) {
  if (!form.title.trim()) {
    ElMessage.warning('请填写文章标题')
    return
  }
  if (!form.content.trim()) {
    ElMessage.warning('正文不能为空')
    return
  }
  saving.value = true
  try {
    const payload = {
      title: form.title,
      slug: form.slug || null,
      summary: form.summary || null,
      content: form.content,
      cover: form.cover || null,
      status,
      is_top: form.is_top,
      category_id: form.category_id,
      tag_ids: form.tag_ids,
    }
    if (isEdit.value) {
      await updatePost(form.id, payload)
      ElMessage.success(status === 1 ? '已保存并发布' : '已存为草稿')
    } else {
      const created = await createPost(payload)
      ElMessage.success(status === 1 ? '文章已发布' : '已存为草稿')
      router.replace(`/admin/posts/${created.id}`)
      return
    }
    await loadPost()
  } catch {
    /* 拦截器已提示 */
  } finally {
    saving.value = false
  }
}

// 允许在下拉框里直接新建分类
async function onCategoryChange(val) {
  if (typeof val !== 'string') return
  const name = val.trim()
  if (!name) return
  try {
    const created = await createCategory({ name })
    categories.value = await getCategories()
    form.category_id = created.id
    ElMessage.success(`已新建分类「${created.name}」`)
  } catch {
    form.category_id = null
  }
}

// ---------------- 封面图上传 ----------------
const coverUploading = ref(false)

// 与后端 upload 接口的限制保持一致：类型白名单 + 5MB 上限
const COVER_MAX_SIZE = 5 * 1024 * 1024
const COVER_ALLOWED_EXTS = ['jpg', 'jpeg', 'png', 'gif', 'webp', 'bmp']

function validateCoverFile(file) {
  const ext = (file.name.split('.').pop() || '').toLowerCase()
  if (!COVER_ALLOWED_EXTS.includes(ext)) {
    ElMessage.error(`不支持的图片格式：${ext || '未知'}，仅支持 ${COVER_ALLOWED_EXTS.join(' / ')}`)
    return false
  }
  if (file.size > COVER_MAX_SIZE) {
    ElMessage.error(`封面图过大（${formatSize(file.size)}），不能超过 5MB`)
    return false
  }
  return true
}

// 紧凑体积格式（显示空间小，与 utils/format.js 的通用 formatSize 刻意不同）
function formatSize(bytes) {
  if (bytes >= 1024 * 1024) return `${(bytes / 1024 / 1024).toFixed(1)}MB`
  if (bytes >= 1024) return `${(bytes / 1024).toFixed(0)}KB`
  return `${bytes}B`
}

async function onCoverUpload({ file }) {
  if (!validateCoverFile(file)) return
  coverUploading.value = true
  try {
    // scope=post：封面图属于文章图片，仅随文章展示，不进入网站图片栏
    const { url } = await uploadImage(file, 'post')
    form.cover = url // 上传成功后自动写入文章数据，随保存接口提交
    ElMessage.success('封面已上传，保存文章后生效')
  } catch {
    /* 上传失败提示由请求拦截器统一处理 */
  } finally {
    coverUploading.value = false
  }
}

function removeCover() {
  ElMessageBox.confirm('确定删除该封面图吗？', '删除确认', {
    type: 'warning',
    confirmButtonText: '删除',
    cancelButtonText: '取消',
    confirmButtonClass: 'el-button--danger',
  })
    .then(() => {
      form.cover = ''
      ElMessage.success('封面已移除，保存文章后生效')
    })
    .catch(() => {})
}

const preview = () => {
  if (form.status !== 1) {
    ElMessage.info('草稿文章，前台不可见')
    return
  }
  router.push({ name: 'post', params: { slug: form.slug } })
}

onMounted(async () => {
  await loadOptions()
  if (isEdit.value) await loadPost()
})
</script>

<style scoped>
.post-edit {
  position: relative;
}

/* 页面头部 */
.head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 16px;
  margin-bottom: 18px;
}

.title {
  display: flex;
  align-items: center;
  gap: 12px;
  margin: 0;
  font-size: 22px;
  font-weight: 800;
  letter-spacing: 0.3px;
}

.title-icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 42px;
  height: 42px;
  border-radius: 12px;
  background: var(--bm-gradient);
  color: #fff;
  box-shadow: 0 8px 20px var(--bm-shadow-color);
}

.ops {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}

/* 编辑器面板 */
.editor-panel {
  padding: 24px;
}

.title-input :deep(.el-input__wrapper) {
  box-shadow: none;
  border-bottom: 2px solid var(--bm-border);
  border-radius: 0;
  padding-left: 0;
  padding-right: 0;
  transition: border-color 0.3s var(--bm-ease);
}

.title-input :deep(.el-input__wrapper:hover) {
  border-bottom-color: var(--bm-primary);
  box-shadow: none;
}

.title-input :deep(.el-input.is-focus .el-input__wrapper) {
  border-bottom-color: var(--bm-primary-2);
  box-shadow: none;
}

.title-input :deep(.el-input__inner) {
  font-size: 22px;
  font-weight: 700;
  height: 52px;
  letter-spacing: 0.3px;
}

.title-input :deep(.el-input__count) {
  color: var(--bm-text-mute);
  font-size: 12px;
}

.editor {
  margin-top: 18px;
}

/* 侧边栏面板 */
.side-panel {
  margin-bottom: 16px;
}

.panel-title {
  display: flex;
  align-items: center;
  gap: 9px;
  margin: 0 0 18px;
  font-size: 15.5px;
  font-weight: 700;
  line-height: 1.2;
}

.panel-title .dot {
  width: 9px;
  height: 9px;
  border-radius: 3px;
  background: var(--bm-gradient);
  transform: rotate(45deg);
  box-shadow: 0 3px 8px var(--bm-shadow-color);
}

.full {
  width: 100%;
}

.hint {
  margin-top: 6px;
  font-size: 12px;
  color: var(--bm-text-mute);
  line-height: 1.5;
}

/* 置顶复选框 */
.top-checkbox {
  display: flex;
  align-items: center;
  width: 100%;
  padding: 10px 14px;
  background: var(--bm-accent-soft);
  border-radius: 10px;
  margin: 0;
}

.checkbox-text {
  flex: 1;
  font-weight: 500;
  color: var(--bm-text);
}

.pin-icon {
  color: var(--bm-accent);
  font-size: 16px;
}

/* 封面上传 */
.cover-uploader {
  width: 100%;
}

.cover-uploader :deep(.el-upload) {
  width: 100%;
}

/* 拖拽区去默认边框，视觉由 placeholder / cover 自绘 */
.cover-uploader :deep(.el-upload-dragger) {
  width: 100%;
  height: auto;
  padding: 0;
  border: none;
  background: transparent;
  border-radius: var(--bm-radius-sm);
  transition: none;
}

.cover-uploader :deep(.el-upload-dragger:hover) {
  border: none;
}

.cover-wrapper {
  position: relative;
  width: 100%;
  overflow: hidden;
  border-radius: var(--bm-radius-sm);
}

.cover {
  width: 100%;
  height: 180px;
  object-fit: cover;
  border-radius: var(--bm-radius-sm);
  display: block;
  transition: transform 0.3s var(--bm-ease);
}

.cover-uploader:hover .cover {
  transform: scale(1.02);
}

/* 悬停遮罩：提示可替换 */
.cover-mask {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: flex-end;
  justify-content: center;
  padding-bottom: 14px;
  border-radius: var(--bm-radius-sm);
  background: linear-gradient(to top, rgba(15, 17, 23, 0.55) 0%, transparent 45%);
  opacity: 0;
  transition: opacity 0.25s var(--bm-ease);
  pointer-events: none;
}

.cover-uploader:hover .cover-mask {
  opacity: 1;
}

.mask-tip {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 6px 14px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.92);
  color: var(--bm-text);
  font-size: 12.5px;
  font-weight: 600;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.18);
}

html.dark .mask-tip {
  background: rgba(30, 27, 45, 0.92);
  color: var(--bm-text);
}

.placeholder {
  width: 100%;
  height: 180px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 6px;
  border: 2px dashed var(--bm-border);
  border-radius: var(--bm-radius-sm);
  color: var(--bm-text-mute);
  font-size: 13px;
  cursor: pointer;
  transition: all 0.3s var(--bm-ease);
  background: linear-gradient(135deg, rgba(138, 182, 255, 0.03) 0%, rgba(255, 176, 200, 0.03) 100%);
}

.cover-uploader:hover .placeholder,
.cover-uploader :deep(.el-upload-dragger:hover) .placeholder {
  border-color: var(--bm-primary-2);
  color: var(--bm-primary-2);
  background: var(--bm-primary-soft);
}

.ph-icon {
  width: 48px;
  height: 48px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 14px;
  background: var(--bm-primary-soft);
  color: var(--bm-primary-2);
  margin-bottom: 4px;
}

.ph-text {
  font-weight: 600;
  font-size: 14px;
}

.ph-hint {
  font-size: 11.5px;
  opacity: 0.8;
}

/* 封面操作行 */
.cover-ops {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  margin-top: 10px;
}

.cover-hint {
  font-size: 11.5px;
  color: var(--bm-text-mute);
}

/* 文章信息 */
.meta-list {
  list-style: none;
  margin: 0;
  padding: 0;
  font-size: 13px;
}

.meta-list li {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 0;
  border-bottom: 1px dashed var(--bm-border);
}

.meta-list li:last-child {
  border-bottom: none;
}

.meta-label {
  color: var(--bm-text-sub);
  font-size: 13px;
}

.meta-value {
  font-weight: 600;
  color: var(--bm-text);
  font-size: 13px;
}

/* 深色模式 */
html.dark .top-checkbox {
  background: rgba(255, 158, 192, 0.1);
}

html.dark .placeholder {
  background: linear-gradient(135deg, rgba(143, 157, 255, 0.05) 0%, rgba(239, 143, 180, 0.05) 100%);
}

html.dark .ph-icon {
  background: var(--bm-primary-soft);
}

/* 响应式 */
@media (max-width: 1024px) {
  .title {
    font-size: 18px;
  }

  .title-input :deep(.el-input__inner) {
    font-size: 18px;
  }
}
</style>
