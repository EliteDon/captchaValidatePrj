import axios from 'axios'

const http = axios.create({ baseURL: '/api', timeout: 10000 })

export const get = (url, params) => http.get(url, { params })
export const post = (url, data) => http.post(url, data)
export const del = (url, data) => http.delete(url, { data })

export default http
