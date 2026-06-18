<template>
  <div class="space-y-6">
    <!-- 心情预设 + 站点偏好 -->
    <div class="card">
      <div class="flex flex-wrap gap-4 items-center justify-between">
        <div>
          <span class="text-sm text-gray-500 mr-3">快捷心情</span>
          <el-button
            v-for="preset in MOOD_PRESETS"
            :key="preset.name"
            size="small"
            round
            @click="applyPreset(preset)"
          >
            {{ preset.name }}
          </el-button>
        </div>
        <div class="flex items-center gap-2">
          <span class="text-sm text-gray-500">偏好站点</span>
          <SourceSelect v-model="preferSource" width="160px" clearable placeholder="不限站点" />
        </div>
      </div>
      <p class="form-tip mt-2">点击心情预设快速填充，也可拖拽/点击标签自定义 · 拖拽歌曲增加权重</p>
    </div>

    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <div class="card">
        <h3 class="font-bold mb-2">音乐标签库</h3>
        <p class="text-sm text-gray-500 mb-4">点击或拖拽到右侧 · 排序越靠前权重越高</p>
        <div class="flex flex-wrap gap-2">
          <div
            v-for="tag in availableTags"
            :key="tag.id"
            class="pref-chip"
            :class="{ 'pref-chip-active': isTagSelected(tag.id) }"
            :style="{ borderColor: tag.color, color: tag.color }"
            draggable="true"
            @click="addTag(tag)"
            @dragstart="onDragStart($event, tag)"
          >
            {{ tag.id }}
            <span class="text-xs opacity-60 ml-1">{{ tag.type === 'genre' ? '曲风' : '场景' }}</span>
          </div>
        </div>

        <h4 class="font-semibold mt-6 mb-2">从曲库添加</h4>
        <div class="flex gap-2 mb-3">
          <SourceSelect v-model="searchSource" width="140px" clearable placeholder="全部站点" />
          <el-input v-model="search" placeholder="搜索歌曲" clearable @keyup.enter="searchTracks" />
          <el-button @click="searchTracks">搜索</el-button>
        </div>
        <div class="space-y-2 max-h-48 overflow-y-auto">
          <div
            v-for="t in searchResults"
            :key="t.track_id + t.source"
            class="pref-track-item"
            draggable="true"
            @click="addTrack(t)"
            @dragstart="onDragTrack($event, t)"
          >
            <el-tag size="small" type="info">{{ getSiteLabel(t.source) }}</el-tag>
            <span class="font-medium ml-2">{{ t.title }}</span>
            <span class="text-xs text-gray-500 ml-2">{{ (t.artists || []).join('/') }}</span>
          </div>
          <EmptyState v-if="search && !searchResults.length" icon="🔍" title="未找到歌曲" />
        </div>
      </div>

      <div class="card">
        <div class="flex justify-between items-center mb-2">
          <h3 class="font-bold">我的音乐喜好</h3>
          <el-tag v-if="preferences.length" type="info">{{ preferences.length }} 项</el-tag>
        </div>
        <div
          class="drop-zone"
          :class="{ 'drop-active': isDragOver }"
          @dragover.prevent="isDragOver = true"
          @dragleave="isDragOver = false"
          @drop="onDrop"
        >
          <EmptyState
            v-if="!preferences.length"
            icon="💜"
            title="拖拽或点击标签到这里"
            hint="支持拖拽排序调整权重"
          />
          <div v-else class="space-y-2">
            <div
              v-for="(pref, index) in preferences"
              :key="pref.uid"
              class="pref-item"
              draggable="true"
              @dragstart="onReorderStart($event, index)"
              @dragover.prevent
              @drop="onReorderDrop($event, index)"
            >
              <span class="drag-handle">⋮⋮</span>
              <el-tag :color="pref.color" effect="dark" closable @close="removePref(index)">
                {{ pref.label }}
              </el-tag>
              <span class="text-xs text-gray-400 ml-auto">权重 #{{ index + 1 }}</span>
            </div>
          </div>
        </div>
        <div class="mt-4 flex gap-2">
          <el-button type="primary" :loading="loading" @click="doRecommend">
            生成歌单推荐
          </el-button>
          <el-button @click="clearPrefs">清空</el-button>
        </div>
      </div>
    </div>

    <div v-if="loading" class="card"><el-skeleton :rows="4" animated /></div>

    <div v-else-if="recommendations.length" class="space-y-4">
      <h3 class="text-lg font-bold">为你推荐的歌单</h3>
      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        <div
          v-for="rec in recommendations"
          :key="rec.id"
          class="card rec-card"
          :style="{ borderTop: `3px solid ${rec.cover_color || '#1e6fff'}` }"
        >
          <div class="flex justify-between items-start mb-2">
            <h4 class="font-bold">{{ rec.name }}</h4>
            <el-tag type="success" size="small">匹配 {{ rec.score }}</el-tag>
          </div>
          <p class="text-xs text-gray-500 mb-3">{{ rec.match_reason }}</p>
          <el-tag size="small">{{ getSiteLabel(rec.source) }}</el-tag>
          <div v-if="rec.preview_tracks?.length" class="mt-3 space-y-1">
            <p class="text-xs font-semibold text-gray-500">预览曲目</p>
            <div v-for="t in rec.preview_tracks" :key="t.track_id" class="text-sm flex items-center gap-2">
              <el-avatar v-if="t.cover_url" :src="t.cover_url" :size="28" shape="square" />
              <span class="truncate">{{ t.title }} — {{ (t.artists || []).join('/') }}</span>
            </div>
          </div>
          <p v-if="rec.total_tracks" class="text-xs text-gray-400 mt-2">共 {{ rec.total_tracks }} 首</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { getRecommendTags, recommendPlaylists, getTracks } from '../api'
import { DEFAULT_SOURCE, getSiteLabel, MOOD_PRESETS } from '../constants/sites'
import SourceSelect from '../components/SourceSelect.vue'
import EmptyState from '../components/EmptyState.vue'

const availableTags = ref([])
const preferences = ref([])
const recommendations = ref([])
const search = ref('')
const searchSource = ref('')
const searchResults = ref([])
const preferSource = ref('')
const loading = ref(false)
const isDragOver = ref(false)
let dragPayload = null
let reorderFrom = null
let uidCounter = 0

function isTagSelected(id) {
  return preferences.value.some(p => p.kind === 'tag' && p.id === id)
}

function addTag(tag) {
  if (isTagSelected(tag.id)) {
    ElMessage.info('已在喜好中')
    return
  }
  preferences.value.push({
    uid: ++uidCounter, kind: 'tag', id: tag.id, label: tag.id,
    tagType: tag.type, color: tag.color,
  })
}

function addTrack(t) {
  preferences.value.push({
    uid: ++uidCounter, kind: 'track', id: t.track_id,
    label: `${t.title} - ${(t.artists || [])[0] || ''}`,
    track: t, color: '#1e6fff',
  })
  ElMessage.success('已添加歌曲')
}

function applyPreset(preset) {
  clearPrefs(false)
  for (const g of preset.genres) {
    const tag = availableTags.value.find(t => t.id === g)
    if (tag) addTag(tag)
  }
  for (const s of preset.scenes) {
    const tag = availableTags.value.find(t => t.id === s)
    if (tag && !isTagSelected(s)) addTag(tag)
  }
  ElMessage.success(`已应用「${preset.name}」预设`)
}

function onDragStart(e, tag) { dragPayload = { type: 'tag', tag }; e.dataTransfer.effectAllowed = 'copy' }
function onDragTrack(e, track) { dragPayload = { type: 'track', track }; e.dataTransfer.effectAllowed = 'copy' }

function onDrop(e) {
  e.preventDefault()
  isDragOver.value = false
  if (!dragPayload) return
  if (dragPayload.type === 'tag') addTag(dragPayload.tag)
  else if (dragPayload.type === 'track') addTrack(dragPayload.track)
  dragPayload = null
}

function onReorderStart(e, index) { reorderFrom = index; e.dataTransfer.effectAllowed = 'move' }
function onReorderDrop(e, toIndex) {
  e.preventDefault()
  if (reorderFrom === null || reorderFrom === toIndex) return
  const item = preferences.value.splice(reorderFrom, 1)[0]
  preferences.value.splice(toIndex, 0, item)
  reorderFrom = null
}

function removePref(index) { preferences.value.splice(index, 1) }
function clearPrefs(clearRec = true) {
  preferences.value = []
  if (clearRec) recommendations.value = []
}

function buildRequest() {
  const genres = [], scenes = [], tags = [], tracks = []
  preferences.value.forEach((p, i) => {
    const weight = preferences.value.length - i
    if (p.kind === 'tag') {
      if (p.tagType === 'genre') genres.push(p.id)
      else scenes.push(p.id)
      if (weight > 2) tags.push(p.id)
    } else if (p.kind === 'track' && p.track) {
      tracks.push({ title: p.track.title, artists: p.track.artists || [], tags: p.track.tags || [] })
    }
  })
  const req = { genres, scenes, tags, tracks, limit: 6, with_preview: true }
  if (preferSource.value) req.sources = [preferSource.value]
  return req
}

async function doRecommend() {
  if (!preferences.value.length) {
    ElMessage.warning('请先添加音乐喜好')
    return
  }
  loading.value = true
  recommendations.value = []
  try {
    const res = await recommendPlaylists(buildRequest())
    recommendations.value = res.data.recommendations
    ElMessage.success(`为你找到 ${res.data.count} 个歌单`)
  } catch (e) {
    ElMessage.error('推荐失败')
  } finally {
    loading.value = false
  }
}

async function searchTracks() {
  if (!search.value) return
  const params = { search: search.value, limit: 10 }
  if (searchSource.value) params.source = searchSource.value
  const res = await getTracks(params)
  searchResults.value = res.data.tracks
}

onMounted(async () => {
  const res = await getRecommendTags()
  availableTags.value = res.data.tags

  const pending = sessionStorage.getItem('a4m-pending-track')
  if (pending) {
    try {
      addTrack(JSON.parse(pending))
      sessionStorage.removeItem('a4m-pending-track')
    } catch (_) {}
  }
})
</script>

<style scoped>
.pref-chip {
  padding: 6px 12px;
  border: 2px solid;
  border-radius: 20px;
  cursor: pointer;
  font-size: 14px;
  background: var(--bg-card);
  user-select: none;
  transition: transform 0.15s;
}
.pref-chip:hover { transform: scale(1.05); }
.pref-chip-active { background: rgba(30, 111, 255, 0.08); }
.drop-zone {
  min-height: 200px;
  border: 2px dashed #cbd5e1;
  border-radius: 12px;
  padding: 16px;
  transition: all 0.2s;
}
.drop-active { border-color: #1e6fff; background: rgba(30, 111, 255, 0.05); }
.pref-item {
  display: flex; align-items: center; gap: 8px;
  padding: 8px; background: rgba(0,0,0,0.03);
  border-radius: 8px; cursor: grab;
}
.drag-handle { color: #94a3b8; }
.pref-track-item {
  padding: 8px 12px; border-radius: 8px;
  background: rgba(0,0,0,0.04); cursor: pointer;
  transition: background 0.15s;
}
.pref-track-item:hover { background: rgba(30, 111, 255, 0.08); }
.rec-card { transition: transform 0.2s; }
.rec-card:hover { transform: translateY(-2px); }
</style>
