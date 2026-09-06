<template>
  <div class="login-page">
    <!-- 装饰光斑 -->
    <div class="deco" aria-hidden="true">
      <span class="orb orb-a"></span>
      <span class="orb orb-b"></span>
      <span class="orb orb-c"></span>
      <span class="sp sp-1">✦</span>
      <span class="sp sp-2">✧</span>
      <span class="sp sp-3">✦</span>
      <span class="sp sp-4">✧</span>
    </div>

    <div class="box">
      <div class="brand">
        <h1>BlueMoonの博客</h1>
        <p>后台管理</p>
      </div>

      <el-form ref="formRef" :model="form" :rules="rules" size="large" @keyup.enter="onSubmit">
        <el-form-item prop="username">
          <el-input v-model="form.username" placeholder="用户名" :prefix-icon="User" />
        </el-form-item>
        <el-form-item prop="password">
          <el-input
            v-model="form.password"
            type="password"
            placeholder="密码"
            show-password
            :prefix-icon="Lock"
          />
        </el-form-item>
        <el-button type="primary" size="large" class="submit" :loading="loading" @click="onSubmit">
          登 录
        </el-button>
      </el-form>

      <div class="tip">
        默认账号 <code>admin</code> / 密码 <code>admin123</code>
      </div>
      <el-link :underline="false" class="back" @click="$router.push('/')">← 返回前台</el-link>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Lock, User } from '@element-plus/icons-vue'
import { login } from '@/api'
import { useUserStore } from '@/stores/user'

const route = useRoute()
const router = useRouter()
const store = useUserStore()

const formRef = ref()
const loading = ref(false)
const form = ref({ username: '', password: '' })

const rules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }],
}

// 安全校验：redirect 只允许站内路径（以 / 开头且非 //，防开放重定向）
function safeRedirect() {
  const r = route.query.redirect
  if (typeof r === 'string' && r.startsWith('/') && !r.startsWith('//')) return r
  return '/admin'
}

async function onSubmit() {
  await formRef.value.validate(async (valid) => {
    if (!valid) return
    loading.value = true
    try {
      const data = await login(form.value)
      store.setAuth(data)
      ElMessage.success(`欢迎回来，${data.user.nickname || data.user.username}`)
      router.push(safeRedirect())
    } catch {
      /* 拦截器已提示 */
    } finally {
      loading.value = false
    }
  })
}
</script>

<style scoped>
.login-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--bm-gradient);
  padding: 20px;
  position: relative;
  overflow: hidden;
}

/* 装饰光斑与星点 */
.deco {
  position: absolute;
  inset: 0;
  pointer-events: none;
  z-index: 0;
}

.orb {
  position: absolute;
  border-radius: 50%;
  filter: blur(70px);
  opacity: 0.55;
}

.orb-a {
  width: 420px;
  height: 420px;
  top: -160px;
  left: -120px;
  background: radial-gradient(circle, rgba(255, 255, 255, 0.5), transparent 70%);
  animation: drift-a 18s ease-in-out infinite;
}

.orb-b {
  width: 460px;
  height: 460px;
  bottom: -180px;
  right: -140px;
  background: radial-gradient(circle, rgba(255, 255, 255, 0.4), transparent 70%);
  animation: drift-b 22s ease-in-out infinite;
}

.orb-c {
  width: 300px;
  height: 300px;
  top: 50%;
  right: 5%;
  background: radial-gradient(circle, rgba(255, 255, 255, 0.3), transparent 70%);
  animation: drift-a 28s ease-in-out infinite;
}

.sp {
  position: absolute;
  color: rgba(255, 255, 255, 0.8);
  font-size: 18px;
  animation: twinkle 3s ease-in-out infinite;
}

.sp-1 { top: 20%; left: 16%; }
.sp-2 { top: 28%; right: 20%; animation-delay: 0.8s; }
.sp-3 { bottom: 24%; left: 28%; animation-delay: 1.5s; }
.sp-4 { bottom: 18%; right: 16%; animation-delay: 2.2s; font-size: 14px; }

@keyframes drift-a {
  0%, 100% { transform: translate(0, 0); }
  50% { transform: translate(30px, 22px); }
}

@keyframes drift-b {
  0%, 100% { transform: translate(0, 0); }
  50% { transform: translate(-28px, -20px); }
}

@keyframes twinkle {
  0%, 100% { opacity: 0.35; transform: scale(0.9); }
  50% { opacity: 1; transform: scale(1.15); }
}

.box {
  width: 380px;
  padding: 44px 38px 30px;
  background: rgba(255, 255, 255, 0.96);
  backdrop-filter: blur(20px);
  border-radius: 24px;
  box-shadow: 0 24px 60px rgba(44, 47, 58, 0.22);
  position: relative;
  z-index: 1;
  overflow: hidden;
  animation: box-in 0.5s var(--bm-ease-bounce);
}

@keyframes box-in {
  from { opacity: 0; transform: translateY(20px) scale(0.96); }
  to { opacity: 1; transform: translateY(0) scale(1); }
}

html.dark .box {
  background: rgba(27, 24, 40, 0.96);
  box-shadow: 0 24px 60px rgba(0, 0, 0, 0.5);
}

.box::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 5px;
  background: var(--bm-gradient);
}

.brand {
  text-align: center;
  margin-bottom: 30px;
}

.brand h1 {
  margin: 0 0 2px;
  font-size: 26px;
  font-weight: 800;
  letter-spacing: 1.2px;
  background: var(--bm-gradient);
  -webkit-background-clip: text;
  background-clip: text;
  -webkit-text-fill-color: transparent;
  color: transparent;
  filter: drop-shadow(0 3px 8px var(--bm-shadow-color));
}

.brand p {
  margin: 0;
  font-size: 13px;
  color: var(--bm-text-sub);
}

.submit {
  width: 100%;
  margin-top: 6px;
  border-radius: 14px;
  font-weight: 700;
  letter-spacing: 2px;
  transition: transform 0.25s var(--bm-ease-bounce), box-shadow 0.25s var(--bm-ease),
    filter 0.25s var(--bm-ease);
}

.submit:hover {
  transform: translateY(-2px);
  filter: brightness(1.05);
}

/* 输入框聚焦时的渐变光晕 */
.box :deep(.el-input__wrapper.is-focus) {
  box-shadow: 0 0 0 1px var(--bm-primary-2) inset, 0 0 16px rgba(184, 146, 246, 0.15);
}

.box :deep(.el-input__wrapper) {
  border-radius: 12px;
  transition: box-shadow 0.3s var(--bm-ease);
}

.tip {
  margin-top: 18px;
  text-align: center;
  font-size: 12.5px;
  color: var(--bm-text-sub);
}

.tip code {
  background: var(--bm-primary-soft);
  padding: 1px 6px;
  border-radius: 4px;
  color: var(--bm-primary-2);
  font-weight: 600;
}

.back {
  display: block;
  margin-top: 14px;
  text-align: center;
  font-size: 13px;
  color: var(--bm-text-sub);
}

@media (prefers-reduced-motion: reduce) {
  .orb, .sp, .box {
    animation: none;
  }
}
</style>
