import { defineStore } from 'pinia'
import { getCategories, getPosts, getProfile, getSiteInfo } from '@/api'

export const useSiteStore = defineStore('site', {
  state: () => ({
    site: {},
    profile: {},
    categories: [],
    hotPosts: [],
    _loaded: false,
    _loading: false,
  }),
  getters: {
    avatar: (s) => s.profile?.avatar || '',
    nickname: (s) => s.profile?.nickname || s.site?.title || '',
  },
  actions: {
    async load(force = false) {
      if (this._loaded && !force) return
      if (this._loading) return
      this._loading = true
      try {
        const [site, profile, categories] = await Promise.all([
          getSiteInfo(),
          getProfile().catch(() => ({})),
          getCategories(),
        ])
        let hotPosts = []
        try {
          const res = await getPosts({ page: 1, page_size: 5, order_by: 'views' })
          hotPosts = res.list || []
        } catch {
          hotPosts = []
        }
        this.site = site
        this.profile = profile
        this.categories = categories
        this.hotPosts = hotPosts
        this._loaded = true
      } finally {
        this._loading = false
      }
    },
    async refresh() {
      return this.load(true)
    },
    async refreshProfile() {
      // 只刷新资料（头像更新时用）
      try {
        const profile = await getProfile()
        this.profile = profile
      } catch {
        /* 忽略 */
      }
    },
    reset() {
      this._loaded = false
    },
  },
})
