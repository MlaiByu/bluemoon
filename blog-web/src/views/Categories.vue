<template>
  <div class="bm-container layout">
    <div class="content bm-card" v-loading="loading">
      <PageHeader :icon="Folder" title="分类" />

      <div class="cat-grid">
        <div
          v-for="c in categories"
          :key="c.id"
          class="cat-card"
          :class="{ active: activeId === c.id }"
          @click="pick(c)"
        >
          <span class="cat-bar"></span>
          <div class="cat-head">
            <span class="cat-name">{{ c.name }}</span>
            <span class="cat-count">{{ c.post_count }}</span>
          </div>
          <p class="cat-desc">{{ c.description || '暂无描述' }}</p>
        </div>
      </div>

      <el-empty v-if="!loading && !categories.length" description="暂无分类" />

      <template v-if="activeId">
        <div class="split">
          <h3 class="bm-subtitle">“{{ activeName }}” 下的文章</h3>
          <el-button v-if="activeId" link type="primary" @click="clear">查看全部</el-button>
        </div>
        <div v-loading="listLoading">
          <PostCard v-for="p in posts" :key="p.id" :post="p" />
          <el-empty v-if="!listLoading && !posts.length" description="该分类下暂无文章" />
        </div>
        <div v-if="total > pageSize" class="pager">
          <el-pagination
            v-model:current-page="page"
            :page-size="pageSize"
            :total="total"
            layout="prev, pager, next"
            background
            @current-change="fetchPosts"
          />
        </div>
      </template>
    </div>

    <SidePanel
      :site="siteStore.site"
      :profile="siteStore.profile"
      :categories="siteStore.categories"
      :hot-posts="siteStore.hotPosts"
    />
  </div>
</template>

<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Folder } from '@element-plus/icons-vue'
import PostCard from '@/components/PostCard.vue'
import SidePanel from '@/components/SidePanel.vue'
import PageHeader from '@/components/PageHeader.vue'
import { getPosts } from '@/api'
import { useSiteStore } from '@/stores/site'

const route = useRoute()
const router = useRouter()
const siteStore = useSiteStore()

const categories = computed(() => siteStore.categories || [])
const loading = ref(false)
const listLoading = ref(false)

const activeId = ref(null)
const activeName = computed(
  () => categories.value.find((c) => c.id === activeId.value)?.name || ''
)

const posts = ref([])
const total = ref(0)
const page = ref(1)
const pageSize = 10

async function fetchPosts() {
  listLoading.value = true
  try {
    const res = await getPosts({
      page: page.value,
      page_size: pageSize,
      category_id: activeId.value || undefined,
    })
    posts.value = res.list || []
    total.value = res.total || 0
  } finally {
    listLoading.value = false
  }
}

function pick(c) {
  activeId.value = c.id
  page.value = 1
  router.replace({ query: { cat: c.id } })
  fetchPosts()
}

function clear() {
  activeId.value = null
  posts.value = []
  router.replace({ query: {} })
}

onMounted(async () => {
  loading.value = true
  await siteStore.load()
  loading.value = false

  const cat = Number(route.query.cat)
  if (cat && categories.value.some((c) => c.id === cat)) {
    activeId.value = cat
    fetchPosts()
  }
})

watch(
  () => route.query.cat,
  (v) => {
    const id = Number(v)
    if (id && id !== activeId.value) {
      activeId.value = id
      page.value = 1
      fetchPosts()
    }
  }
)
</script>

<style scoped>
.layout {
  display: flex;
  gap: 20px;
  align-items: flex-start;
}

.content {
  flex: 1;
  min-width: 0;
  padding: 28px 32px;
}

.cat-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(230px, 1fr));
  gap: 16px;
}

.cat-card {
  position: relative;
  padding: 18px 18px 16px;
  border: 1px solid var(--bm-border);
  border-radius: var(--bm-radius);
  background: var(--bm-card);
  cursor: pointer;
  overflow: hidden;
  transition: transform 0.3s var(--bm-ease-bounce), box-shadow 0.3s var(--bm-ease),
    border-color 0.3s var(--bm-ease);
}

.cat-card:hover {
  transform: translateY(-6px);
  border-color: transparent;
  box-shadow: var(--bm-shadow-hover);
}

.cat-bar {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 3px;
  background: var(--bm-gradient);
  transform: scaleX(0);
  transform-origin: left;
  transition: transform 0.25s;
}

.cat-card:hover .cat-bar,
.cat-card.active .cat-bar {
  transform: scaleX(1);
}

.cat-card.active {
  border-color: var(--bm-primary);
  background: var(--bm-primary-soft);
}

.cat-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
}

.cat-name {
  font-size: 16px;
  font-weight: 700;
}

.cat-count {
  flex-shrink: 0;
  font-size: 12px;
  font-weight: 700;
  color: #fff;
  background: var(--bm-gradient);
  border-radius: 10px;
  padding: 1px 10px;
}

.cat-card.active .cat-count {
  background: var(--bm-primary-2);
}

.cat-desc {
  margin: 8px 0 0;
  font-size: 13px;
  color: var(--bm-text-sub);
  line-height: 1.6;
}

.split {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin: 28px 0 16px;
  padding-top: 22px;
  border-top: 1px solid var(--bm-border);
}

.pager {
  display: flex;
  justify-content: center;
  padding-top: 8px;
}

@media (max-width: 900px) {
  .layout {
    flex-direction: column;
  }
  .content {
    padding: 20px 16px;
  }
}
</style>
