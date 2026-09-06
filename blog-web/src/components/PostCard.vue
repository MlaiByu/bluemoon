<template>
  <article class="post-card" @click="go">
    <div class="cover" :class="{ empty: !post.cover }">
      <img v-if="post.cover" :src="coverUrl" :alt="post.title" loading="lazy" />
      <span v-if="post.is_top" class="top-badge">置顶</span>
      <span
        v-if="post.category"
        class="cover-cat"
        @click.stop="goCategory(post.category)"
      >
        <el-icon><Folder /></el-icon>{{ post.category.name }}
      </span>
    </div>

    <div class="body">
      <div class="meta">
        <span>{{ formatDate(post.published_at || post.created_at) }}</span>
        <span class="dot">·</span>
        <span><el-icon><View /></el-icon>{{ post.views }}</span>
        <span class="dot">·</span>
        <span>{{ readingTime }} 分钟</span>
      </div>

      <h2 class="title" v-html="hl(post.title)"></h2>
      <p class="summary" v-html="post.summary ? hl(post.summary) : '（暂无摘要）'"></p>

      <div class="footer">
        <span class="more">阅读全文 →</span>
      </div>
    </div>
  </article>
</template>

<script setup>
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { formatDate, readingMinutes } from '@/utils/format'

const props = defineProps({
  post: { type: Object, required: true },
  keyword: { type: String, default: '' },
})
const router = useRouter()

const readingTime = computed(() => readingMinutes(props.post.word_count))
const coverUrl = computed(() => resolveImageUrl(props.post.cover))

// 搜索高亮：对文本做 HTML 转义，仅把命中片段（文章自身内容）包进 <mark>。
// keyword 只作为正则分隔符，绝不会被插入输出，因此恶意 keyword 无法注入 HTML。
function escapeHtml(s) {
  return s
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
}
function hl(text) {
  if (!props.keyword || !text) return escapeHtml(text || '')
  const kw = props.keyword.trim()
  if (!kw) return escapeHtml(text)
  const re = new RegExp('(' + kw.replace(/[.*+?^${}()|[\]\\]/g, '\\$&') + ')', 'gi')
  let out = ''
  let last = 0
  text.replace(re, (m, _p1, offset) => {
    out += escapeHtml(text.slice(last, offset)) + '<mark>' + escapeHtml(m) + '</mark>'
    last = offset + m.length
    return m
  })
  out += escapeHtml(text.slice(last))
  return out
}

const go = () => router.push({ name: 'post', params: { slug: props.post.slug } })
const goTag = (t) => router.push({ name: 'tags', query: { tag: t.id } })
const goCategory = (c) => router.push({ name: 'categories', query: { cat: c.id } })
</script>

<style scoped>
.post-card {
  display: flex;
  gap: 18px;
  padding: 16px;
  margin-bottom: 18px;
  background: var(--bm-card);
  border-radius: var(--bm-radius);
  box-shadow: var(--bm-shadow-card);
  cursor: pointer;
  transition: transform 0.32s var(--bm-ease-bounce), box-shadow 0.32s var(--bm-ease),
    border-color 0.32s var(--bm-ease);
  border: 1px solid var(--bm-border);
}

.post-card:hover {
  transform: translateY(-6px);
  box-shadow: var(--bm-shadow-hover);
  border-color: transparent;
}

.cover {
  position: relative;
  flex: 0 0 196px;
  height: 134px;
  border-radius: var(--bm-radius-sm);
  overflow: hidden;
  background: var(--bm-gradient-soft);
}

.cover.empty {
  display: flex;
  align-items: center;
  justify-content: center;
}

.cover img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  transition: transform 0.45s ease;
}

.post-card:hover .cover img {
  transform: scale(1.08);
}

.cover:not(.empty)::after {
  content: '';
  position: absolute;
  left: 0;
  right: 0;
  bottom: 0;
  height: 46%;
  background: linear-gradient(to top, rgba(0, 0, 0, 0.3), transparent);
  pointer-events: none;
}

.top-badge {
  position: absolute;
  top: 8px;
  left: 8px;
  z-index: 2;
  padding: 2px 9px;
  border-radius: 999px;
  background: var(--bm-gradient);
  color: #fff;
  font-size: 11.5px;
  font-weight: 700;
  box-shadow: 0 4px 10px var(--bm-shadow-color);
}

.cover-cat {
  position: absolute;
  left: 8px;
  bottom: 8px;
  z-index: 2;
  display: inline-flex;
  align-items: center;
  gap: 3px;
  padding: 2px 10px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.92);
  color: var(--bm-primary-2);
  font-size: 11.5px;
  font-weight: 700;
  cursor: pointer;
  backdrop-filter: blur(4px);
  transition: background 0.2s, color 0.2s;
}

.cover-cat:hover {
  background: var(--bm-primary-2);
  color: #fff;
}

.cover-cat .el-icon {
  font-size: 12px;
}

.body {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
}

.meta {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 6px;
  font-size: 12.5px;
  color: var(--bm-text-sub);
}

.meta .el-icon {
  margin-right: 3px;
  vertical-align: -1px;
}

.meta .dot {
  opacity: 0.5;
}

.title {
  margin: 8px 0 6px;
  font-size: 19px;
  font-weight: 700;
  line-height: 1.4;
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
}

.summary {
  flex: 1;
  margin: 0 0 12px;
  color: var(--bm-text-sub);
  font-size: 14px;
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
}

.footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.more {
  flex-shrink: 0;
  font-size: 13px;
  font-weight: 600;
  color: var(--bm-primary-2);
  transition: transform 0.2s;
}

.post-card:hover .more {
  transform: translateX(4px);
}

/* 搜索命中高亮 */
.post-card mark {
  background: var(--bm-accent-soft);
  color: var(--bm-primary-2);
  padding: 0 3px;
  border-radius: 5px;
  font-weight: 800;
}

@media (max-width: 700px) {
  .post-card {
    flex-direction: column;
  }
  .cover {
    flex: none;
    width: 100%;
    height: 170px;
  }
}
</style>
