<template>
  <div v-loading="loading" class="profile-admin bm-fade-up">
    <el-row :gutter="16">
      <!-- 站点资料 -->
      <el-col :xs="24" :lg="14">
        <div class="bm-card panel">
          <h3 class="block-title"><i class="dot"></i>关于我</h3>
          <el-form :model="profile" label-width="80px">
            <el-form-item label="昵称">
              <el-input v-model="profile.nickname" maxlength="50" />
            </el-form-item>
            <el-form-item label="一句话">
              <el-input v-model="profile.bio" maxlength="500" placeholder="显示在名片下方" />
            </el-form-item>
            <el-form-item label="正文">
              <MarkdownEditor v-model="profile.content" placeholder="用 Markdown 写自我介绍…" />
            </el-form-item>
          </el-form>
        </div>
      </el-col>

      <!-- 联系方式 + 账号 -->
      <el-col :xs="24" :lg="10">
        <div class="bm-card panel">
          <h3 class="block-title"><i class="dot"></i>联系方式</h3>
          <el-form :model="profile" label-width="80px">
            <el-form-item label="所在地">
              <el-input v-model="profile.location" maxlength="100" />
            </el-form-item>
            <el-form-item label="邮箱">
              <el-input v-model="profile.email" maxlength="120" />
            </el-form-item>
            <el-form-item label="网站">
              <el-input v-model="profile.website" maxlength="200" placeholder="https://" />
            </el-form-item>
            <el-form-item label="GitHub">
              <el-input v-model="profile.github" maxlength="200" placeholder="https://github.com/xxx" />
            </el-form-item>
            <el-form-item label="微信">
              <el-input v-model="profile.wechat" maxlength="100" />
            </el-form-item>
            <el-form-item label="QQ">
              <el-input v-model="profile.qq" maxlength="50" />
            </el-form-item>
          </el-form>
          <div class="ops">
            <el-button type="primary" :icon="Check" :loading="saving" @click="saveProfile">保存资料</el-button>
          </div>
        </div>

        <div class="bm-card panel">
          <h3 class="block-title"><i class="dot"></i>账号信息</h3>

          <!-- 账号头像 -->
          <div class="account-avatar-section">
            <div class="avatar-upload-wrap large">
              <el-upload
                :show-file-list="false"
                :before-upload="beforeAccountAvatarUpload"
                :http-request="onAccountAvatarUpload"
                accept="image/jpeg,image/png,image/gif,image/webp"
              >
                <div class="avatar-box large">
                  <el-avatar v-if="accountAvatarUrl" :size="100" :src="accountAvatarUrl" class="avatar-img" />
                  <div v-else class="avatar-placeholder large">
                    <span class="default-avatar-text">{{ avatarText }}</span>
                  </div>
                  <div v-if="accountAvatarUploading" class="avatar-mask">
                    <el-icon class="mask-icon"><Loading /></el-icon>
                    <span>上传中…</span>
                  </div>
                  <div class="avatar-hover-mask">
                    <el-icon :size="24"><Camera /></el-icon>
                    <span>更换头像</span>
                  </div>
                </div>
              </el-upload>
            </div>
            <div class="avatar-info">
              <div class="avatar-name">{{ account.nickname || user?.username || '博主' }}</div>
              <div class="avatar-desc">支持 JPG / PNG / GIF / WebP，最大 5MB</div>
              <div class="avatar-desc">系统会自动压缩到 512px 以内</div>
            </div>
          </div>

          <el-form :model="account" label-width="80px" class="account-form">
            <el-form-item label="用户名">
              <el-input :model-value="user?.username" disabled />
            </el-form-item>
            <el-form-item label="昵称">
              <el-input v-model="account.nickname" />
            </el-form-item>
            <el-form-item label="邮箱">
              <el-input v-model="account.email" />
            </el-form-item>
            <el-form-item label="简介">
              <el-input v-model="account.bio" type="textarea" :rows="2" maxlength="500" />
            </el-form-item>
          </el-form>
          <div class="ops">
            <el-button :icon="Check" :loading="savingAccount" @click="saveAccount">保存账号</el-button>
            <el-button type="warning" :icon="Key" @click="pwdDialog = true">修改密码</el-button>
          </div>
        </div>
      </el-col>
    </el-row>

    <!-- 修改密码 -->
    <el-dialog v-model="pwdDialog" title="修改密码" width="400px">
      <el-form :model="pwd" label-width="90px">
        <el-form-item label="原密码">
          <el-input v-model="pwd.old_password" type="password" show-password />
        </el-form-item>
        <el-form-item label="新密码">
          <el-input v-model="pwd.new_password" type="password" show-password placeholder="至少 6 位" />
        </el-form-item>
        <el-form-item label="确认密码">
          <el-input v-model="pwd.confirm" type="password" show-password />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="pwdDialog = false">取消</el-button>
        <el-button type="primary" :loading="savingPwd" @click="savePwd">确认修改</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { Camera, Check, Key, Loading } from '@element-plus/icons-vue'
import MarkdownEditor from '@/components/MarkdownEditor.vue'
import {
  changePassword, getProfile, updateMe, updateProfile, uploadAvatar,
} from '@/api'
import { useUserStore } from '@/stores/user'
import { useSiteStore } from '@/stores/site'

const store = useUserStore()
const siteStore = useSiteStore()
const user = ref(store.user)

const loading = ref(false)
const saving = ref(false)
const savingAccount = ref(false)
const savingPwd = ref(false)
const pwdDialog = ref(false)

// 上传状态
const accountAvatarUploading = ref(false)

// 保存上传前的头像 URL，用于失败回退
const _backupAccountAvatar = ref('')

const profile = reactive({
  nickname: '', bio: '', content: '', location: '',
  email: '', website: '', github: '', wechat: '', qq: '',
})
const account = reactive({ nickname: '', email: '', bio: '', avatar: '' })
const pwd = reactive({ old_password: '', new_password: '', confirm: '' })

const accountAvatarUrl = computed(() => account.avatar || user.value?.avatar || '')

const avatarText = computed(() => {
  const name = account.nickname || user.value?.nickname || user.value?.username || 'B'
  return name.slice(0, 1).toUpperCase()
})

// 前端图片校验：格式 + 大小
function validateImage(file) {
  const allowedTypes = ['image/jpeg', 'image/png', 'image/gif', 'image/webp']
  const allowedExts = ['jpg', 'jpeg', 'png', 'gif', 'webp']

  // 类型校验
  const ext = file.name.split('.').pop()?.toLowerCase() || ''
  if (!allowedTypes.includes(file.type) && !allowedExts.includes(ext)) {
    ElMessage.error('不支持的图片格式，请上传 JPG / PNG / GIF / WebP 格式的图片')
    return false
  }

  // 大小校验（5MB）
  const maxSize = 5 * 1024 * 1024
  if (file.size > maxSize) {
    ElMessage.error('图片太大了，不能超过 5MB')
    return false
  }

  return true
}

async function load() {
  loading.value = true
  try {
    const p = await getProfile()
    Object.keys(profile).forEach((k) => {
      profile[k] = p[k] ?? ''
    })
    user.value = store.user
    account.nickname = store.user?.nickname || ''
    account.email = store.user?.email || ''
    account.bio = store.user?.bio || ''
    account.avatar = store.user?.avatar || ''
  } finally {
    loading.value = false
  }
}

async function saveProfile() {
  saving.value = true
  try {
    await updateProfile({ ...profile })
    // 同步刷新前台 site store
    siteStore.refresh()
    ElMessage.success('站点资料已保存')
  } catch {
    /* 拦截器已提示 */
  } finally {
    saving.value = false
  }
}

async function saveAccount() {
  savingAccount.value = true
  try {
    const updated = await updateMe({ ...account })
    store.updateUser(updated)
    user.value = store.user
    account.avatar = updated.avatar || account.avatar
    // 同步刷新前台 site store
    siteStore.refreshProfile()
    ElMessage.success('账号信息已保存')
  } catch {
    /* 拦截器已提示 */
  } finally {
    savingAccount.value = false
  }
}

async function savePwd() {
  if (pwd.new_password.length < 6) {
    ElMessage.warning('新密码至少 6 位')
    return
  }
  if (pwd.new_password !== pwd.confirm) {
    ElMessage.warning('两次输入的新密码不一致')
    return
  }
  savingPwd.value = true
  try {
    await changePassword({ old_password: pwd.old_password, new_password: pwd.new_password })
    ElMessage.success('密码已修改')
    pwdDialog.value = false
    pwd.old_password = pwd.new_password = pwd.confirm = ''
  } catch {
    /* 拦截器已提示 */
  } finally {
    savingPwd.value = false
  }
}

/* ---------- 账号头像上传 ---------- */
function beforeAccountAvatarUpload(file) {
  if (!validateImage(file)) return false
  _backupAccountAvatar.value = accountAvatarUrl.value
  accountAvatarUploading.value = true
  return true
}

async function onAccountAvatarUpload({ file }) {
  try {
    const res = await uploadAvatar(file)
    const url = res?.url
    if (url) {
      account.avatar = url
      // 同步更新 user store 和 localStorage
      store.updateUser({ avatar: url })
      user.value = store.user
      // 同步刷新前台 site store，保证前台头像立即更新
      siteStore.refreshProfile()
      ElMessage.success('头像已更新')
    } else {
      throw new Error('上传失败')
    }
  } catch {
    // 失败回退（错误提示已由请求拦截器统一处理）
    account.avatar = _backupAccountAvatar.value
  } finally {
    accountAvatarUploading.value = false
  }
}

onMounted(async () => {
  if (!store.user) await store.fetchMe()
  await load()
})
</script>

<style scoped>
.profile-admin {
  position: relative;
}

.block-title {
  display: flex;
  align-items: center;
  gap: 9px;
  margin: 0 0 18px;
  font-size: 16px;
  font-weight: 700;
  line-height: 1.2;
}

.block-title .dot {
  width: 9px;
  height: 9px;
  border-radius: 3px;
  background: var(--bm-gradient);
  transform: rotate(45deg);
  box-shadow: 0 3px 8px var(--bm-shadow-color);
}

/* ========== 头像上传组件 ========== */
.avatar-row {
  display: flex;
  align-items: center;
  gap: 16px;
  width: 100%;
}

.avatar-upload-wrap {
  flex-shrink: 0;
}

.avatar-upload-wrap :deep(.el-upload) {
  cursor: pointer;
  line-height: 0;
}

.avatar-box {
  position: relative;
  width: 80px;
  height: 80px;
  border-radius: 50%;
  overflow: hidden;
  transition: transform 0.3s var(--bm-ease-bounce);
}

.avatar-box.large {
  width: 100px;
  height: 100px;
}

.avatar-box:hover {
  transform: scale(1.04);
}

.avatar-img {
  width: 100%;
  height: 100%;
  display: block;
}

.avatar-placeholder {
  width: 80px;
  height: 80px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 2px dashed var(--bm-border);
  border-radius: 50%;
  color: var(--bm-text-mute);
  background: var(--bm-primary-soft);
  transition: all 0.3s var(--bm-ease);
}

.avatar-placeholder.large {
  width: 100px;
  height: 100px;
}

.avatar-box:hover .avatar-placeholder {
  border-color: var(--bm-primary-2);
  color: var(--bm-primary-2);
}

.default-avatar-text {
  font-size: 36px;
  font-weight: 800;
  background: var(--bm-gradient);
  -webkit-background-clip: text;
  background-clip: text;
  -webkit-text-fill-color: transparent;
}

/* 悬停遮罩 */
.avatar-hover-mask {
  position: absolute;
  inset: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 4px;
  background: rgba(0, 0, 0, 0.45);
  color: #fff;
  font-size: 12px;
  opacity: 0;
  transition: opacity 0.25s var(--bm-ease);
  backdrop-filter: blur(2px);
}

.avatar-box:hover .avatar-hover-mask {
  opacity: 1;
}

/* 上传中遮罩 */
.avatar-mask {
  position: absolute;
  inset: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 6px;
  background: rgba(0, 0, 0, 0.55);
  color: #fff;
  font-size: 12px;
  z-index: 5;
  backdrop-filter: blur(3px);
}

.mask-icon {
  font-size: 22px;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.avatar-tip {
  margin-top: 8px;
  font-size: 12px;
  color: var(--bm-text-mute);
  text-align: center;
}

.avatar-url {
  flex: 1;
}

/* ========== 账号头像区 ========== */
.account-avatar-section {
  display: flex;
  align-items: center;
  gap: 18px;
  padding: 14px 16px;
  margin-bottom: 18px;
  background: linear-gradient(135deg, rgba(138, 182, 255, 0.08) 0%, rgba(255, 176, 200, 0.08) 100%);
  border-radius: var(--bm-radius-sm);
  border: 1px solid var(--bm-border);
}

.avatar-info {
  flex: 1;
  min-width: 0;
}

.avatar-name {
  font-size: 17px;
  font-weight: 700;
  color: var(--bm-text);
  margin-bottom: 4px;
}

.avatar-desc {
  font-size: 12px;
  color: var(--bm-text-sub);
  line-height: 1.6;
}

.account-form {
  margin-top: 6px;
}

.ops {
  display: flex;
  gap: 10px;
  padding-top: 6px;
}

/* ========== 深色模式 ========== */
html.dark .account-avatar-section {
  background: linear-gradient(135deg, rgba(143, 157, 255, 0.1) 0%, rgba(239, 143, 180, 0.1) 100%);
}

html.dark .avatar-placeholder {
  background: var(--bm-primary-soft);
}

/* ========== 响应式 ========== */
@media (max-width: 640px) {
  .avatar-row {
    flex-direction: column;
    align-items: flex-start;
  }

  .avatar-url {
    width: 100%;
  }
}
</style>
