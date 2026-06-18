import axios from 'axios'

const api = axios.create({ baseURL: '/api', timeout: 30000 })

export const getSiteOptions = () => api.get('/charts/sites')
export const getStats = () => api.get('/stats')
export const getChartsCatalog = (source) => api.get('/charts/catalog', { params: { source } })
export const getLatestChart = (params) => api.get('/charts/latest', { params })
export const getAllLatestCharts = (source, limit = 20) => api.get('/charts/latest/all', { params: { source, limit } })
export const getRecommendTags = () => api.get('/recommend/tags')
export const recommendPlaylists = (data) => api.post('/recommend/playlists', data)
export const getTasks = (params) => api.get('/tasks', { params })
export const getTask = (id) => api.get(`/tasks/${id}`)
export const createTask = (data) => api.post('/tasks', data)
export const pauseTask = (id) => api.patch(`/tasks/${id}/pause`)
export const resumeTask = (id) => api.patch(`/tasks/${id}/resume`)
export const cancelTask = (id) => api.patch(`/tasks/${id}/cancel`)
export const getTracks = (params) => api.get('/data/tracks', { params })
export const getArtists = (params) => api.get('/data/artists', { params })
export const getRecommend = (source) => api.get('/tasks/recommend/types', { params: { source } })
export const exportData = (params) => `/api/export?${new URLSearchParams(params)}`
export const getArchitecture = () => api.get('/diagrams/architecture')
export const getBusinessFlow = () => api.get('/diagrams/business-flow')

export function connectLogs(taskId, onMessage) {
  const protocol = location.protocol === 'https:' ? 'wss:' : 'ws:'
  const ws = new WebSocket(`${protocol}//${location.host}/ws/logs/${taskId}`)
  ws.onmessage = (e) => {
    const data = JSON.parse(e.data)
    if (data.type !== 'ping') onMessage(data)
  }
  return ws
}

export default api
