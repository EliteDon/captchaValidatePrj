import axios from 'axios'

const apiClient = axios.create({
  baseURL: '/api',
  timeout: 10000
})

apiClient.interceptors.response.use(
  response => response,
  error => {
    const message = error.response?.data?.message || error.message || '请求失败'
    return Promise.reject(new Error(message))
  }
)

export const post = (url, data) => apiClient.post(url, data)
export const get = (url, params) => apiClient.get(url, { params })
export const del = (url, data) => apiClient.delete(url, { data })

export default apiClient
