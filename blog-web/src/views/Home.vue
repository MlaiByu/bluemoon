<template>
  <div class="home">
    <!-- 首屏：随机背景图 + 随机一句 + 下滑进入 -->
    <HomeHero
      :site="site"
      :avatar="profile.avatar"
      :avatar-text="avatarText"
      :quote="randomQuote"
      :banner-src="bannerSrc"
      @enter="enterHome"
    />

    <!-- 主页内容（两栏：侧边栏 + 文章卡片流） -->
    <div id="posts" class="container">
      <HomeSidebar
        :site="site"
        :avatar="profile.avatar"
        :avatar-text="avatarText"
        :categories="categories"
        :cat="cat"
        @select-cat="selectCat"
      />

      <main class="main">
        <div class="main-head">
          <h1>{{ headTitle }}</h1>
          <span class="count">{{ posts.length }} 篇</span>
        </div>

        <transition-group name="card" tag="div" class="grid" v-loading="loading">
          <article
            v-for="(p, i) in posts"
            :key="p.id"
            class="card"
            :style="{ animationDelay: `${i * 0.06}s` }"
            @click="goPost(p)"
          >
            <div class="cover-wrap" :class="{ 'cover-empty': !p.cover && !pickCover(p) }">
              <img
                v-if="p.cover || pickCover(p)"
                class="cover"
                :src="p.cover || pickCover(p)"
                :alt="p.title"
                loading="lazy"
                decoding="async"
              />
              <span v-else class="cover-placeholder">🌙</span>
              <span class="cat-chip">{{ p.category?.name || '未分类' }}</span>
            </div>

            <div class="body">
              <h2>{{ p.title }}</h2>
              <div class="meta">
                <span>📅 {{ formatDate(p.published_at || p.created_at) }}</span>
                <span>⏱ {{ readingMinutes(p.word_count) }} 分钟阅读</span>
                <span>👁 {{ p.views || 0 }}</span>
              </div>
              <p class="summary">{{ p.summary || '（暂无摘要）' }}</p>
              <span class="read-more">阅读全文</span>
            </div>
          </article>
        </transition-group>

        <EmptyState
          v-if="!loading && !posts.length"
          emoji="🌙"
          text="这里还没有相关文章～"
        />
      </main>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import HomeHero from '@/components/HomeHero.vue'
import HomeSidebar from '@/components/HomeSidebar.vue'
import EmptyState from '@/components/EmptyState.vue'
import { getPosts, getImages } from '@/api'
import { formatDate, readingMinutes } from '@/utils/format'
import { useSiteStore } from '@/stores/site'

const route = useRoute()
const router = useRouter()
const siteStore = useSiteStore()

const site = computed(() => siteStore.site || {})
const profile = computed(() => siteStore.profile || {})
const categories = computed(() => siteStore.categories || [])
const tags = computed(() => siteStore.tags || [])
const posts = ref([])
const loading = ref(false)

const cat = ref('all') // 分类 id 或 'all'
const keyword = ref(route.query.q || '')

const avatarText = computed(() => {
  const name = profile.value.nickname || site.value.title || 'B'
  return name.charAt(0).toUpperCase()
})

/* 用户上传的图片库，用于 banner 和文章封面回退 */
const gallery = ref([])

/* 首屏 banner：优先 site.banner → 用户图片库随机一张 → 渐变回退 */
const bannerSrc = computed(() => {
  if (site.value.banner) return site.value.banner
  if (gallery.value.length) {
    return gallery.value[Math.floor(Math.random() * gallery.value.length)].url
  }
  return ''
})

// 随机一句：每次进入随机取一条，不轮播
const QUOTES = [
  '种一棵树最好的时间是十年前，其次是现在。',
  '代码如诗，bug 如歌，调试是修行。',
  '保持好奇，比保持正确更重要。',
  '你写的每一行注释，都是在拯救未来的自己。',
  '简单是可靠的先决条件。',
  '不要为了炫技而复杂化，克制是一种能力。',
  '今天也要开心地写 bug～',
  '读源码比读文档更接近真相。',
  '把时间花在值得的事情上，包括好好生活。',
]
const randomQuote = ref(QUOTES[Math.floor(Math.random() * QUOTES.length)])

const headTitle = computed(() => {
  if (keyword.value) return `“${keyword.value}” 的搜索结果`
  if (cat.value !== 'all') {
    const c = categories.value.find((x) => x.id === cat.value)
    return c ? c.name : '全部文章'
  }
  return '全部文章'
})

/** 平滑滚动到文章区 */
function enterHome() {
  document.getElementById('posts')?.scrollIntoView({ behavior: 'smooth', block: 'start' })
}

function selectCat(id) {
  cat.value = id
  fetchPosts()
}

async function fetchPosts() {
  loading.value = true
  try {
    const params = { page_size: 50 }
    if (keyword.value) params.keyword = keyword.value
    else if (cat.value !== 'all') params.category_id = cat.value
    posts.value = (await getPosts(params)).list || []
  } finally {
    loading.value = false
  }
}

const goPost = (p) => router.push({ name: 'post', params: { slug: p.slug } })

/* 从用户图片库中按文章 ID 稳定取一张作为封面回退 */
function pickCover(post) {
  if (!gallery.value.length) return ''
  const idx = (post.id || 0) % gallery.value.length
  return gallery.value[idx].url
}

onMounted(async () => {
  // 站点信息从 store 统一加载，保证全站数据一致
  await siteStore.load()
  // 图片库仅首页使用，单独加载
  try {
    gallery.value = (await getImages()) || []
  } catch {
    gallery.value = []
  }
  fetchPosts()
})

// 顶部搜索框跳转 /search?q= 时同步过滤
watch(
  () => route.query.q,
  (q) => {
    keyword.value = q || ''
    fetchPosts()
  }
)
</script>

<style scoped>
/* 主页内容容器（首屏与侧边栏样式已抽到 HomeHero / HomeSidebar） */
.container {
  max-width: 1280px;
  margin: 0 auto;
  padding: 32px 24px;
  display: flex;
  gap: 28px;
  align-items: flex-start;
}

.main {
  flex: 1 1 80%;
  min-width: 0;
  /* 透明主体：顶部与 Hero 的渐变羽化衔接（保持页脚间距） */
  background: linear-gradient(
    to bottom,
    transparent 0%,
    rgba(255, 255, 255, 0.55) 28px,
    var(--bm-bg) 96px
  );
  border-radius: var(--bm-radius);
  padding: 26px;
}

.main-head {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  margin-bottom: 20px;
  padding: 0 4px;
}

.main-head h1 {
  font-size: 19px;
  font-weight: 800;
}

.main-head .count {
  font-size: 13px;
  color: var(--bm-text-sub);
  background: var(--bm-primary-soft);
  padding: 2px 12px;
  border-radius: 999px;
}

.grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
  gap: 22px;
  min-height: 200px;
}

/* 分类/标签筛选切换时的淡入动画 */
.card-enter-active,
.card-leave-active {
  transition: opacity 0.35s var(--bm-ease), transform 0.35s var(--bm-ease);
}

.card-enter-from,
.card-leave-to {
  opacity: 0;
  transform: translateY(16px) scale(0.97);
}

.card {
  background: var(--bm-card);
  border-radius: var(--bm-radius);
  overflow: hidden;
  box-shadow: var(--bm-shadow-card);
  border: 1px solid var(--bm-border);
  transition: transform 0.3s var(--bm-ease-bounce), box-shadow 0.3s var(--bm-ease),
    border-color 0.3s var(--bm-ease);
  display: flex;
  flex-direction: column;
  cursor: pointer;
  position: relative;
  animation: bm-fade-up 0.5s var(--bm-ease) backwards;
}

/* 悬停时卡片顶部渐变光带 */
.card::after {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 3px;
  background: var(--bm-gradient);
  opacity: 0;
  transition: opacity 0.3s var(--bm-ease);
  z-index: 3;
}

.card:hover {
  transform: translateY(-7px);
  box-shadow: var(--bm-shadow-hover);
  border-color: transparent;
}

.card:hover::after {
  opacity: 1;
}

.cover-wrap {
  position: relative;
}

/* 无封面时的渐变背景 + emoji 占位 */
.cover-empty {
  background: var(--bm-gradient-soft);
  display: flex;
  align-items: center;
  justify-content: center;
}

.cover-placeholder {
  font-size: 48px;
  opacity: 0.4;
  animation: bm-fade-in 0.6s var(--bm-ease) backwards;
}

.card .cover {
  width: 100%;
  aspect-ratio: 16 / 9;
  object-fit: cover;
  display: block;
  transition: transform 0.5s var(--bm-ease);
}

.card:hover .cover {
  transform: scale(1.08);
}

/* 封面底部渐变，保证分类 chip 始终清晰 */
.cover-wrap::after {
  content: '';
  position: absolute;
  left: 0;
  right: 0;
  bottom: 0;
  height: 48%;
  background: linear-gradient(to top, rgba(40, 30, 60, 0.35), transparent);
  pointer-events: none;
}

.cat-chip {
  position: absolute;
  left: 12px;
  bottom: 12px;
  z-index: 2;
  font-size: 11.5px;
  font-weight: 700;
  letter-spacing: 0.5px;
  padding: 3px 12px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.92);
  color: var(--bm-primary-2);
  backdrop-filter: blur(4px);
}

.card .body {
  padding: 18px 20px 20px;
}

.card h2 {
  font-size: 17px;
  font-weight: 700;
  line-height: 1.5;
  margin-bottom: 8px;
}

.card .meta {
  font-size: 12.5px;
  color: var(--bm-text-sub);
  display: flex;
  gap: 12px;
  margin-bottom: 10px;
  flex-wrap: wrap;
}

.card .summary {
  font-size: 13.5px;
  color: var(--bm-text-sub);
  line-height: 1.7;
  margin-bottom: 14px;
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.card .read-more {
  font-size: 13.5px;
  font-weight: 700;
  background: var(--bm-gradient);
  -webkit-background-clip: text;
  background-clip: text;
  -webkit-text-fill-color: transparent;
  display: inline-flex;
  align-items: center;
  gap: 4px;
}

.card .read-more::after {
  content: '→';
  transition: transform 0.2s var(--bm-ease);
}

.card:hover .read-more::after {
  transform: translateX(4px);
}

html.dark .main {
  background: linear-gradient(
    to bottom,
    transparent 0%,
    rgba(20, 18, 31, 0.55) 28px,
    var(--bm-bg) 96px
  );
}

html.dark .card {
  background: var(--bm-card);
}

@media (max-width: 900px) {
  .container {
    flex-direction: column;
  }
  .main {
    flex: none;
    width: 100%;
  }
}

@media (max-width: 640px) {
  .grid {
    grid-template-columns: 1fr;
  }
  .main {
    padding: 18px;
  }
}
</style>
