import request from './request'

/* ---------------- 文章 ---------------- */
export const getPosts = (params) => request.get('/posts', { params })
export const getPostBySlug = (slug) =>
  request.get(`/posts/detail/${encodeURIComponent(slug)}`)
export const getPostById = (id) => request.get(`/posts/${id}`)
export const recordView = (postId) => request.post(`/posts/${postId}/view`)
export const getAdminPosts = (params) => request.get('/posts/admin', { params })
export const createPost = (data) => request.post('/posts', data)
export const updatePost = (id, data) => request.put(`/posts/${id}`, data)
export const deletePost = (id) => request.delete(`/posts/${id}`)
export const getArchives = () => request.get('/posts/archives')

/* ---------------- 分类 ---------------- */
export const getCategories = () => request.get('/categories')
export const createCategory = (data) => request.post('/categories', data)
export const updateCategory = (id, data) => request.put(`/categories/${id}`, data)
export const deleteCategory = (id) => request.delete(`/categories/${id}`)

/* ---------------- 认证 ---------------- */
export const login = (data) => request.post('/auth/login', data)
export const logout = () => request.post('/auth/logout')
export const getMe = () => request.get('/auth/me')
export const updateMe = (data) => request.put('/auth/me', data)
export const changePassword = (data) => request.put('/auth/password', data)
export const uploadAvatar = (file) => {
  const form = new FormData()
  form.append('file', file)
  return request.post('/auth/avatar', form, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
}
// 历史头像：列表（按时间倒序，含 is_current 标记）/ 恢复 / 删除
export const getAvatarHistory = () => request.get('/auth/avatars')
export const restoreAvatar = (id) => request.post('/auth/avatar/restore', { id })
export const deleteAvatar = (id) => request.delete(`/auth/avatar/${id}`)

/* ---------------- 统计 / 站点 ---------------- */
export const getSiteInfo = () => request.get('/stats/site')
export const getOverview = () => request.get('/stats/overview')
export const getProfile = () => request.get('/profile')
export const updateProfile = (data) => request.put('/profile', data)
export const flushViews = () => request.post('/posts/flush-views')
export const getCacheInfo = () => request.get('/cache/info')
export const flushCache = () => request.post('/stats/cache/flush')

/* ---------------- 上传 ---------------- */
// scope: 'post' = 文章图片（仅随文章展示，不进图库）；'gallery' = 图库图片（展示在图片栏）
export const uploadImage = (file, scope = 'gallery') => {
  const form = new FormData()
  form.append('file', file)
  return request.post('/upload/image', form, {
    params: { scope },
    headers: { 'Content-Type': 'multipart/form-data' },
  })
}
export const getImages = () => request.get('/upload/images')
export const deleteImage = (url, force = false) =>
  request.delete('/upload/image', { params: { url, force } })
export const batchDeleteImages = (urls, force = false) =>
  request.post('/upload/image/batch-delete', { urls }, { params: { force } })
export const checkImageRefs = (urls) =>
  request.post('/upload/image/check-refs', { urls })
