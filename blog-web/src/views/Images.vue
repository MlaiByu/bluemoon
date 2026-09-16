<template>
  <div class="bm-container images-page">
    <!-- 页头 -->
    <PageHeader :icon="Picture" title="光影相册" />
    <p class="subtitle">
      这里收录站长上传的独立图片，悬停聚焦查看光影，点击放大可左右切换；文章中使用的图片随文章展示，不在此列。
    </p>

    <!-- 光影相册：数据获取与展示分离，组件内部负责入场 / 聚焦 / 灯箱 -->
    <LightShadowGallery v-loading="loading" :images="galleryItems" class="gallery" />

    <p v-if="!loading && !galleryItems.length" class="sample-note">
      （当前为示例占位图片，上传图片后将自动替换为真实相册内容）
    </p>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { Picture } from '@element-plus/icons-vue'
import { getImages } from '@/api'
import { formatSize } from '@/utils/format'
import LightShadowGallery from '@/components/LightShadowGallery.vue'
import PageHeader from '@/components/PageHeader.vue'

const images = ref([])
const loading = ref(false)

/* 把接口字段映射成相册组件统一形态，展示与数据解耦 */
const galleryItems = computed(() =>
  images.value.map((it) => ({
    url: it.url,
    title: it.name,
    desc: [it.size_label, it.uploaded_at].filter(Boolean).join(' · '),
  }))
)

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

.gallery {
  min-height: 160px;
}

.sample-note {
  margin-top: 18px;
  text-align: center;
  color: var(--bm-text-mute);
  font-size: 12.5px;
}
</style>
