<template>
  <!-- 首屏 Hero：随机背景图 + 随机文案 + 快捷导航 + 下滑进入主页 -->
  <section class="hero" :style="{ '--hero-bg': bannerSrc }">
    <div class="hero-banner" aria-hidden="true">
      <img :src="bannerSrc" alt="" loading="eager" />
    </div>

    <!-- 装饰：漂浮光斑 + 随机星点 -->
    <div class="hero-deco" aria-hidden="true">
      <span class="orb orb-1"></span>
      <span class="orb orb-2"></span>
      <span class="orb orb-3"></span>
      <span
        v-for="s in stars"
        :key="s.id"
        class="star"
        :class="s.shape"
        :style="starStyle(s)"
      >{{ s.char }}</span>
    </div>

    <div class="hero-inner">
      <div class="avatar-lg bm-scale-in" style="animation-delay: 0.1s">
        <span class="halo"></span>
        <span class="halo-2"></span>
        <el-avatar :size="104" :src="avatar || ''" class="avatar-img">
          <span class="txt">{{ avatarText }}</span>
        </el-avatar>
      </div>

      <h1 class="hero-title bm-fade-up" style="animation-delay: 0.25s">{{ title }}</h1>
      <p class="hero-bio bm-fade-up" style="animation-delay: 0.4s">{{ bio }}</p>

      <!-- 随机一句：每次刷新换一条 -->
      <p class="quote bm-fade-up" style="animation-delay: 0.55s">"{{ quote }}"</p>

      <button class="enter-btn bm-fade-up" style="animation-delay: 0.7s" @click="emit('enter')">
        <span>进入主页</span>
        <el-icon><ArrowDown /></el-icon>
      </button>

      <nav class="hero-links bm-fade-up" style="animation-delay: 0.85s">
        <router-link to="/archives">归档</router-link>
        <router-link to="/categories">分类</router-link>
        <router-link to="/images">图片</router-link>
        <router-link to="/about">关于</router-link>
      </nav>
    </div>

    <div class="scroll-hint" @click="emit('enter')" aria-label="下滑进入主页">
      <el-icon><ArrowDown /></el-icon>
    </div>
  </section>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { ArrowDown } from '@element-plus/icons-vue'

const props = defineProps({
  site: { type: Object, default: () => ({}) },
  avatar: { type: String, default: '' },
  avatarText: { type: String, default: 'B' },
  quote: { type: String, default: '' },
  bannerSrc: { type: String, default: '' },
})

const emit = defineEmits(['enter'])

const title = computed(() => props.site.title || 'BlueMoonの博客')
const bio = computed(
  () => props.site.description || '一个喜欢折腾前端与 Python 的技术人'
)

/* ---------- 随机小星星 ---------- */
// 预设颜色池：日系动漫风（粉、蓝、紫、薄荷、暖黄）
const STAR_COLORS = [
  '#ff8fab', // 粉
  '#8ab6ff', // 蓝
  '#b892ff', // 紫
  '#7ed6c1', // 薄荷
  '#ffd28a', // 暖黄
  '#ffb4c8', // 浅粉
  '#a0c4ff', // 浅蓝
  '#c8b6ff', // 淡紫
]
const STAR_SHAPES = [
  { shape: 's4', char: '✦' },  // 四角星
  { shape: 's5', char: '★' },  // 五角星
  { shape: 's6', char: '✧' },  // 空心四角
  { shape: 's7', char: '⋆' },  // 小星
]

const stars = ref([])
let starTimer = null

/** 生成一颗随机星星 */
function makeStar(id) {
  const shape = STAR_SHAPES[Math.floor(Math.random() * STAR_SHAPES.length)]
  const color = STAR_COLORS[Math.floor(Math.random() * STAR_COLORS.length)]
  // 位置：在 Hero 可视区内随机分布，避开中间 30% 核心内容区
  let top, left
  const isCenterArea = Math.random() > 0.35 // 65% 概率落在边缘区
  if (isCenterArea) {
    // 边缘区域：上下左右四分之一区域
    const side = Math.floor(Math.random() * 4)
    if (side === 0) { // 上
      top = 5 + Math.random() * 25
      left = 5 + Math.random() * 90
    } else if (side === 1) { // 下
      top = 70 + Math.random() * 25
      left = 5 + Math.random() * 90
    } else if (side === 2) { // 左
      top = 10 + Math.random() * 80
      left = 3 + Math.random() * 20
    } else { // 右
      top = 10 + Math.random() * 80
      left = 77 + Math.random() * 20
    }
  } else {
    // 完全随机
    top = 8 + Math.random() * 84
    left = 5 + Math.random() * 90
  }
  return {
    id,
    top,
    left,
    color,
    size: 10 + Math.random() * 16, // 10-26px
    duration: 2 + Math.random() * 3.5, // 闪烁周期 2-5.5s
    delay: -Math.random() * 4, // 错开相位
    shape: shape.shape,
    char: shape.char,
    opacity: 0.4 + Math.random() * 0.55,
  }
}

/** 初始化一组星星 */
function initStars() {
  const w = window.innerWidth
  const count = w < 640 ? 10 : w < 1024 ? 16 : 22
  const list = []
  for (let i = 0; i < count; i++) {
    list.push(makeStar(i))
  }
  stars.value = list
}

/** 生成星星内联样式 */
function starStyle(s) {
  return {
    top: `${s.top}%`,
    left: `${s.left}%`,
    color: s.color,
    fontSize: `${s.size}px`,
    opacity: s.opacity,
    animationDuration: `${s.duration}s`,
    animationDelay: `${s.delay}s`,
    textShadow: `0 0 ${s.size * 0.6}px ${s.color}`,
  }
}

/** 每隔一段时间随机替换几颗星星，制造"随机出现"的感觉 */
function startShuffle() {
  starTimer = setInterval(() => {
    if (!stars.value.length) return
    // 每次随机替换 1-2 颗
    const replaceCount = 1 + Math.floor(Math.random() * 2)
    for (let i = 0; i < replaceCount; i++) {
      const idx = Math.floor(Math.random() * stars.value.length)
      stars.value[idx] = makeStar(stars.value[idx].id + 10000)
    }
  }, 2500)
}

onMounted(() => {
  initStars()
  startShuffle()
  window.addEventListener('resize', initStars)
})

onBeforeUnmount(() => {
  if (starTimer) clearInterval(starTimer)
  window.removeEventListener('resize', initStars)
})
</script>

<style scoped>
/* Hero 顶到屏幕顶端 + 占满整个首屏：消除「下方内容冒头」的预览。
   60px = 顶部导航高度的等量内补，保证头像/标题不被顶栏遮住。 */
.hero {
  position: relative;
  margin: -60px 0 0;
  height: 100vh;
  min-height: 640px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  overflow: hidden;
  padding-top: 60px; /* 与负 margin 抵消，让内容视觉上仍在导航下方 */
  background: linear-gradient(
      160deg,
      rgba(253, 251, 255, 0.86) 0%,
      rgba(247, 246, 255, 0.88) 55%,
      rgba(255, 244, 249, 0.86) 100%
    ),
    var(--hero-bg) center / cover no-repeat;
}

/* 底部羽化遮罩：让 hero 与下方区域无缝过渡，彻底杜绝"冒头"边界 */
.hero::after {
  content: '';
  position: absolute;
  left: 0;
  right: 0;
  bottom: 0;
  height: 120px;
  pointer-events: none;
  z-index: 1;
  background: linear-gradient(
    to bottom,
    transparent 0%,
    rgba(255, 255, 255, 0.55) 70%,
    var(--bm-bg, #ffffff) 100%
  );
}

/* 顶部 banner 背景图 + 柔和遮罩（保证文字可读） */
.hero-banner {
  position: absolute;
  inset: 0;
  z-index: 0;
}

.hero-banner img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}

.hero-banner::after {
  content: '';
  position: absolute;
  inset: 0;
  background: linear-gradient(
    160deg,
    rgba(253, 251, 255, 0.8) 0%,
    rgba(247, 246, 255, 0.84) 55%,
    rgba(255, 244, 249, 0.8) 100%
  );
  mask-image: linear-gradient(
    to bottom,
    #000 0%,
    #000 60%,
    transparent 100%
  );
  -webkit-mask-image: linear-gradient(
    to bottom,
    #000 0%,
    #000 60%,
    transparent 100%
  );
}

/* ---------- 装饰元素 ---------- */
.hero-deco {
  position: absolute;
  inset: 0;
  z-index: 1;
  pointer-events: none;
  overflow: hidden;
}

.orb {
  position: absolute;
  border-radius: 50%;
  filter: blur(90px);
  opacity: 0.6;
}

.orb-1 {
  width: 520px;
  height: 520px;
  top: -180px;
  left: -120px;
  background: radial-gradient(circle, var(--bm-glow-blue), transparent 70%);
  animation: orb-a 18s ease-in-out infinite;
}

.orb-2 {
  width: 560px;
  height: 560px;
  bottom: -220px;
  right: -140px;
  background: radial-gradient(circle, var(--bm-glow-pink), transparent 70%);
  animation: orb-b 22s ease-in-out infinite;
}

.orb-3 {
  width: 340px;
  height: 340px;
  top: 40%;
  right: 10%;
  background: radial-gradient(circle, var(--bm-glow-mint), transparent 70%);
  animation: orb-a 26s ease-in-out infinite reverse;
}

/* 随机小星星 */
.star {
  position: absolute;
  pointer-events: none;
  line-height: 1;
  animation: twinkle ease-in-out infinite;
  will-change: opacity, transform;
}

/* 不同形状轻微差异化动画 */
.star.s5 {
  animation-name: twinkle-scale;
}
.star.s7 {
  animation-name: twinkle;
  animation-timing-function: ease-in-out;
}

/* ---------- 内容 ---------- */
.hero-inner {
  position: relative;
  z-index: 2;
  text-align: center;
  padding: 40px 24px;
  max-width: 760px;
}

.avatar-lg {
  position: relative;
  width: 104px;
  height: 104px;
  margin: 0 auto 22px;
}

.avatar-lg .avatar-img {
  display: block !important;
  margin: 0 auto;
  position: relative;
  z-index: 2;
  background: var(--bm-gradient) !important;
  box-shadow: 0 14px 34px var(--bm-shadow-color);
  transition: transform 0.4s var(--bm-ease-bounce);
}

.avatar-lg:hover .avatar-img {
  transform: scale(1.06) rotate(-4deg);
}

.avatar-lg .txt {
  color: #fff;
  font-size: 42px;
  font-weight: 800;
  letter-spacing: 1px;
}

/* 头像外圈光环 */
.halo {
  position: absolute;
  inset: -9px;
  border-radius: 50%;
  border: 2px dashed var(--bm-accent);
  opacity: 0.7;
  animation: spin 14s linear infinite;
}

/* 第二光环：更大、更淡、反向旋转 */
.halo-2 {
  position: absolute;
  inset: -20px;
  border-radius: 50%;
  border: 1px solid var(--bm-glow-blue);
  opacity: 0.4;
  animation: spin 24s linear infinite reverse;
}

.hero-title {
  font-size: 46px;
  font-weight: 800;
  letter-spacing: 2px;
  margin: 0;
  background: var(--bm-gradient);
  -webkit-background-clip: text;
  background-clip: text;
  -webkit-text-fill-color: transparent;
  color: transparent;
  filter: drop-shadow(0 6px 14px var(--bm-shadow-color));
}

.hero-bio {
  margin: 12px 0 30px;
  font-size: 15.5px;
  color: var(--bm-text-sub);
}

/* 随机一句 */
.quote {
  margin: 0 auto;
  font-size: 19px;
  line-height: 1.7;
  font-weight: 600;
  color: var(--bm-text);
  letter-spacing: 0.3px;
  max-width: 560px;
}

.enter-btn {
  margin-top: 34px;
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 12px 30px;
  border: none;
  border-radius: 999px;
  background: var(--bm-gradient);
  color: #fff;
  font-size: 15px;
  font-weight: 700;
  cursor: pointer;
  box-shadow: 0 10px 26px var(--bm-shadow-color);
  transition: transform 0.3s var(--bm-ease-bounce), box-shadow 0.3s var(--bm-ease),
    filter 0.3s var(--bm-ease);
}

.enter-btn:hover {
  transform: translateY(-4px) scale(1.03);
  box-shadow: 0 18px 36px var(--bm-shadow-color);
  filter: brightness(1.05);
}

.enter-btn .el-icon {
  animation: bob 1.6s ease-in-out infinite;
}

/* 首屏快捷导航（胶囊） */
.hero-links {
  margin-top: 28px;
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: 12px;
}

.hero-links a {
  padding: 7px 18px;
  border-radius: 999px;
  font-size: 13.5px;
  font-weight: 600;
  color: var(--bm-text-sub);
  background: rgba(255, 255, 255, 0.66);
  border: 1px solid var(--bm-border);
  backdrop-filter: blur(6px);
  transition: all 0.25s var(--bm-ease-bounce);
}

.hero-links a:hover {
  color: #fff;
  background: var(--bm-gradient);
  border-color: transparent;
  transform: translateY(-3px);
  box-shadow: 0 10px 20px var(--bm-shadow-color);
}

.scroll-hint {
  position: absolute;
  bottom: 26px;
  left: 50%;
  transform: translateX(-50%);
  z-index: 2;
  font-size: 26px;
  color: var(--bm-primary-2);
  cursor: pointer;
  opacity: 0.65;
  animation: bob 1.8s ease-in-out infinite;
}

.scroll-hint:hover {
  opacity: 1;
}

/* ---------- 动画 ---------- */
@keyframes bob {
  0%,
  100% {
    transform: translateY(0);
  }
  50% {
    transform: translateY(4px);
  }
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

@keyframes twinkle {
  0%,
  100% {
    opacity: 0.35;
    transform: scale(0.9);
  }
  50% {
    opacity: 1;
    transform: scale(1.15);
  }
}

@keyframes twinkle-scale {
  0%,
  100% {
    opacity: 0.3;
    transform: scale(0.8) rotate(0deg);
  }
  50% {
    opacity: 1;
    transform: scale(1.25) rotate(180deg);
  }
}

@keyframes orb-a {
  0%,
  100% {
    transform: translate(0, 0);
  }
  50% {
    transform: translate(40px, 28px);
  }
}

@keyframes orb-b {
  0%,
  100% {
    transform: translate(0, 0);
  }
  50% {
    transform: translate(-36px, -26px);
  }
}

/* ---------- 深色适配 ---------- */
html.dark .hero {
  background: linear-gradient(
      160deg,
      rgba(20, 18, 31, 0.82) 0%,
      rgba(20, 18, 31, 0.86) 55%,
      rgba(38, 24, 52, 0.82) 100%
    ),
    var(--hero-bg) center / cover no-repeat;
}

html.dark .hero-banner::after {
  background: linear-gradient(
    160deg,
    rgba(20, 18, 31, 0.74) 0%,
    rgba(20, 18, 31, 0.8) 55%,
    rgba(38, 24, 52, 0.74) 100%
  );
  mask-image: linear-gradient(
    to bottom,
    #000 0%,
    #000 60%,
    transparent 100%
  );
  -webkit-mask-image: linear-gradient(
    to bottom,
    #000 0%,
    #000 60%,
    transparent 100%
  );
}

html.dark .hero-links a {
  background: rgba(255, 255, 255, 0.1);
  color: var(--bm-text-sub);
  border-color: rgba(255, 255, 255, 0.14);
}

html.dark .hero-links a:hover {
  color: #fff;
  background: var(--bm-gradient);
  border-color: transparent;
}

/* ---------- 响应式 ---------- */
@media (max-width: 640px) {
  .hero-title {
    font-size: 33px;
  }
  .quote {
    font-size: 16px;
  }
  .hero-links {
    gap: 8px;
  }
  .hero-links a {
    padding: 6px 14px;
    font-size: 12.5px;
  }
}

@media (prefers-reduced-motion: reduce) {
  .orb,
  .star,
  .halo,
  .halo-2,
  .enter-btn .el-icon,
  .scroll-hint {
    animation: none;
  }
}
</style>
