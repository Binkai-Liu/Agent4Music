export const SITE_OPTIONS = [
  { value: 'qq', label: 'QQ音乐', icon: '🎵', color: '#1e6fff' },
  { value: 'netease', label: '网易云音乐', icon: '☁️', color: '#d33a31' },
]

export const DEFAULT_SOURCE = 'qq'

export function getSiteLabel(source) {
  return SITE_OPTIONS.find(s => s.value === source)?.label || source
}

export const CHART_TYPE_LABELS = {
  hot: '热歌榜',
  new: '新歌榜',
  surge: '飙升榜',
  original: '原创榜',
  pop: '流行指数',
  electronic: '电音榜',
}

export const MOOD_PRESETS = [
  { name: '治愈午后', genres: ['流行', '民谣'], scenes: ['治愈'] },
  { name: '燃脂运动', genres: ['电子', '摇滚'], scenes: ['运动', '热血'] },
  { name: '古风日常', genres: ['古风'], scenes: ['怀旧'] },
  { name: '深夜安眠', genres: ['纯音乐', '民谣'], scenes: ['睡前', '治愈'] },
  { name: '说唱潮流', genres: ['说唱'], scenes: ['热血'] },
]

export const PAGE_META = {
  '/': { title: '仪表盘', desc: '数据总览与快捷操作' },
  '/charts': { title: '最新榜单', desc: '实时拉取 QQ / 网易云各类榜单' },
  '/recommend': { title: '喜好推荐', desc: '拖拽或点选喜好，智能匹配歌单' },
  '/tasks/new': { title: '创建任务', desc: '配置并启动数据采集任务' },
  '/data': { title: '数据浏览', desc: '检索、预览已采集的音乐数据' },
  '/export': { title: '数据导出', desc: '导出 CSV / JSON / Excel' },
}
