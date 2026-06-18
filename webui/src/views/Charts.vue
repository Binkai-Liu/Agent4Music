<template>
  <div class="space-y-6">
    <div class="card">
      <el-form inline class="flex flex-wrap gap-y-3 items-end">
        <el-form-item label="音乐站点" class="mb-0">
          <SourceSelect v-model="source" width="180px" @change="onSourceChange" />
        </el-form-item>
        <el-form-item label="榜单类型" class="mb-0">
          <el-radio-group v-model="chartType" class="chart-tabs" @change="fetchChart">
            <el-radio-button v-for="c in catalog" :key="c.id" :label="c.id">
              {{ c.name }}
            </el-radio-button>
          </el-radio-group>
        </el-form-item>
        <el-form-item class="mb-0">
          <el-button type="primary" :loading="loading" @click="fetchChart">
            <el-icon class="mr-1"><Refresh /></el-icon>刷新当前榜
          </el-button>
          <el-button :loading="loadingAll" @click="fetchAllCharts">全部榜单</el-button>
        </el-form-item>
      </el-form>
      <p class="form-tip mt-2">默认展示 QQ 音乐热歌榜，切换站点/榜单后自动刷新</p>
    </div>

    <div v-if="loading && !tracks.length" class="card">
      <el-skeleton :rows="8" animated />
    </div>

    <div v-else-if="chartMeta" class="card">
      <div class="flex justify-between items-center mb-4">
        <div>
          <div class="flex items-center gap-2">
            <el-tag>{{ getSiteLabel(source) }}</el-tag>
            <h2 class="text-xl font-bold">{{ chartMeta.name }}</h2>
          </div>
          <p class="text-sm text-gray-500 mt-1">
            {{ chartMeta.track_count }} 首 · 更新于 {{ formatTime(chartMeta.fetched_at) }}
          </p>
        </div>
        <div class="flex gap-2">
          <el-button size="small" @click="saveChart" :disabled="!tracks.length" :loading="saving">
            入库保存
          </el-button>
          <el-button size="small" type="primary" plain @click="$router.push('/recommend')">
            据此推荐歌单
          </el-button>
        </div>
      </div>
      <el-table :data="tracks" stripe max-height="520" highlight-current-row>
        <el-table-column prop="chart_rank" label="#" width="60" />
        <el-table-column label="封面" width="70">
          <template #default="{ row }">
            <el-avatar v-if="row.cover_url" :src="row.cover_url" shape="square" :size="44" />
            <el-avatar v-else shape="square" :size="44">🎵</el-avatar>
          </template>
        </el-table-column>
        <el-table-column prop="title" label="歌曲" min-width="180" show-overflow-tooltip />
        <el-table-column label="歌手" min-width="140" show-overflow-tooltip>
          <template #default="{ row }">{{ (row.artists || []).join(' / ') }}</template>
        </el-table-column>
        <el-table-column prop="album" label="专辑" min-width="140" show-overflow-tooltip />
        <el-table-column label="时长" width="80">
          <template #default="{ row }">{{ formatDuration(row.duration_ms) }}</template>
        </el-table-column>
      </el-table>
    </div>

    <EmptyState v-else icon="📊" title="选择站点和榜单后自动加载" hint="默认 QQ 音乐 · 热歌榜">
      <el-button type="primary" @click="fetchChart">立即加载</el-button>
    </EmptyState>

    <div v-if="allCharts.length" class="space-y-4">
      <h3 class="text-lg font-semibold">全部榜单概览</h3>
      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        <div
          v-for="c in allCharts"
          :key="c.chart_type"
          class="card quick-card"
          @click="selectChart(c)"
        >
          <div class="flex justify-between items-start">
            <div>
              <h4 class="font-bold">{{ c.chart_name }}</h4>
              <p class="text-xs text-gray-500 mt-1">{{ c.description }}</p>
            </div>
            <el-tag size="small" type="info">{{ c.track_count || 0 }} 首</el-tag>
          </div>
          <div v-if="c.tracks?.length" class="mt-3 text-sm text-gray-500 truncate">
            🥇 {{ c.tracks[0]?.title }}
            <span v-if="c.tracks[1]"> · {{ c.tracks[1]?.title }}</span>
          </div>
          <el-alert v-if="c.error" type="error" :title="c.error" class="mt-2" />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { getChartsCatalog, getLatestChart, getAllLatestCharts } from '../api'
import { DEFAULT_SOURCE, getSiteLabel } from '../constants/sites'
import SourceSelect from '../components/SourceSelect.vue'
import EmptyState from '../components/EmptyState.vue'

const source = ref(DEFAULT_SOURCE)
const chartType = ref('hot')
const catalog = ref([])
const tracks = ref([])
const chartMeta = ref(null)
const allCharts = ref([])
const loading = ref(false)
const loadingAll = ref(false)
const saving = ref(false)

async function loadCatalog() {
  const res = await getChartsCatalog(source.value)
  catalog.value = res.data.charts
  if (catalog.value.length && !catalog.value.find(c => c.id === chartType.value)) {
    chartType.value = catalog.value[0].id
  }
}

async function onSourceChange() {
  await loadCatalog()
  await fetchChart()
}

async function fetchChart() {
  loading.value = true
  try {
    const res = await getLatestChart({
      source: source.value,
      chart_type: chartType.value,
      limit: 50,
    })
    tracks.value = res.data.tracks
    chartMeta.value = res.data
  } catch (e) {
    ElMessage.error('获取失败: ' + (e.response?.data?.detail || e.message))
  } finally {
    loading.value = false
  }
}

async function fetchAllCharts() {
  loadingAll.value = true
  try {
    const res = await getAllLatestCharts(source.value, 10)
    allCharts.value = res.data.charts
    ElMessage.success('全部榜单已刷新')
  } catch (e) {
    ElMessage.error('刷新失败')
  } finally {
    loadingAll.value = false
  }
}

async function saveChart() {
  saving.value = true
  try {
    const res = await getLatestChart({
      source: source.value,
      chart_type: chartType.value,
      limit: 50,
      save: true,
    })
    ElMessage.success(`已入库 · 任务 ${res.data.saved_task_id}`)
  } finally {
    saving.value = false
  }
}

function selectChart(c) {
  chartType.value = c.chart_type
  tracks.value = c.tracks || []
  chartMeta.value = {
    name: c.chart_name,
    track_count: c.track_count,
    fetched_at: c.fetched_at,
  }
}

function formatTime(ts) {
  if (!ts) return '-'
  return new Date(ts).toLocaleString('zh-CN')
}

function formatDuration(ms) {
  if (!ms) return '-'
  const sec = Math.floor(ms / 1000)
  return `${Math.floor(sec / 60)}:${String(sec % 60).padStart(2, '0')}`
}

onMounted(async () => {
  await loadCatalog()
  await fetchChart()
})
</script>
