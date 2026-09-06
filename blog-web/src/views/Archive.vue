<template>
  <div class="bm-container layout" v-loading="loading">
    <div class="content bm-card archive">
      <PageHeader :icon="Collection" title="文章归档" :count="`共 ${total} 篇`" />

      <section v-for="g in groups" :key="`${g.year}-${g.month}`" class="group">
        <h3 class="month">
          <span class="y bm-gradient-text">{{ g.year }}</span> 年 {{ String(g.month).padStart(2, '0') }} 月
          <em>{{ g.count }} 篇</em>
        </h3>
        <ul class="posts">
          <li v-for="p in g.posts" :key="p.id">
            <span class="day">{{ formatDay(p.published_at || p.created_at) }}</span>
            <a class="t" @click="go(p)">{{ p.title }}</a>
            <span class="cat" v-if="p.category">{{ p.category.name }}</span>
          </li>
        </ul>
      </section>

      <el-empty v-if="!loading && !groups.length" description="暂无文章" />
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
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { Collection } from '@element-plus/icons-vue'
import SidePanel from '@/components/SidePanel.vue'
import PageHeader from '@/components/PageHeader.vue'
import { getArchives } from '@/api'
import { formatDay } from '@/utils/format'
import { useSiteStore } from '@/stores/site'

const router = useRouter()
const siteStore = useSiteStore()

const groups = ref([])
const loading = ref(false)

const total = computed(() => groups.value.reduce((s, g) => s + g.count, 0))
const go = (p) => router.push({ name: 'post', params: { slug: p.slug } })

onMounted(async () => {
  await siteStore.load()
  loading.value = true
  try {
    groups.value = (await getArchives()) || []
  } finally {
    loading.value = false
  }
})
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
}

.archive {
  padding: 28px 32px;
}

.group {
  margin-bottom: 28px;
}

.month {
  display: flex;
  align-items: baseline;
  gap: 4px;
  margin: 0 0 14px;
  font-size: 17px;
  color: var(--bm-text);
}

.month .y {
  font-size: 23px;
  font-weight: 800;
}

.month em {
  margin-left: 8px;
  font-size: 12px;
  font-style: normal;
  color: var(--bm-text-sub);
}

.posts {
  list-style: none;
  margin: 0;
  padding: 0 0 0 8px;
  border-left: 2px solid var(--bm-border);
}

.posts li {
  position: relative;
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 9px 0 9px 20px;
  font-size: 14.5px;
  border-radius: 8px;
  transition: background 0.2s;
}

.posts li:hover {
  background: var(--bm-primary-soft);
}

.posts li::before {
  content: '';
  position: absolute;
  left: -6px;
  top: 50%;
  width: 9px;
  height: 9px;
  margin-top: -4.5px;
  border-radius: 50%;
  background: #ded8f2;
  border: 2px solid var(--bm-card);
  transition: background 0.25s var(--bm-ease), box-shadow 0.25s var(--bm-ease),
    transform 0.25s var(--bm-ease-bounce);
}

.posts li:hover::before {
  background: var(--bm-accent);
  box-shadow: 0 0 0 5px var(--bm-accent-soft);
  transform: scale(1.25);
}

.day {
  flex-shrink: 0;
  font-size: 12.5px;
  color: var(--bm-text-sub);
  font-variant-numeric: tabular-nums;
  width: 40px;
}

.t {
  flex: 1;
  min-width: 0;
  cursor: pointer;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.t:hover {
  color: var(--bm-primary-2);
}

.cat {
  flex-shrink: 0;
  font-size: 12px;
  color: var(--bm-primary-2);
  background: var(--bm-primary-soft);
  border-radius: 10px;
  padding: 1px 9px;
}

@media (max-width: 900px) {
  .layout {
    flex-direction: column;
  }
  .archive {
    padding: 20px 16px;
  }
}
</style>
