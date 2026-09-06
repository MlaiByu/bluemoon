<template>
  <div class="posts-admin bm-fade-up">
    <div class="bm-card panel">
      <!-- 标题 + 筛选栏 -->
      <div class="panel-head">
        <h3 class="block-title"><i class="dot"></i>文章管理</h3>
        <div class="head-stats">
          <span class="stat-chip">共 {{ total }} 篇</span>
        </div>
      </div>

      <div class="filters">
        <el-input
          v-model="filters.keyword"
          placeholder="搜索标题 / 内容"
          clearable
          style="width: 240px"
          @keyup.enter="reload"
          @clear="reload"
        >
          <template #prefix><el-icon><Search /></el-icon></template>
        </el-input>

        <el-select v-model="filters.status" placeholder="状态" clearable style="width: 130px" @change="reload">
          <el-option label="已发布" :value="1" />
          <el-option label="草稿" :value="0" />
        </el-select>

        <el-select v-model="filters.category_id" placeholder="分类" clearable filterable style="width: 160px" @change="reload">
          <el-option v-for="c in categories" :key="c.id" :label="c.name" :value="c.id" />
        </el-select>

        <el-button :icon="Refresh" @click="reload">刷新</el-button>
        <div class="spacer"></div>
        <el-button type="primary" :icon="EditPen" @click="$router.push('/admin/posts/new')">写文章</el-button>
      </div>

      <!-- 表格 -->
      <el-table v-loading="loading" :data="posts" stripe class="posts-table">
        <el-table-column prop="title" label="标题" min-width="300" show-overflow-tooltip>
          <template #default="{ row }">
            <div class="title-cell">
              <div class="title-badges">
                <el-tag v-if="row.is_top" type="danger" size="small" effect="light" round>置顶</el-tag>
                <el-tag v-if="row.status === 0" size="small" effect="plain" round>草稿</el-tag>
              </div>
              <span class="title-text">{{ row.title }}</span>
            </div>
          </template>
        </el-table-column>

        <el-table-column label="分类" width="120">
          <template #default="{ row }">
            <span class="cat-chip">{{ row.category?.name || '-' }}</span>
          </template>
        </el-table-column>

        <el-table-column prop="views" label="阅读" width="90" align="right">
          <template #default="{ row }">
            <span class="view-num">
              <el-icon size="12"><View /></el-icon>
              {{ row.views }}
            </span>
          </template>
        </el-table-column>

        <el-table-column prop="word_count" label="字数" width="90" align="right" />

        <el-table-column label="发布时间" width="160">
          <template #default="{ row }">
            <span class="date-text">{{ row.published_at ? formatDateTime(row.published_at) : '—' }}</span>
          </template>
        </el-table-column>

        <el-table-column label="操作" width="200" fixed="right" align="center">
          <template #default="{ row }">
            <div class="action-btns">
              <el-button link type="primary" size="small" @click="edit(row.id)">
                <el-icon><Edit /></el-icon>
                编辑
              </el-button>
              <el-button link type="info" size="small" @click="preview(row)">
                <el-icon><View /></el-icon>
                查看
              </el-button>
              <el-button link type="danger" size="small" @click="remove(row)">
                <el-icon><Delete /></el-icon>
                删除
              </el-button>
            </div>
          </template>
        </el-table-column>
      </el-table>

      <div class="pager">
        <el-pagination
          v-model:current-page="page"
          :page-size="pageSize"
          :total="total"
          layout="total, prev, pager, next"
          background
          @current-change="fetchPosts"
        />
      </div>
    </div>
  </div>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Delete, Edit, EditPen, Refresh, Search, View } from '@element-plus/icons-vue'
import { deletePost, getAdminPosts, getCategories } from '@/api'
import { formatDateTime } from '@/utils/format'

const router = useRouter()
const posts = ref([])
const categories = ref([])
const total = ref(0)
const page = ref(1)
const pageSize = 10
const loading = ref(false)

const filters = reactive({
  keyword: '',
  status: null,
  category_id: null,
})

async function fetchPosts() {
  loading.value = true
  try {
    const res = await getAdminPosts({
      page: page.value,
      page_size: pageSize,
      keyword: filters.keyword || undefined,
      status: filters.status,
      category_id: filters.category_id || undefined,
    })
    posts.value = res.list || []
    total.value = res.total || 0
  } finally {
    loading.value = false
  }
}

function reload() {
  page.value = 1
  fetchPosts()
}

const edit = (id) => router.push(`/admin/posts/${id}`)
const preview = (row) => {
  if (row.status === 0) {
    ElMessage.info('草稿文章，前台不可见')
    return
  }
  router.push({ name: 'post', params: { slug: row.slug } })
}

async function remove(row) {
  try {
    await ElMessageBox.confirm(`确定删除《${row.title}》？该操作不可恢复。`, '删除确认', {
      type: 'warning',
      confirmButtonText: '删除',
      confirmButtonClass: 'el-button--danger',
    })
  } catch {
    return
  }
  try {
    await deletePost(row.id)
    ElMessage.success('已删除')
    if (posts.value.length === 1 && page.value > 1) page.value -= 1
    fetchPosts()
  } catch {
    /* 拦截器已提示 */
  }
}

onMounted(async () => {
  fetchPosts()
  categories.value = (await getCategories()) || []
})
</script>

<style scoped>
.posts-admin {
  position: relative;
}

/* 面板头部 */
.panel-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
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

.head-stats {
  display: flex;
  gap: 8px;
}

.stat-chip {
  padding: 5px 14px;
  background: var(--bm-primary-soft);
  color: var(--bm-primary-2);
  border-radius: 999px;
  font-size: 12.5px;
  font-weight: 600;
}

/* 筛选栏 */
.filters {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 12px;
  margin-bottom: 18px;
  padding: 16px 18px;
  background: linear-gradient(135deg, rgba(138, 182, 255, 0.06) 0%, rgba(255, 176, 200, 0.06) 100%);
  border-radius: var(--bm-radius-sm);
  border: 1px solid var(--bm-border);
}

.filters .spacer {
  flex: 1;
}

/* 表格 */
.posts-table {
  border-radius: var(--bm-radius-sm);
  overflow: hidden;
}

.title-cell {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.title-badges {
  display: flex;
  gap: 6px;
}

.title-text {
  font-weight: 500;
  color: var(--bm-text);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.cat-chip {
  display: inline-block;
  padding: 3px 10px;
  background: var(--bm-primary-soft-2);
  color: var(--bm-primary-2);
  border-radius: 999px;
  font-size: 12.5px;
  font-weight: 500;
}

.view-num {
  color: var(--bm-text-mute);
  font-size: 13px;
}

.view-num {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-weight: 600;
  color: var(--bm-primary-2);
  font-size: 13px;
}

.date-text {
  color: var(--bm-text-sub);
  font-size: 13px;
}

/* 操作按钮 */
.action-btns {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 2px;
}

.action-btns .el-button {
  display: inline-flex;
  align-items: center;
  gap: 3px;
  padding: 0 8px;
  font-size: 13px;
}

/* 分页器 */
.pager {
  display: flex;
  justify-content: flex-end;
  padding-top: 18px;
}

/* 深色模式 */
html.dark .filters {
  background: linear-gradient(135deg, rgba(143, 157, 255, 0.08) 0%, rgba(239, 143, 180, 0.08) 100%);
}

html.dark .cat-chip {
  background: var(--bm-primary-soft-2);
}
</style>
