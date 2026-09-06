<template>
  <aside class="side">
    <!-- 站点名片 -->
    <div class="bm-card card profile-card">
      <span class="glow"></span>
      <div class="avatar-wrap">
        <el-avatar :size="84" :src="profile.avatar || ''" class="avatar">
          {{ avatarText }}
        </el-avatar>
        <span class="avatar-ring"></span>
      </div>
      <h3 class="nickname">{{ profile.nickname || site.title }}</h3>
      <p class="bio">{{ profile.bio || site.description }}</p>
      <div class="stat">
        <div><strong>{{ site.post_count }}</strong><span>文章</span></div>
        <div><strong>{{ site.category_count }}</strong><span>分类</span></div>
      </div>
      <div class="links">
        <a v-if="profile.github" :href="profile.github" target="_blank" rel="noopener" title="GitHub">
          <el-icon><Link /></el-icon>
        </a>
        <a v-if="profile.email" :href="`mailto:${profile.email}`" title="邮箱">
          <el-icon><Message /></el-icon>
        </a>
        <a v-if="profile.website" :href="profile.website" target="_blank" rel="noopener" title="网站">
          <el-icon><HomeFilled /></el-icon>
        </a>
      </div>
    </div>

    <!-- 分类 -->
    <div class="bm-card card">
      <h4 class="bm-section-title">分类</h4>
      <ul class="list">
        <li v-for="c in categories" :key="c.id" @click="goCategory(c)">
          <span class="name">{{ c.name }}</span>
          <span class="count">{{ c.post_count }}</span>
        </li>
        <li v-if="!categories.length" class="empty">暂无分类</li>
      </ul>
    </div>

    <!-- 热门文章 -->
    <div class="bm-card card">
      <h4 class="bm-section-title">热门文章</h4>
      <ul class="list hot">
        <li v-for="(p, i) in hotPosts" :key="p.id" @click="goPost(p)">
          <span class="rank" :class="{ top: i < 3 }">{{ i + 1 }}</span>
          <span class="name">{{ p.title }}</span>
        </li>
        <li v-if="!hotPosts.length" class="empty">暂无数据</li>
      </ul>
    </div>
  </aside>
</template>

<script setup>
import { computed } from 'vue'
import { useRouter } from 'vue-router'

const props = defineProps({
  site: { type: Object, default: () => ({}) },
  profile: { type: Object, default: () => ({}) },
  categories: { type: Array, default: () => [] },
  hotPosts: { type: Array, default: () => [] },
})

const router = useRouter()

const avatarText = computed(() => {
  const name = props.profile.nickname || props.site.title || 'B'
  return name.slice(0, 1).toUpperCase()
})

const goCategory = (c) => router.push({ name: 'categories', query: { cat: c.id } })
const goPost = (p) => router.push({ name: 'post', params: { slug: p.slug } })
</script>

<style scoped>
.side {
  width: 300px;
  flex-shrink: 0;
}

.card {
  padding: 20px;
  margin-bottom: 16px;
}

.profile-card {
  position: relative;
  text-align: center;
  overflow: hidden;
}

.avatar-wrap {
  position: relative;
  width: 84px;
  height: 84px;
  margin: 0 auto 12px;
}

.avatar {
  display: block !important;
  margin: 0 auto !important;
  position: relative;
  z-index: 2;
  background: var(--bm-gradient) !important;
  font-size: 32px !important;
  font-weight: 700;
  color: #fff !important;
  box-shadow: 0 8px 20px var(--bm-shadow-color);
  transition: transform 0.4s var(--bm-ease-bounce);
}

.avatar-wrap:hover .avatar {
  transform: scale(1.06) rotate(-5deg);
}

.avatar-ring {
  position: absolute;
  top: -4px;
  left: -4px;
  right: -4px;
  bottom: -4px;
  border-radius: 50%;
  background: var(--bm-gradient);
  opacity: 0.3;
  z-index: 1;
  animation: avatar-ring-pulse 3s ease-in-out infinite;
}

@keyframes avatar-ring-pulse {
  0%, 100% { transform: scale(1); opacity: 0.3; }
  50% { transform: scale(1.08); opacity: 0.5; }
}

.nickname {
  margin: 4px 0 4px;
  font-size: 17px;
  position: relative;
  z-index: 2;
}

.bio {
  margin: 0 0 16px;
  font-size: 13px;
  color: var(--bm-text-sub);
  position: relative;
}

.stat {
  display: flex;
  border-top: 1px solid var(--bm-border);
  padding-top: 14px;
}

.stat div {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.stat strong {
  font-size: 18px;
  color: var(--bm-text);
  font-weight: 800;
}

.stat span {
  font-size: 12px;
  color: var(--bm-text-sub);
}

.links {
  display: flex;
  justify-content: center;
  gap: 16px;
  margin-top: 16px;
  font-size: 18px;
  color: var(--bm-text-sub);
}

.links a {
  transition: color 0.2s, transform 0.2s;
}

.links a:hover {
  color: var(--bm-primary-2);
  transform: translateY(-2px);
}

.list {
  list-style: none;
  margin: 0;
  padding: 0;
}

.list li {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 0;
  font-size: 14px;
  cursor: pointer;
  border-bottom: 1px dashed var(--bm-border);
  transition: padding-left 0.2s;
}

.list li:last-child {
  border-bottom: none;
}

.list li:hover {
  padding-left: 4px;
}

.list li:hover .name {
  color: var(--bm-primary-2);
}

.list .name {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.list .count {
  flex-shrink: 0;
  margin-left: 8px;
  font-size: 12px;
  color: var(--bm-primary-2);
  background: var(--bm-primary-soft);
  border-radius: 10px;
  padding: 0 8px;
}

.hot li {
  justify-content: flex-start;
  gap: 10px;
}

.rank {
  flex: 0 0 22px;
  height: 22px;
  line-height: 22px;
  text-align: center;
  border-radius: 6px;
  background: var(--bm-primary-soft);
  color: var(--bm-text-sub);
  font-size: 12px;
  font-weight: 600;
}

.rank.top {
  background: var(--bm-gradient);
  color: #fff;
  box-shadow: 0 4px 10px rgba(102, 126, 234, 0.3);
}

.empty {
  font-size: 13px;
  color: var(--bm-text-mute);
  cursor: default !important;
}

@media (max-width: 900px) {
  .side {
    width: 100%;
  }
}
</style>
