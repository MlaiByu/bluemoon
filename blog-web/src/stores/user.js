import { defineStore } from 'pinia'
import { getMe } from '@/api'

const TOKEN_KEY = 'bm_token'
const USER_KEY = 'bm_user'

export const useUserStore = defineStore('user', {
  state: () => ({
    token: localStorage.getItem(TOKEN_KEY) || '',
    user: JSON.parse(localStorage.getItem(USER_KEY) || 'null'),
  }),
  getters: {
    isLogin: (s) => !!s.token,
    nickname: (s) => s.user?.nickname || s.user?.username || '',
    avatar: (s) => s.user?.avatar || '',
  },
  actions: {
    setAuth(data) {
      this.token = data.access_token
      this.user = data.user
      localStorage.setItem(TOKEN_KEY, this.token)
      localStorage.setItem(USER_KEY, JSON.stringify(this.user))
    },
    async fetchMe() {
      if (!this.token) return null
      try {
        this.user = await getMe()
        localStorage.setItem(USER_KEY, JSON.stringify(this.user))
        return this.user
      } catch {
        this.clear()
        return null
      }
    },
    updateUser(data) {
      // 部分更新用户信息，并同步到 localStorage
      if (!this.user) {
        this.user = { ...data }
      } else {
        this.user = { ...this.user, ...data }
      }
      localStorage.setItem(USER_KEY, JSON.stringify(this.user))
    },
    clear() {
      this.token = ''
      this.user = null
      localStorage.removeItem(TOKEN_KEY)
      localStorage.removeItem(USER_KEY)
    },
  },
})
