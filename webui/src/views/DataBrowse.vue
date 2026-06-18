<template>
  <div class="space-y-6">
    <div class="card">
      <div class="flex flex-wrap gap-3 mb-4 items-end">
        <el-form-item label="音乐站点" class="mb-0">
          <SourceSelect v-model="filters.source" width="160px" clearable placeholder="全部站点" @change="onFilterChange" />
        </el-form-item>
        <el-input
          v-model="filters.search"
          placeholder="搜索歌曲名 / 歌手"
          clearable
          style="width: 260px"
          @keyup.enter="load"
          @clear="load"
        >
          <template #prefix><el-icon><Search /></el-icon></template>
        </el-input>
        <el-button type="primary" @click="load">搜索</el-button>
        <el-button @click="resetFilters">重置</el-button>
      </div>

      <el-table :data="tracks" stripe v-loading="loading" empty-text="暂无数据，请先采集或切换筛选条件">
        <el-table-column prop="chart_rank" label="#" width="60" />
        <el-table-column label="封面" width="70">
          <template #default="{ row }">
            <el-avatar v-if="row.cover_url" :src="row.cover_url" shape="square" :size="48" />
          </template>
        </el-table-column>
        <el-table-column prop="title" label="歌曲" show-overflow-tooltip />
        <el-table-column label="歌手" show-overflow-tooltip>
          <template #default="{ row }">{{ (row.artists || []).join(', ') }}</template>
        </el-table-column>
        <el-table-column prop="album" label="专辑" show-overflow-tooltip />
        <el-table-column label="站点" width="110">
          <template #default="{ row }">
            <el-tag size="small" type="info">{{ getSiteLabel(row.source) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="140">
          <template #default="{ row }">
            <el-button size="small" link type="primary" @click="preview(row)">预览</el-button>
            <el-button size="small" link @click="goRecommend(row)">加入喜好</el-button>
          </template>
        </el-table-column>
      </el-table>

      <el-pagination
        class="mt-4 justify-center"
        v-model:current-page="page"
        :page-size="limit"
        :total="total"
        layout="total, prev, pager, next"
        @current-change="load"
      />
    </div>

    <el-dialog v-model="dialogVisible" title="歌曲详情" width="480px" destroy-on-close>
      <div v-if="current" class="text-center">
        <el-avatar v-if="current.cover_url" :src="current.cover_url" :size="120" shape="square" />
        <h3 class="text-xl font-bold mt-4">{{ current.title }}</h3>
        <p class="text-gray-500">{{ (current.artists || []).join(' / ') }}</p>
        <el-tag class="mt-2">{{ getSiteLabel(current.source) }}</el-tag>
        <p class="text-sm mt-3">专辑：{{ current.album || '未知' }}</p>
        <div v-if="current.lyric_raw" class="mt-4 text-left text-sm whitespace-pre-wrap max-h-60 overflow-y-auto bg-gray-50 dark:bg-slate-700 p-3 rounded">
          {{ current.lyric_raw }}
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { getTracks } from '../api'
import { DEFAULT_SOURCE, getSiteLabel } from '../constants/sites'
import SourceSelect from '../components/SourceSelect.vue'

const router = useRouter()
const tracks = ref([])
const total = ref(0)
const page = ref(1)
const limit = 20
const loading = ref(false)
const filters = ref({ source: DEFAULT_SOURCE, search: '' })
const dialogVisible = ref(false)
const current = ref(null)

async function load() {
  loading.value = true
  try {
    const res = await getTracks({
      source: filters.value.source || undefined,
      search: filters.value.search || undefined,
      limit,
      offset: (page.value - 1) * limit,
    })
    tracks.value = res.data.tracks
    total.value = res.data.total
  } finally {
    loading.value = false
  }
}

function onFilterChange() {
  page.value = 1
  load()
}

function resetFilters() {
  filters.value = { source: DEFAULT_SOURCE, search: '' }
  page.value = 1
  load()
}

function preview(row) {
  current.value = row
  dialogVisible.value = true
}

function goRecommend(row) {
  sessionStorage.setItem('a4m-pending-track', JSON.stringify(row))
  router.push('/recommend')
}

onMounted(load)
</script>
