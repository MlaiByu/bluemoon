<template>
  <div v-loading="loading" class="dashboard">
    <!-- 欢迎横幅 -->
    <div class="welcome-banner bm-fade-up">
      <div class="banner-content">
        <div class="banner-text">
          <h2 class="greeting">{{ greeting }}，{{ user?.nickname || '博主' }} ✨</h2>
          <p class="sub">今天也要元气满满地创作哦～</p>
        </div>
        <div class="banner-stats">
          <div class="stat-mini">
            <span class="label">今日访问</span>
            <strong class="value">{{ overview.total_views ?? 0 }}</strong>
          </div>
          <div class="stat-mini">
            <span class="label">文章总数</span>
            <strong class="value">{{ overview.total_posts ?? 0 }}</strong>
          </div>
        </div>
      </div>
      <div class="banner-deco" aria-hidden="true">
        <span class="star star-1">✦</span>
        <span class="star star-2">✧</span>
        <span class="star star-3">✦</span>
        <span class="cloud cloud-1">☁</span>
        <span class="cloud cloud-2">☁</span>
      </div>
    </div>

    <!-- 统计卡片 -->
    <div class="cards">
      <div
        v-for="(c, i) in cards"
        :key="c.label"
        class="stat-card bm-fade-up"
        :style="{ animationDelay: `${i * 0.08 + 0.1}s` }"
        :class="c.theme"
      >
        <div class="card-bg" aria-hidden="true"></div>
        <div class="icon">
          <el-icon :size="24"><component :is="c.icon" /></el-icon>
        </div>
        <div class="info">
          <strong class="value">{{ c.value }}</strong>
          <span class="label">{{ c.label }}</span>
        </div>
        <div class="trend" v-if="c.trend">
          <el-icon><TrendCharts /></el-icon>
          <span>{{ c.trend }}</span>
        </div>
      </div>
    </div>

    <el-row :gutter="16">
      <!-- 发布趋势 -->
      <el-col :xs="24" :md="14">
        <div class="bm-card panel bm-fade-up" style="animation-delay: 0.2s">
          <div class="panel-head">
            <h3 class="panel-title"><span class="dot"></span>近 7 天发布趋势</h3>
            <span class="panel-sub">最近一周发文统计</span>
          </div>
          <div class="chart">
            <div v-for="(d, i) in overview.trend || []" :key="d.date" class="bar-wrap"
                 :style="{ animationDelay: `${i * 0.06 + 0.3}s` }">
              <div class="bar" :style="{ height: barHeight(d.count) }" :title="`${d.date}: ${d.count} 篇`">
                <span class="bar-top" v-if="d.count">{{ d.count }}</span>
              </div>
              <span class="bar-label">{{ d.date }}</span>
            </div>
            <div v-if="!(overview.trend || []).length" class="chart-empty">暂无数据</div>
          </div>
        </div>
      </el-col>

      <!-- 分类分布 -->
      <el-col :xs="24" :md="10">
        <div class="bm-card panel bm-fade-up" style="animation-delay: 0.28s">
          <div class="panel-head">
            <h3 class="panel-title"><span class="dot"></span>分类分布</h3>
            <span class="panel-sub">共 {{ (overview.category_dist || []).length }} 个分类</span>
          </div>
          <ul class="dist">
            <li v-for="(c, i) in overview.category_dist || []" :key="c.name"
                :style="{ animationDelay: `${i * 0.05 + 0.35}s` }">
              <span class="d-name">{{ c.name }}</span>
              <div class="d-bar">
                <i :style="{ width: distWidth(c.value) }"></i>
              </div>
              <span class="d-val">{{ c.value }}</span>
            </li>
            <li v-if="!(overview.category_dist || []).length" class="chart-empty">暂无数据</li>
          </ul>
        </div>
      </el-col>
    </el-row>

    <!-- 热门文章 -->
    <div class="bm-card panel bm-fade-up" style="animation-delay: 0.35s">
      <div class="panel-head">
        <h3 class="panel-title"><span class="dot"></span>热门文章 Top 5</h3>
        <span class="panel-sub">按阅读量排序</span>
      </div>
      <el-table :data="overview.top_posts || []" size="default" stripe>
        <el-table-column type="index" width="60" label="#" align="center">
          <template #default="{ $index }">
            <span class="rank-badge" :class="`rank-${$index + 1}`">{{ $index + 1 }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="title" label="标题" min-width="280" show-overflow-tooltip />
        <el-table-column prop="views" label="阅读量" width="120" align="right">
          <template #default="{ row }">
            <span class="view-count">
              <el-icon><View /></el-icon>
              {{ row.views }}
            </span>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="130" align="center">
          <template #default="{ row }">
            <el-button link type="primary" size="small" @click="edit(row.id)">编辑</el-button>
            <el-button link type="info" size="small" @click="view(row.slug)">查看</el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <el-row :gutter="16">
      <!-- 缓存管理 -->
      <el-col :xs="24" :md="12">
        <div class="bm-card panel bm-fade-up" style="animation-delay: 0.4s">
          <div class="panel-head">
            <h3 class="panel-title"><span class="dot"></span>缓存管理</h3>
            <el-tag :type="cacheInfo.status === 'up' ? 'success' : 'danger'" size="small" effect="light" round>
              {{ cacheInfo.status === 'up' ? '运行中' : '异常' }}
            </el-tag>
          </div>
          <div class="cache-info">
            <div class="cache-item">
              <span class="ci-label">Redis 状态</span>
              <span class="ci-value" :class="cacheInfo.status === 'up' ? 'ok' : 'bad'">
                <span class="status-dot"></span>
                {{ cacheInfo.status === 'up' ? '正常运行' : '未启用 / 异常' }}
              </span>
            </div>
            <div class="cache-item">
              <span class="ci-label">缓存键数</span>
              <span class="ci-value">{{ cacheInfo.keys ?? '-' }}</span>
            </div>
          </div>
          <el-button :icon="Delete" type="warning" plain :loading="clearing" class="cache-btn" @click="doClearCache">
            清空缓存
          </el-button>
          <p class="cache-tip">清空后下次访问会重新从 MySQL 加载并写入缓存（列表/详情/统计等）。</p>
        </div>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import {
  DataLine, Delete, Document, EditPen, TrendCharts, View,
} from '@element-plus/icons-vue'
import { flushCache, flushViews, getCacheInfo, getOverview } from '@/api'
import { useUserStore } from '@/stores/user'

const router = useRouter()
const store = useUserStore()
const user = computed(() => store.user)
const overview = ref({})
const loading = ref(false)
const cacheInfo = ref({})
const clearing = ref(false)

const greeting = computed(() => {
  const hour = new Date().getHours()
  if (hour < 6) return '夜深了'
  if (hour < 11) return '早上好'
  if (hour < 13) return '中午好'
  if (hour < 18) return '下午好'
  return '晚上好'
})

const cards = computed(() => [
  { label: '文章总数', value: overview.value.total_posts ?? 0, icon: Document, theme: 'theme-blue', trend: '全部' },
  { label: '已发布', value: overview.value.published ?? 0, icon: View, theme: 'theme-purple', trend: '公开' },
  { label: '草稿箱', value: overview.value.drafts ?? 0, icon: EditPen, theme: 'theme-pink', trend: '待发布' },
  { label: '总阅读量', value: overview.value.total_views ?? 0, icon: DataLine, theme: 'theme-mint', trend: '累计' },
])

const maxTrend = computed(() =>
  Math.max(1, ...(overview.value.trend || []).map((d) => d.count))
)
const barHeight = (n) => `${Math.max(6, (n / maxTrend.value) * 100)}%`

const maxDist = computed(() =>
  Math.max(1, ...(overview.value.category_dist || []).map((c) => c.value))
)
const distWidth = (n) => `${(n / maxDist.value) * 100}%`

async function loadData() {
  loading.value = true
  try {
    overview.value = (await getOverview()) || {}
  } finally {
    loading.value = false
  }
}

async function loadCacheInfo() {
  try {
    cacheInfo.value = (await getCacheInfo()) || {}
  } catch {
    /* 拦截器已提示 */
  }
}

async function doFlush() {
  try {
    const res = await flushViews()
    ElMessage.success(res.msg || '已回写')
    loadData()
  } catch {
    /* 拦截器已提示 */
  }
}

async function doClearCache() {
  clearing.value = true
  try {
    const res = await flushCache()
    ElMessage.success(res.msg || '已清空')
    loadCacheInfo()
    loadData()
  } catch {
    /* 拦截器已提示 */
  } finally {
    clearing.value = false
  }
}

const edit = (id) => router.push(`/admin/posts/${id}`)
const view = (slug) => router.push({ name: 'post', params: { slug } })

onMounted(() => {
  loadData()
  loadCacheInfo()
})
</script>

<style scoped>
.dashboard {
  position: relative;
}

/* ============================ 欢迎横幅 ============================ */
.welcome-banner {
  position: relative;
  padding: 28px 32px;
  border-radius: var(--bm-radius);
  background: var(--bm-gradient);
  color: #fff;
  margin-bottom: 20px;
  overflow: hidden;
  box-shadow: 0 12px 32px var(--bm-shadow-color);
}

.banner-content {
  position: relative;
  z-index: 1;
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 20px;
}

.greeting {
  margin: 0;
  font-size: 22px;
  font-weight: 800;
  letter-spacing: 0.5px;
  text-shadow: 0 2px 10px rgba(0, 0, 0, 0.15);
}

.sub {
  margin: 6px 0 0;
  font-size: 14px;
  opacity: 0.9;
}

.banner-stats {
  display: flex;
  gap: 32px;
}

.stat-mini {
  text-align: center;
}

.stat-mini .label {
  display: block;
  font-size: 12px;
  opacity: 0.85;
  margin-bottom: 4px;
}

.stat-mini .value {
  font-size: 24px;
  font-weight: 800;
  text-shadow: 0 2px 10px rgba(0, 0, 0, 0.15);
}

/* 装饰元素 */
.banner-deco {
  position: absolute;
  inset: 0;
  pointer-events: none;
  overflow: hidden;
}

.star {
  position: absolute;
  font-size: 16px;
  opacity: 0.6;
  animation: twinkle 3s ease-in-out infinite;
}

.star-1 { top: 18%; left: 15%; animation-delay: 0s; }
.star-2 { top: 60%; left: 40%; font-size: 12px; animation-delay: 1s; }
.star-3 { top: 25%; right: 30%; font-size: 14px; animation-delay: 2s; }

@keyframes twinkle {
  0%, 100% { opacity: 0.3; transform: scale(0.8); }
  50% { opacity: 0.9; transform: scale(1.2); }
}

.cloud {
  position: absolute;
  font-size: 40px;
  opacity: 0.15;
  animation: float 6s ease-in-out infinite;
}

.cloud-1 { top: -10px; right: 10%; }
.cloud-2 { bottom: -20px; right: 25%; font-size: 50px; animation-delay: 2s; }

@keyframes float {
  0%, 100% { transform: translateY(0) translateX(0); }
  50% { transform: translateY(-8px) translateX(5px); }
}

/* ============================ 统计卡片 ============================ */
.cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 16px;
  margin-bottom: 16px;
}

.stat-card {
  position: relative;
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 24px;
  background: #fff;
  border-radius: var(--bm-radius);
  box-shadow: var(--bm-shadow-card);
  border: 1px solid var(--bm-border);
  overflow: hidden;
  transition: transform 0.3s var(--bm-ease-bounce), box-shadow 0.3s var(--bm-ease);
}

.stat-card:hover {
  transform: translateY(-6px);
  box-shadow: var(--bm-shadow-hover);
}

.card-bg {
  position: absolute;
  top: 0;
  right: 0;
  width: 120px;
  height: 120px;
  border-radius: 50%;
  filter: blur(40px);
  opacity: 0.3;
  pointer-events: none;
}

.theme-blue .card-bg { background: var(--bm-primary); }
.theme-purple .card-bg { background: var(--bm-primary-2); }
.theme-pink .card-bg { background: var(--bm-accent); }
.theme-mint .card-bg { background: var(--bm-mint); }

.stat-card .icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 54px;
  height: 54px;
  border-radius: 14px;
  color: #fff;
  position: relative;
  z-index: 1;
  flex-shrink: 0;
}

.theme-blue .icon { background: linear-gradient(135deg, #8ab6ff, #6a9cf5); box-shadow: 0 8px 20px rgba(122, 165, 247, 0.4); }
.theme-purple .icon { background: linear-gradient(135deg, #c9a8ff, #b892f6); box-shadow: 0 8px 20px rgba(184, 146, 246, 0.4); }
.theme-pink .icon { background: linear-gradient(135deg, #ffc4d6, #ffb0c8); box-shadow: 0 8px 20px rgba(255, 176, 200, 0.4); }
.theme-mint .icon { background: linear-gradient(135deg, #a5e8db, #8fe0cf); box-shadow: 0 8px 20px rgba(143, 224, 207, 0.4); }

.stat-card .info {
  display: flex;
  flex-direction: column;
  gap: 4px;
  position: relative;
  z-index: 1;
}

.stat-card .value {
  font-size: 28px;
  line-height: 1.1;
  font-weight: 800;
  color: var(--bm-text);
}

.theme-blue .value { color: #4a7fd9; }
.theme-purple .value { color: #8b6cd9; }
.theme-pink .value { color: #e07a9a; }
.theme-mint .value { color: #4ab8a0; }

.stat-card .label {
  font-size: 13.5px;
  color: var(--bm-text-sub);
}

.stat-card .trend {
  margin-left: auto;
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  color: var(--bm-text-mute);
  padding: 4px 10px;
  background: var(--bm-primary-soft);
  border-radius: 999px;
  position: relative;
  z-index: 1;
}

/* ============================ 面板头部 ============================ */
.panel-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 18px;
}

.panel-title {
  display: flex;
  align-items: center;
  gap: 9px;
  margin: 0;
  font-size: 16px;
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

.panel-sub {
  font-size: 12.5px;
  color: var(--bm-text-mute);
}

/* ============================ 图表 ============================ */
.chart {
  display: flex;
  align-items: flex-end;
  gap: 12px;
  height: 200px;
  padding-top: 20px;
}

.bar-wrap {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: flex-end;
  height: 100%;
  gap: 8px;
  animation: bar-grow 0.6s var(--bm-ease-bounce) backwards;
}

@keyframes bar-grow {
  from { opacity: 0; transform: scaleY(0.3); }
  to { opacity: 1; transform: scaleY(1); }
}

.bar {
  width: 65%;
  max-width: 36px;
  min-height: 4px;
  background: linear-gradient(180deg, var(--bm-primary) 0%, var(--bm-primary-2) 100%);
  border-radius: 8px 8px 4px 4px;
  position: relative;
  cursor: pointer;
  transition: filter 0.25s var(--bm-ease), transform 0.25s var(--bm-ease);
  transform-origin: bottom;
}

.bar:hover {
  filter: brightness(1.15) saturate(1.2);
  transform: scaleX(1.1);
}

.bar-top {
  position: absolute;
  top: -22px;
  left: 50%;
  transform: translateX(-50%);
  font-size: 11.5px;
  font-weight: 700;
  color: var(--bm-primary-2);
  background: #fff;
  padding: 2px 6px;
  border-radius: 6px;
  box-shadow: 0 2px 8px rgba(184, 146, 246, 0.2);
  white-space: nowrap;
  opacity: 0;
  transition: opacity 0.25s var(--bm-ease);
}

.bar:hover .bar-top {
  opacity: 1;
}

.bar-label {
  font-size: 11.5px;
  color: var(--bm-text-sub);
}

.chart-empty {
  width: 100%;
  text-align: center;
  color: #c0c4cc;
  font-size: 13px;
  padding: 40px 0;
}

/* ============================ 分类分布 ============================ */
.dist {
  list-style: none;
  margin: 0;
  padding: 0;
}

.dist li {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 0;
  font-size: 13.5px;
  animation: dist-in 0.5s var(--bm-ease) backwards;
}

@keyframes dist-in {
  from { opacity: 0; transform: translateX(-10px); }
  to { opacity: 1; transform: translateX(0); }
}

.d-name {
  flex: 0 0 84px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-weight: 500;
}

.d-bar {
  flex: 1;
  height: 10px;
  background: #f0f1f5;
  border-radius: 5px;
  overflow: hidden;
}

.d-bar i {
  display: block;
  height: 100%;
  background: var(--bm-gradient);
  border-radius: 5px;
  transition: width 0.6s var(--bm-ease-bounce);
  box-shadow: 0 0 10px rgba(184, 146, 246, 0.25);
}

.d-val {
  flex: 0 0 32px;
  text-align: right;
  color: var(--bm-text-sub);
  font-weight: 600;
}

/* ============================ 热门文章排名徽章 ============================ */
.rank-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 26px;
  height: 26px;
  border-radius: 8px;
  font-size: 12px;
  font-weight: 700;
  background: var(--bm-primary-soft);
  color: var(--bm-primary-2);
}

.rank-1 { background: linear-gradient(135deg, #ffd76e, #ffb347); color: #fff; box-shadow: 0 3px 10px rgba(255, 179, 71, 0.4); }
.rank-2 { background: linear-gradient(135deg, #c0c8d6, #a0aac0); color: #fff; box-shadow: 0 3px 10px rgba(160, 170, 192, 0.4); }
.rank-3 { background: linear-gradient(135deg, #e8a87c, #d4916a); color: #fff; box-shadow: 0 3px 10px rgba(212, 145, 106, 0.4); }

.view-count {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-weight: 600;
  color: var(--bm-primary-2);
}

.view-count .el-icon {
  font-size: 14px;
}

/* ============================ 缓存管理 ============================ */
.cache-info {
  margin-bottom: 16px;
}

.cache-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 0;
  border-bottom: 1px dashed var(--bm-border);
}

.cache-item:last-of-type {
  border-bottom: none;
}

.ci-label {
  font-size: 13.5px;
  color: var(--bm-text-sub);
}

.ci-value {
  font-size: 14px;
  font-weight: 600;
  display: flex;
  align-items: center;
  gap: 8px;
}

.ci-value.ok { color: #18a058; }
.ci-value.bad { color: #e0525f; }

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: currentColor;
  animation: pulse 2s ease-in-out infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; transform: scale(1); }
  50% { opacity: 0.6; transform: scale(0.85); }
}

.cache-btn {
  width: 100%;
  margin-bottom: 10px;
}

.cache-tip {
  margin: 0;
  font-size: 12px;
  color: var(--bm-text-mute);
  line-height: 1.5;
}

/* ============================ 深色模式 ============================ */
html.dark .stat-card {
  background: var(--bm-card);
}

html.dark .d-bar {
  background: rgba(255, 255, 255, 0.06);
}

html.dark .quick-btn {
  background: var(--bm-card);
}

html.dark .q-icon {
  background: var(--bm-primary-soft);
}

html.dark .bar-top {
  background: var(--bm-card);
}

html.dark .cache-item {
  border-bottom-color: var(--bm-border);
}

/* 响应式 */
@media (max-width: 640px) {
  .welcome-banner {
    padding: 20px;
  }

  .greeting {
    font-size: 18px;
  }

  .banner-stats {
    gap: 20px;
  }

  .stat-mini .value {
    font-size: 20px;
  }

  .cards {
    grid-template-columns: repeat(2, 1fr);
    gap: 12px;
  }

  .stat-card {
    padding: 16px;
    flex-direction: column;
    text-align: center;
    gap: 10px;
  }

  .stat-card .trend {
    margin: 0;
  }

  .stat-card .value {
    font-size: 22px;
  }

  .quick {
    grid-template-columns: repeat(3, 1fr);
  }
}
</style>
