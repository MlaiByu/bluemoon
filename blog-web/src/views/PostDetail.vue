<template>
  <div class="detail" v-loading="loading">
    <div class="bm-container bm-layout">
    <div class="bm-layout-main content">
      <article v-if="post" class="bm-card article">
        <div v-if="post.cover" class="hero">
          <img
            :src="coverThumb"
            :data-original="coverUrl"
            :alt="post.title"
            decoding="async"
            @error="onImageError"
          />
        </div>

        <header class="article-head">
          <div class="badges">
            <el-tag v-if="post.is_top" type="danger" size="small" effect="light" round>置顶</el-tag>
            <el-tag v-if="post.status === 0" type="warning" size="small" effect="light" round>草稿</el-tag>
          </div>
          <h1 class="title">{{ post.title }}</h1>
          <div class="meta">
            <span v-if="post.category"><el-icon><Folder /></el-icon>{{ post.category.name }}</span>
            <span><el-icon><Calendar /></el-icon>{{ formatDate(post.published_at || post.created_at, 'YYYY-MM-DD', '-') }}</span>
            <span><el-icon><View /></el-icon>{{ post.views }} 次阅读</span>
            <span><el-icon><EditPen /></el-icon>{{ post.word_count }} 字</span>
          </div>

          <!-- 作者信息 -->
          <div v-if="post.author" class="author-bar">
            <el-avatar :size="44" :src="authorAvatar" class="author-avatar">
              {{ authorName.slice(0, 1).toUpperCase() }}
            </el-avatar>
            <div class="author-info">
              <span class="author-name">{{ authorName }}</span>
              <span class="author-label">作者</span>
            </div>
          </div>
        </header>

        <MarkdownView :content="post.content" class="content-md" />

        <footer class="article-foot">
          <p class="updated">最后更新：{{ formatDate(post.updated_at, 'YYYY-MM-DD HH:mm', '-') }}</p>
          <div class="nav-posts">
            <router-link
              v-if="neighbors.prev"
              class="nav-card"
              :to="{ name: 'post', params: { slug: neighbors.prev.slug } }"
            >
              <span class="label">← 上一篇</span>
              <span class="t">{{ neighbors.prev.title }}</span>
            </router-link>
            <span v-else class="nav-card disabled">
              <span class="label">← 上一篇</span><span class="t">没有了</span>
            </span>
            <router-link
              v-if="neighbors.next"
              class="nav-card right"
              :to="{ name: 'post', params: { slug: neighbors.next.slug } }"
            >
              <span class="label">下一篇 →</span>
              <span class="t">{{ neighbors.next.title }}</span>
            </router-link>
            <span v-else class="nav-card right disabled">
              <span class="label">下一篇 →</span><span class="t">没有了</span>
            </span>
          </div>
        </footer>
      </article>

      <el-empty v-else-if="!loading" description="文章不存在或已删除">
        <el-button type="primary" @click="$router.push('/')">回到首页</el-button>
      </el-empty>
    </div>

    <SidePanel
      :site="siteStore.site"
      :profile="siteStore.profile"
      :categories="siteStore.categories"
      :hot-posts="siteStore.hotPosts"
    />
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import MarkdownView from '@/components/MarkdownView.vue'
import SidePanel from '@/components/SidePanel.vue'
import { getPostBySlug } from '@/api'
import { formatDate, onImageError, resolveImageUrl, resolveImageVariant } from '@/utils/format'
import { useSiteStore } from '@/stores/site'
import { useReadingTimer } from '@/composables/useReadingTimer'
import { applyPostSeo } from '@/composables/useSeo'

const route = useRoute()
const siteStore = useSiteStore()

const post = ref(null)
const neighbors = ref({ prev: null, next: null })
const loading = ref(false)

// 作者头像统一从 siteStore 取，保证与全站头像一致
const authorAvatar = computed(() => siteStore.avatar || post.value?.author?.avatar || '')
const coverUrl = computed(() => resolveImageUrl(post.value?.cover))
/* 文章头图是大图：走 1024 档，原图作为 onerror 兜底 */
const coverThumb = computed(() => resolveImageVariant(post.value?.cover, 1024))
const authorName = computed(() =>
  post.value?.author?.nickname || post.value?.author?.username || siteStore.nickname || 'B'
)

// 文章 ID 引用（用于阅读计时器）
const postId = computed(() => post.value?.id || null)

// 有效阅读统计：进入文章并持续阅读满 5 秒计一次，后端按 IP 去重
const { views: reportedViews } = useReadingTimer(postId)

// 上报成功后用服务端返回的最新阅读数校准展示，避免页面数字落后于真实值
watch(reportedViews, (v) => {
  if (typeof v === 'number' && post.value) post.value.views = v
})

async function fetchPost() {
  loading.value = true
  try {
    const res = await getPostBySlug(route.params.slug)
    post.value = res
    neighbors.value = res.neighbors || { prev: null, next: null }
    // SEO：title / description / OG / canonical 统一走 useSeo，与路由守卫的 setTitle
    // 收敛到同一出口（此前 document.title 在 router 与本文件两处分别赋值）
    applyPostSeo(res, { site: siteStore.site, resolveImage: resolveImageUrl })
  } catch {
    post.value = null
  } finally {
    loading.value = false
  }
}

onMounted(async () => {
  await siteStore.load()
  fetchPost()
})

watch(() => route.params.slug, fetchPost)
</script>

<style scoped>
.detail {
  position: relative;
}

/* .bm-layout 由 layout-common.css 提供 */
.bm-container.bm-layout {
  position: relative;
  z-index: 1;
}

.article {
  padding: 0 0 26px;
  overflow: hidden;
}

.hero {
  height: 300px;
  overflow: hidden;
  background: var(--bm-gradient-soft);
  position: relative;
}

.hero img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
  transition: transform 8s ease;
}

/* 封面底部渐变遮罩，让标题区过渡更自然 */
.hero::after {
  content: '';
  position: absolute;
  left: 0;
  right: 0;
  bottom: 0;
  height: 60%;
  background: linear-gradient(to top, var(--bm-card) 0%, transparent 100%);
}

.article-head {
  padding: 28px 38px 20px;
  text-align: center;
  border-bottom: 1px solid var(--bm-border);
}

.badges {
  margin-bottom: 12px;
  min-height: 22px;
}

.title {
  margin: 6px 0 16px;
  font-size: 28px;
  font-weight: 800;
  line-height: 1.4;
  letter-spacing: 0.5px;
  animation: bm-fade-up 0.5s var(--bm-ease) backwards;
}

.meta {
  display: flex;
  justify-content: center;
  flex-wrap: wrap;
  gap: 20px;
  font-size: 13.5px;
  color: var(--bm-text-sub);
}

.meta span {
  display: inline-flex;
  align-items: center;
}

.meta .el-icon {
  margin-right: 5px;
  color: var(--bm-primary-2);
}

.author-bar {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  margin-top: 18px;
  padding: 12px 18px;
  background: linear-gradient(135deg, rgba(138, 182, 255, 0.08) 0%, rgba(255, 176, 200, 0.08) 100%);
  border: 1px solid var(--bm-border);
  border-radius: var(--bm-radius-sm);
}

.author-avatar {
  background: var(--bm-gradient) !important;
  font-weight: 700;
  color: #fff !important;
  box-shadow: 0 4px 12px var(--bm-shadow-color);
  transition: transform 0.3s var(--bm-ease-bounce);
}

.author-bar:hover .author-avatar {
  transform: scale(1.08);
}

.author-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.author-name {
  font-size: 14.5px;
  font-weight: 700;
  color: var(--bm-text);
}

.author-label {
  font-size: 11px;
  color: var(--bm-text-mute);
  letter-spacing: 1px;
}

.content-md {
  padding: 14px 38px 4px;
}

.article-foot {
  margin-top: 26px;
  padding: 20px 38px 0;
  border-top: 1px solid var(--bm-border);
}

.updated {
  margin: 0 0 16px;
  font-size: 13px;
  color: var(--bm-text-sub);
  text-align: right;
}

.nav-posts {
  display: flex;
  gap: 14px;
}

.nav-card {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 6px;
  padding: 16px 20px;
  border-radius: var(--bm-radius-sm);
  background: var(--bm-primary-soft);
  border: 1px solid var(--bm-border);
  cursor: pointer;
  transition: all 0.25s var(--bm-ease-bounce);
  position: relative;
  overflow: hidden;
}

/* 导航卡片顶部渐变线 */
.nav-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 2px;
  background: var(--bm-gradient);
  opacity: 0;
  transition: opacity 0.25s var(--bm-ease);
}

.nav-card:hover {
  background: var(--bm-card);
  border-color: transparent;
  transform: translateY(-3px);
  box-shadow: var(--bm-shadow-hover);
  /* 卡片现为 <a>：不加这条会被全局 a:hover 的紫色字色带跑（.t 未单独设色） */
  color: var(--bm-text);
}

.nav-card:hover::before {
  opacity: 1;
}

.nav-card.right {
  text-align: right;
  align-items: flex-end;
}

.nav-card.disabled {
  cursor: default;
  opacity: 0.5;
}

.nav-card.disabled:hover {
  /* 用令牌承接 disabled 的「退后」背景：明暗自动适配，
     避免硬编码 #f7f8fc 在暗色下因特异性压过 html.dark .nav-card:hover 而闪白块 */
  background: var(--bm-primary-soft);
  border-color: var(--bm-border);
  transform: none;
  box-shadow: none;
}

.nav-card .label {
  font-size: 12px;
  color: var(--bm-text-sub);
}

.nav-card .t {
  font-size: 14.5px;
  font-weight: 600;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  max-width: 100%;
}

@media (max-width: 900px) {
  .layout {
    flex-direction: column;
  }
  .article-head,
  .content-md,
  .article-foot {
    padding-left: 20px;
    padding-right: 20px;
  }
  .hero {
    height: 180px;
  }
  .title {
    font-size: 23px;
  }
  .nav-posts {
    flex-direction: column;
  }
}

/* 深色模式适配 */
html.dark .nav-card {
  background: #20242f;
}

html.dark .nav-card:hover {
  background: #262b38;
}
</style>
