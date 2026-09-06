<template>
  <div class="bm-container images-page">
    <!-- 页头 -->
    <PageHeader :icon="Picture" title="图片" />
    <p class="subtitle">这里收录了站长上传的独立图片，点击可放大查看；文章中使用的图片会随文章展示，不在此列。</p>

    <!-- 画廊（纯展示） -->
    <div v-loading="loading" class="grid">
      <figure
        v-for="img in images"
        :key="img.url"
        class="cell"
        @click="openPreview(img)"
      >
        <el-image :src="img.url" :alt="img.name" fit="cover" loading="lazy">
          <template #error>
            <div class="img-error">加载失败</div>
          </template>
        </el-image>
        <figcaption class="meta">
          <span class="name" :title="img.name">{{ img.name }}</span>
          <span class="info">{{ img.size_label }} · {{ img.uploaded_at }}</span>
        </figcaption>
      </figure>
    </div>

    <!-- 空状态 -->
    <div v-if="!loading && !images.length" class="empty">
      <el-icon class="empty-icon"><Picture /></el-icon>
      <p>还没有保存任何图片～</p>
    </div>

    <!-- 预览 -->
    <el-dialog
      v-model="previewVisible"
      :title="previewName"
      width="min(92vw, 900px)"
      align-center
      class="img-dialog"
      @closed="previewUrl = ''"
    >
      <div class="preview-wrap">
        <img v-if="previewUrl" :src="previewUrl" alt="preview" />
      </div>
      <div class="preview-foot">
        <span v-if="previewSize" class="pv-size">{{ previewSize }}</span>
        <a :href="previewUrl" target="_blank" rel="noopener" class="pv-link">新标签页打开</a>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { Picture } from '@element-plus/icons-vue'
import { getImages } from '@/api'
import { formatSize } from '@/utils/format'
import PageHeader from '@/components/PageHeader.vue'

const images = ref([])
const loading = ref(false)

const previewVisible = ref(false)
const previewUrl = ref('')
const previewName = ref('')
const previewSize = ref('')

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

function openPreview(img) {
  previewUrl.value = img.url
  previewName.value = img.name
  previewSize.value = img.size_label || formatSize(img.size)
  previewVisible.value = true
}

onMounted(loadImages)
</script>

<style scoped>
.images-page {
  padding: 12px 0 8px;
}

.subtitle {
  margin: 0 0 24px;
  color: var(--bm-text-sub);
  font-size: 14px;
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
  border: 1px solid var(--bm-border);
  box-shadow: var(--bm-shadow-card);
  cursor: pointer;
  transition: transform 0.3s var(--bm-ease-bounce), box-shadow 0.3s var(--bm-ease);
}

.cell:hover {
  transform: translateY(-6px) scale(1.01);
  box-shadow: var(--bm-shadow-hover);
}

/* 图片悬停时微缩放 */
.cell :deep(.el-image__inner) {
  transition: transform 0.4s var(--bm-ease);
}

.cell:hover :deep(.el-image__inner) {
  transform: scale(1.06);
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

/* 预览 */
.preview-wrap {
  display: flex;
  align-items: center;
  justify-content: center;
  background: #0f1117;
  border-radius: 10px;
  max-height: 70vh;
  overflow: auto;
}
.preview-wrap img {
  max-width: 100%;
  max-height: 70vh;
  display: block;
}
.preview-foot {
  display: flex;
  align-items: center;
  gap: 14px;
  margin-top: 14px;
  font-size: 13px;
  color: var(--bm-text-sub);
}
.preview-foot .pv-link {
  color: var(--bm-primary-2);
  text-decoration: none;
}
.preview-foot .pv-link:hover {
  text-decoration: underline;
}

@media (max-width: 640px) {
  .grid {
    grid-template-columns: repeat(auto-fill, minmax(140px, 1fr));
  }
}
</style>
