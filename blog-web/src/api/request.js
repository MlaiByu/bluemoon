import axios from 'axios'
import { ElMessage } from 'element-plus/es/components/message/index'

const request = axios.create({
  baseURL: import.meta.env.VITE_API_BASE || '/api/v1',
  timeout: 20000,
})

// 请求拦截：自动带上 token
request.interceptors.request.use((config) => {
  const token = localStorage.getItem('bm_token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

// 响应拦截：统一拆包 / 报错
request.interceptors.response.use(
  (response) => {
    const res = response.data
    // 非标准结构（如二进制）直接返回
    if (!res || typeof res !== 'object' || !('code' in res)) return res
    if (res.code === 0) return res.data
    ElMessage.error(res.msg || '请求失败')
    return Promise.reject(new Error(res.msg || '请求失败'))
  },
  (error) => {
    const status = error.response?.status
    const msg = error.response?.data?.msg || error.message || '网络异常'

    if (status === 401) {
      localStorage.removeItem('bm_token')
      // 后台页面未登录则跳登录页（history 模式下用 pathname 判断）
      if (location.pathname.startsWith('/admin')) {
        ElMessage.warning('登录已过期，请重新登录')
        const redirect = encodeURIComponent(location.pathname + location.search)
        window.location.assign(`/admin/login?redirect=${redirect}`)
      }
    } else if (status === 403) {
      ElMessage.error('没有权限执行该操作')
    } else if (status === 429) {
      ElMessage.error(msg)
    } else if (status >= 500) {
      ElMessage.error('服务器开小差了，请稍后再试')
    } else if (status !== 401) {
      ElMessage.error(msg)
    }
    return Promise.reject(error)
  }
)

export default request
