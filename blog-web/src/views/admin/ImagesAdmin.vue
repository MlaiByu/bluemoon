<template>
  <div class="images-admin bm-fade-up">
    <div class="page-head">
      <h2 class="block-title"><span class="dot"></span>图片管理</h2>
      <div class="head-actions">
        <span class="count-chip">共 {{ images.length }} 张</span>
        <template v-if="selectedUrls.length">
          <span class="selected-chip">已选 {{ selectedUrls.length }} 张</span>
          <el-button type="danger" :icon="Delete" :loading="deleting" @click="batchRemove">
            删除选中
          </el-button>
          <el-button text @click="clearSelection">取消选择</el-button>
        </template>
        <el-button v-else type="primary" :icon="Grid" @click="selectAll">
          全选
        </el-button>
      </div>
    </div>

    <!-- 上传区 -->
    <div class="panel upload-panel">
      <el-upload
        class="img-uploader"
        drag
        multiple
        :auto-upload="true"
        :show-file-list="false"
        :http-request="doUpload"
        accept="image/*"
      >
        <el-icon class="up-icon"><UploadFilled /></el-icon>
        <div class="up-text">拖拽图片到此处，或点击上传</div>
        <div class="up-hint">支持 jpg / png / gif / webp 等，单张 ≤ 5MB · 此处上传的图片将展示在网站图片栏；文章内插入的图片不会出现在这里</div>
      </el-upload>
    </div>

    <!-- 画廊 -->
    <div class="panel">
      <div class="panel-head">
        <h3 class="block-title"><span class="dot"></span>已上传</h3>
        <span v-if="selectedUrls.length" class="select-tip">点击图片可选择 / 取消选择</span>
      </div>

      <div v-loading="loading" class="grid">
        <figure
          v-for="img in images"
          :key="img.url"
          class="cell"
          :class="{ selected: selectedUrls.includes(img.url) }"
          @click.stop="toggleSelect(img.url)"
        >
          <!-- 选择框 -->
          <div class="select-box" @click.stop="toggleSelect(img.url)">
            <el-checkbox :model-value="selectedUrls.includes(img.url)" />
          </div>

          <el-image
            :src="img.url"
            :alt="img.name"
            fit="cover"
            loading="lazy"
            :preview-src-list="[img.url]"
            preview-teleported
            hide-on-click-modal
            @click.stop
          >
            <template #error>
              <div class="img-error">加载失败</div>
            </template>
          </el-image>

          <figcaption class="meta">
            <span class="name" :title="img.name">{{ img.name }}</span>
            <span class="info">{{ img.size_label }} · {{ img.uploaded_at }}</span>
          </figcaption>

          <div class="actions">
            <button class="act-btn copy" title="复制链接" @click.stop="copyUrl(img.url)">
              <el-icon><CopyDocument /></el-icon>
            </button>
            <button class="act-btn del" title="删除" @click.stop="remove(img)">
              <el-icon><Delete /></el-icon>
            </button>
          </div>
        </figure>
      </div>

      <div v-if="!loading && !images.length" class="empty">
        <el-icon class="empty-icon"><Picture /></el-icon>
        <p>还没有上传任何图片～</p>
        <p class="empty-tip">在上方上传区拖入图片即可保存。</p>
      </div>
    </div>

    <!-- 批量删除确认弹窗 -->
    <el-dialog v-model="batchDialog" title="批量删除确认" width="520px" class="batch-dialog">
      <div v-if="checkingRefs" class="checking-refs">
        <el-icon class="loading-icon"><Loading /></el-icon>
        <span>正在检查图片引用情况…</span>
      </div>

      <template v-else>
        <div class="batch-summary">
          <div class="summary-item">
            <span class="label">选中图片</span>
            <span class="value">{{ selectedUrls.length }} 张</span>
          </div>
          <div class="summary-item danger" v-if="refResults.length">
            <span class="label">被文章引用</span>
            <span class="value">{{ refResults.filter(r => r.referenced).length }} 张</span>
          </div>
        </div>

        <!-- 引用详情 -->
        <div v-if="refResults.some(r => r.referenced)" class="ref-list">
          <div class="ref-title">
            <el-icon size="16"><Warning /></el-icon>
            以下图片仍被文章引用，默认跳过：
          </div>
          <ul>
            <li v-for="r in refResults.filter(r => r.referenced)" :key="r.url" class="ref-item">
              <span class="ref-name">{{ r.name }}</span>
              <span class="ref-count">被 {{ r.ref_count }} 篇引用</span>
              <div class="ref-posts">
                <span v-for="(p, i) in r.ref_posts" :key="i" class="ref-post">{{ p }}</span>
              </div>
            </li>
          </ul>
        </div>

        <div class="force-delete">
          <el-checkbox v-model="forceDelete">
            强制删除（包括被引用的图片）
          </el-checkbox>
          <p class="force-tip">强制删除后，引用该图片的文章可能会出现图片裂图。</p>
        </div>
      </template>

      <template #footer>
        <el-button @click="batchDialog = false">取消</el-button>
        <el-button type="danger" :loading="deleting" :disabled="checkingRefs" @click="confirmBatchDelete">
          确认删除
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { CopyDocument, Delete, Grid, Loading, Picture, UploadFilled, Warning } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus/es/components/message/index'
import { ElMessageBox } from 'element-plus/es/components/message-box/index'
import { batchDeleteImages, checkImageRefs, deleteImage, getImages, uploadImage } from '@/api'
import { formatSize } from '@/utils/format'

const images = ref([])
const loading = ref(false)
const deleting = ref(false)
const checkingRefs = ref(false)
const selectedUrls = ref([])
const batchDialog = ref(false)
const forceDelete = ref(false)
const refResults = ref([])

async function loadImages() {
  loading.value = true
  try {
    const list = (await getImages()) || []
    list.forEach((it) => {
      it.size_label = formatSize(it.size)
    })
    images.value = list
  } catch {
    images.value = []
  } finally {
    loading.value = false
  }
}

async function doUpload({ file }) {
  try {
    await uploadImage(file)
    ElMessage.success('上传成功')
    await loadImages()
  } catch {
    /* 错误已在拦截器提示 */
  }
}

// 选择相关
function toggleSelect(url) {
  const idx = selectedUrls.value.indexOf(url)
  if (idx > -1) {
    selectedUrls.value.splice(idx, 1)
  } else {
    selectedUrls.value.push(url)
  }
}

function selectAll() {
  if (selectedUrls.value.length === images.value.length) {
    clearSelection()
  } else {
    selectedUrls.value = images.value.map((i) => i.url)
  }
}

function clearSelection() {
  selectedUrls.value = []
}

// 复制链接
function copyUrl(url) {
  const fullUrl = window.location.origin + url
  navigator.clipboard.writeText(fullUrl).then(() => {
    ElMessage.success('链接已复制到剪贴板')
  }).catch(() => {
    ElMessage.info(url)
  })
}

// 单张删除
async function remove(img) {
  try {
    await ElMessageBox.confirm(
      `确定删除「${img.name}」吗？删除后不可恢复。`,
      '删除确认',
      {
        type: 'warning',
        confirmButtonText: '删除',
        cancelButtonText: '取消',
        confirmButtonClass: 'el-button--danger',
      }
    )
  } catch {
    return
  }
  try {
    await deleteImage(img.url)
    ElMessage.success('已删除')
    selectedUrls.value = selectedUrls.value.filter((u) => u !== img.url)
    await loadImages()
  } catch (err) {
    // 引用被阻止时，提供强制删除选项
    if (err?.msg?.includes('引用')) {
      try {
        await ElMessageBox.confirm(
          err.msg + '\n\n是否强制删除？',
          '图片被引用',
          {
            type: 'warning',
            confirmButtonText: '强制删除',
            cancelButtonText: '取消',
            confirmButtonClass: 'el-button--danger',
          }
        )
      } catch {
        return
      }
      try {
        await deleteImage(img.url, true)
        ElMessage.success('已强制删除')
        selectedUrls.value = selectedUrls.value.filter((u) => u !== img.url)
        await loadImages()
      } catch {
        /* 拦截器已提示 */
      }
    }
  }
}

// 批量删除
async function batchRemove() {
  if (!selectedUrls.value.length) return
  forceDelete.value = false
  refResults.value = []
  checkingRefs.value = true
  batchDialog.value = true

  try {
    const results = await checkImageRefs(selectedUrls.value)
    refResults.value = results || []
  } catch {
    refResults.value = []
  } finally {
    checkingRefs.value = false
  }
}

async function confirmBatchDelete() {
  deleting.value = true
  try {
    const res = await batchDeleteImages(selectedUrls.value, forceDelete.value)
    const data = res || {}
    const msg = res?.msg || `已删除 ${data.success || 0} 张`
    ElMessage.success(msg)

    // 有被引用跳过的提示
    if (data.skipped_refs?.length && !forceDelete.value) {
      ElMessage.info(`${data.skipped_refs.length} 张图片因被引用未删除`)
    }

    clearSelection()
    await loadImages()
    batchDialog.value = false
  } catch {
    /* 拦截器已提示 */
  } finally {
    deleting.value = false
  }
}

onMounted(loadImages)
</script>

<style scoped>
.images-admin {
  position: relative;
}

/* 页面头部 */
.page-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 18px;
  flex-wrap: wrap;
  gap: 12px;
}

.block-title {
  display: flex;
  align-items: center;
  gap: 10px;
  margin: 0;
  font-size: 17px;
  font-weight: 700;
  letter-spacing: 0.3px;
}

.block-title .dot {
  width: 10px;
  height: 10px;
  border-radius: 3px;
  background: var(--bm-gradient);
  transform: rotate(45deg);
  box-shadow: 0 3px 8px var(--bm-shadow-color);
}

.head-actions {
  display: flex;
  align-items: center;
  gap: 10px;
}

.count-chip,
.selected-chip {
  padding: 5px 14px;
  border-radius: 999px;
  font-size: 12.5px;
  font-weight: 600;
}

.count-chip {
  background: var(--bm-primary-soft);
  color: var(--bm-primary-2);
}

.selected-chip {
  background: var(--bm-accent-soft);
  color: #e07a9a;
}

.panel-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
}

.select-tip {
  font-size: 12px;
  color: var(--bm-text-mute);
}

/* 上传区 */
.upload-panel {
  margin-bottom: 16px;
}

.img-uploader :deep(.el-upload-dragger) {
  padding: 30px 12px;
  background: transparent;
  border: 1.5px dashed var(--bm-border);
  border-radius: var(--bm-radius-sm);
  transition: border-color 0.2s var(--bm-ease), background 0.2s var(--bm-ease);
}

.img-uploader :deep(.el-upload) {
  width: 100%;
}

.img-uploader:hover :deep(.el-upload-dragger) {
  border-color: var(--bm-primary);
  background: var(--bm-primary-soft);
}

.up-icon {
  font-size: 44px;
  color: var(--bm-primary);
}

.up-text {
  margin-top: 8px;
  font-size: 15px;
  font-weight: 600;
  color: var(--bm-text);
}

.up-hint {
  margin-top: 4px;
  font-size: 12.5px;
  color: var(--bm-text-mute);
}

/* 画廊网格 */
.grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 18px;
  min-height: 120px;
}

.cell {
  position: relative;
  margin: 0;
  border-radius: var(--bm-radius);
  overflow: hidden;
  background: var(--bm-card);
  border: 2px solid transparent;
  box-shadow: var(--bm-shadow-card);
  transition: all 0.25s var(--bm-ease);
  cursor: pointer;
}

.cell:hover {
  transform: translateY(-4px);
  box-shadow: var(--bm-shadow-hover);
}

.cell.selected {
  border-color: var(--bm-primary-2);
  box-shadow: 0 0 0 3px rgba(184, 146, 246, 0.2), var(--bm-shadow-hover);
  transform: translateY(-4px);
}

/* 选择框 */
.select-box {
  position: absolute;
  top: 10px;
  left: 10px;
  z-index: 3;
  width: 26px;
  height: 26px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(255, 255, 255, 0.95);
  border-radius: 8px;
  backdrop-filter: blur(8px);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
  opacity: 0;
  transition: opacity 0.2s var(--bm-ease);
}

.cell:hover .select-box,
.cell.selected .select-box {
  opacity: 1;
}

.cell :deep(.el-image),
.cell :deep(.el-image__inner) {
  width: 100%;
  height: 170px;
  display: block;
}

.img-error {
  height: 170px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--bm-text-mute);
  font-size: 13px;
  background: var(--bm-primary-soft-2, #f3eefc);
}

.meta {
  padding: 10px 12px 12px;
  display: flex;
  flex-direction: column;
  gap: 3px;
}

.meta .name {
  font-size: 13px;
  font-weight: 600;
  color: var(--bm-text);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.meta .info {
  font-size: 11.5px;
  color: var(--bm-text-mute);
}

/* 操作按钮 */
.actions {
  position: absolute;
  top: 10px;
  right: 10px;
  display: flex;
  gap: 6px;
  z-index: 2;
  opacity: 0;
  transition: opacity 0.2s var(--bm-ease);
}

.cell:hover .actions {
  opacity: 1;
}

.act-btn {
  width: 30px;
  height: 30px;
  border: none;
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.95);
  color: var(--bm-text-sub);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  backdrop-filter: blur(8px);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
  transition: all 0.2s var(--bm-ease);
  font-size: 14px;
}

.act-btn:hover {
  transform: scale(1.08);
}

.act-btn.copy:hover {
  background: var(--bm-primary-soft);
  color: var(--bm-primary-2);
}

.act-btn.del:hover {
  background: #fef0f0;
  color: #f56c6c;
}

/* 空状态 */
.empty {
  text-align: center;
  padding: 70px 0;
  color: var(--bm-text-sub);
}

.empty-icon {
  font-size: 52px;
  color: var(--bm-text-mute);
  margin-bottom: 10px;
}

.empty-tip {
  font-size: 13px;
  color: var(--bm-text-mute);
  margin-top: 4px;
}

/* 批量删除弹窗 */
.batch-dialog :deep(.el-dialog__body) {
  padding-top: 10px;
}

.checking-refs {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  padding: 30px 0;
  color: var(--bm-text-sub);
}

.loading-icon {
  font-size: 20px;
  color: var(--bm-primary-2);
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.batch-summary {
  display: flex;
  gap: 16px;
  margin-bottom: 16px;
  padding: 14px 16px;
  background: var(--bm-primary-soft);
  border-radius: 10px;
}

.summary-item {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.summary-item.danger .value {
  color: #e0525f;
}

.summary-item .label {
  font-size: 12.5px;
  color: var(--bm-text-sub);
}

.summary-item .value {
  font-size: 20px;
  font-weight: 700;
  color: var(--bm-primary-2);
}

.ref-list {
  margin-bottom: 16px;
}

.ref-title {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13.5px;
  font-weight: 600;
  color: #e6a23c;
  margin-bottom: 10px;
}

.ref-list ul {
  list-style: none;
  margin: 0;
  padding: 0;
  max-height: 180px;
  overflow-y: auto;
}

.ref-item {
  padding: 10px 12px;
  background: #fdf6ec;
  border-radius: 8px;
  margin-bottom: 6px;
}

.ref-name {
  font-size: 13px;
  font-weight: 500;
  color: var(--bm-text);
}

.ref-count {
  font-size: 12px;
  color: #e6a23c;
  margin-left: 8px;
}

.ref-posts {
  margin-top: 4px;
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
}

.ref-post {
  font-size: 11.5px;
  color: var(--bm-text-sub);
  background: rgba(230, 162, 60, 0.1);
  padding: 2px 8px;
  border-radius: 4px;
}

.force-delete {
  padding: 12px 14px;
  background: #fef0f0;
  border-radius: 10px;
  border: 1px solid #fbc4c4;
}

.force-tip {
  margin: 6px 0 0;
  font-size: 12px;
  color: #f56c6c;
  line-height: 1.5;
}

/* 深色模式 */
html.dark .cell {
  background: var(--bm-card);
}

html.dark .img-error {
  background: var(--bm-primary-soft-2);
}

html.dark .select-box,
html.dark .act-btn {
  background: rgba(30, 27, 45, 0.9);
}

html.dark .batch-summary {
  background: rgba(169, 155, 255, 0.1);
}

html.dark .ref-item {
  background: rgba(230, 162, 60, 0.1);
}

html.dark .ref-post {
  background: rgba(230, 162, 60, 0.15);
  color: var(--bm-text-sub);
}

html.dark .force-delete {
  background: rgba(245, 108, 108, 0.1);
  border-color: rgba(245, 108, 108, 0.3);
}

html.dark .force-tip {
  color: #f78989;
}

/* 响应式 */
@media (max-width: 640px) {
  .grid {
    grid-template-columns: repeat(auto-fill, minmax(140px, 1fr));
    gap: 12px;
  }

  .cell :deep(.el-image),
  .cell :deep(.el-image__inner) {
    height: 130px;
  }

  .actions {
    opacity: 1;
  }

  .select-box {
    opacity: 1;
  }
}
</style>
