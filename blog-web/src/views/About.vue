<template>
  <div class="bm-container layout">
    <div class="content bm-card" v-loading="loading">
      <div class="hero">
        <div class="avatar-block">
          <div class="avatar-wrap">
            <el-avatar :size="96" :src="profile.avatar || ''" class="avatar">
              {{ avatarText }}
            </el-avatar>
            <span class="avatar-ring"></span>
          </div>
        </div>
        <div class="hero-info">
          <h2 class="name">{{ profile.nickname || site.title }}</h2>
          <p class="bio">{{ profile.bio || site.description }}</p>
          <div class="contacts">
            <span v-if="profile.location"><el-icon><Location /></el-icon>{{ profile.location }}</span>
            <a v-if="profile.email" :href="`mailto:${profile.email}`"><el-icon><Message /></el-icon>{{ profile.email }}</a>
            <a v-if="profile.github" :href="profile.github" target="_blank" rel="noopener">
              <el-icon><Link /></el-icon>GitHub
            </a>
            <a v-if="profile.website" :href="profile.website" target="_blank" rel="noopener">
              <el-icon><HomeFilled /></el-icon>个人网站
            </a>
            <span v-if="profile.wechat"><el-icon><ChatDotRound /></el-icon>微信 {{ profile.wechat }}</span>
            <span v-if="profile.qq"><el-icon><User /></el-icon>QQ {{ profile.qq }}</span>
          </div>
        </div>
      </div>

      <div class="stats" v-if="stats.length">
        <div v-for="s in stats" :key="s.label">
          <strong class="bm-gradient-text">{{ site[s.key] }}</strong>
          <span>{{ s.label }}</span>
        </div>
      </div>

      <div class="md">
        <MarkdownView :content="profile.content || '还没有填写自我介绍～'" />
      </div>

      <!-- 视觉模块：技能栈（光影相册已迁至「图片」页，此处不再保留） -->
      <div class="modules">
        <SkillStack subtitle="滚动到此处触发" />
      </div>
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
import MarkdownView from '@/components/MarkdownView.vue'
import SidePanel from '@/components/SidePanel.vue'
import SkillStack from '@/components/SkillStack.vue'
import { useSiteStore } from '@/stores/site'

const siteStore = useSiteStore()
const site = computed(() => siteStore.site || {})
const profile = computed(() => siteStore.profile || {})
const loading = ref(false)

const avatarText = computed(() => {
  const name = profile.value.nickname || site.value.title || 'B'
  return name.slice(0, 1).toUpperCase()
})

/* 统计项动态生成：后端未提供的字段（如 tag_count）自动隐藏，避免出现空占位 */
const stats = computed(() =>
  [
    { key: 'post_count', label: '文章' },
    { key: 'category_count', label: '分类' },
    { key: 'tag_count', label: '标签' },
    { key: 'total_views', label: '总阅读' },
  ].filter((s) => site.value[s.key] !== undefined && site.value[s.key] !== null)
)

onMounted(async () => {
  loading.value = true
  await siteStore.load()
  loading.value = false
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
  padding: 34px 38px;
  position: relative;
  overflow: hidden;
}

.hero {
  position: relative;
  display: flex;
  align-items: center;
  gap: 24px;
  padding-bottom: 24px;
  border-bottom: 1px solid var(--bm-border);
}

.avatar-block {
  flex-shrink: 0;
  position: relative;
  z-index: 2;
}

.avatar-wrap {
  position: relative;
  width: 96px;
  height: 96px;
}

.avatar {
  display: block !important;
  margin: 0 auto !important;
  position: relative;
  z-index: 2;
  background: var(--bm-gradient) !important;
  font-size: 38px !important;
  font-weight: 700;
  color: #fff !important;
  box-shadow: 0 10px 24px var(--bm-shadow-color);
  transition: transform 0.4s var(--bm-ease-bounce);
}

.avatar-wrap:hover .avatar {
  transform: scale(1.06) rotate(-5deg);
}

.avatar-ring {
  position: absolute;
  top: -5px;
  left: -5px;
  right: -5px;
  bottom: -5px;
  border-radius: 50%;
  background: var(--bm-gradient);
  opacity: 0.3;
  z-index: 1;
  animation: about-avatar-ring 3s ease-in-out infinite;
}

@keyframes about-avatar-ring {
  0%, 100% { transform: scale(1); opacity: 0.3; }
  50% { transform: scale(1.08); opacity: 0.5; }
}

.name {
  margin: 0 0 6px;
  font-size: 23px;
  letter-spacing: 0.5px;
}

.bio {
  margin: 0 0 12px;
  color: var(--bm-text-sub);
  font-size: 14px;
}

.contacts {
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
  font-size: 13px;
  color: var(--bm-text-sub);
}

.contacts a {
  color: var(--bm-text-sub);
}

.contacts a:hover {
  color: var(--bm-primary-2);
}

.contacts .el-icon {
  margin-right: 4px;
  vertical-align: -2px;
}

.stats {
  display: flex;
  margin: 24px 0;
  padding: 20px 0;
  /* 主题令牌：明暗模式自动切换（浅色柔和渐变 / 深色半透明光晕） */
  background: var(--bm-gradient-soft);
  border: 1px solid var(--bm-border);
  border-radius: 14px;
}

.stats div {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 2px;
  border-right: 1px solid var(--bm-border);
}

.stats div:last-child {
  border-right: none;
}

.stats strong {
  font-size: 24px;
  font-weight: 800;
  line-height: 1.3;
}

.stats span {
  font-size: 12.5px;
  color: var(--bm-text-sub);
}

.md {
  padding-top: 8px;
}

/* 视觉模块区：两模块间距与卡片一致，移动端堆叠 */
.modules {
  display: flex;
  flex-direction: column;
  gap: 20px;
  margin-top: 22px;
}

@media (max-width: 900px) {
  .layout {
    flex-direction: column;
  }
  .content {
    padding: 22px 16px;
  }
  .hero {
    flex-direction: column;
    text-align: center;
  }
}
</style>
