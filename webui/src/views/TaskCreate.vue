<template>
  <div class="max-w-3xl mx-auto">
    <div class="card">
      <el-form :model="form" label-width="110px" @submit.prevent="submit">
        <el-form-item label="任务名称" required>
          <el-input v-model="form.name" placeholder="留空将自动生成" clearable />
          <div class="form-tip">将根据站点和采集类型自动填充名称</div>
        </el-form-item>

        <el-form-item label="音乐站点" required>
          <SourceSelect v-model="primarySource" width="200px" @change="onSourceChange" />
          <el-checkbox v-model="dualSite" class="ml-4">同时采集双站（QQ + 网易云）</el-checkbox>
          <div class="form-tip">默认 QQ 音乐，勾选后可并行采集两个站点</div>
        </el-form-item>

        <el-form-item label="采集类型">
          <el-select v-model="form.task_type" style="width: 220px" @change="syncTaskName">
            <el-option label="热歌榜" value="hot_chart" />
            <el-option label="最新榜单（可选类型）" value="chart" />
            <el-option label="歌单详情" value="playlist" />
            <el-option label="歌手信息" value="artist" />
          </el-select>
        </el-form-item>

        <el-form-item v-if="isChartTask" label="榜单类型">
          <el-select v-model="form.config.chart_type" style="width: 180px" @change="syncTaskName">
            <el-option v-for="(label, key) in availableChartTypes" :key="key" :label="label" :value="key" />
          </el-select>
        </el-form-item>

        <el-form-item v-if="form.task_type === 'playlist'" label="歌单 ID">
          <el-input v-model="form.config.playlist_id" placeholder="公开歌单 ID" />
        </el-form-item>

        <el-form-item v-if="form.task_type === 'artist'" label="歌手 ID">
          <el-input v-model="form.config.artist_id" placeholder="歌手 mid / id" />
        </el-form-item>

        <el-form-item v-if="isChartTask" label="采集数量">
          <el-slider v-model="form.config.limit" :min="10" :max="100" :step="10" show-input style="max-width: 360px" />
        </el-form-item>

        <el-form-item label="优先级">
          <el-rate v-model="priorityStars" :max="5" show-text :texts="['低', '较低', '中', '较高', '高']" />
        </el-form-item>

        <el-alert v-if="recommend.length" type="info" :closable="false" class="mb-4" show-icon>
          <template #title>智能建议</template>
          {{ getSiteLabel(primarySource) }} 推荐采集：{{ recommend.join('、') }}
        </el-alert>

        <el-form-item>
          <el-button type="primary" :loading="loading" @click="submit">启动任务</el-button>
          <el-button @click="resetForm">重置</el-button>
        </el-form-item>
      </el-form>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { createTask, getRecommend } from '../api'
import { DEFAULT_SOURCE, getSiteLabel, CHART_TYPE_LABELS } from '../constants/sites'
import SourceSelect from '../components/SourceSelect.vue'

const router = useRouter()
const loading = ref(false)
const recommend = ref([])
const primarySource = ref(DEFAULT_SOURCE)
const dualSite = ref(false)
const priorityStars = ref(3)

const form = ref({
  name: '',
  task_type: 'hot_chart',
  config: { limit: 50, playlist_id: '', artist_id: '', chart_type: 'hot' },
})

const isChartTask = computed(() => ['hot_chart', 'chart'].includes(form.value.task_type))

const availableChartTypes = computed(() => {
  const base = { hot: '热歌榜', new: '新歌榜', surge: '飙升榜', original: '原创榜' }
  if (primarySource.value === 'qq') base.pop = '流行指数'
  if (primarySource.value === 'netease') base.electronic = '电音榜'
  return base
})

const sources = computed(() =>
  dualSite.value ? ['qq', 'netease'] : [primarySource.value]
)

watch([primarySource, () => form.value.task_type, () => form.value.config.chart_type], async () => {
  const res = await getRecommend(primarySource.value)
  recommend.value = res.data.recommended
  syncTaskName()
}, { immediate: true })

watch(priorityStars, (v) => { form.value.priority = v * 2 })

function onSourceChange() {
  if (!availableChartTypes.value[form.value.config.chart_type]) {
    form.value.config.chart_type = 'hot'
  }
}

function syncTaskName() {
  if (form.value.name) return
  const site = dualSite.value ? '双站' : getSiteLabel(primarySource.value)
  const typeMap = { hot_chart: '热歌榜', chart: CHART_TYPE_LABELS[form.value.config.chart_type] || '榜单', playlist: '歌单', artist: '歌手' }
  form.value.name = `${site}${typeMap[form.value.task_type] || '采集'}`
}

function resetForm() {
  form.value = { name: '', task_type: 'hot_chart', config: { limit: 50, playlist_id: '', artist_id: '', chart_type: 'hot' }, priority: 6 }
  primarySource.value = DEFAULT_SOURCE
  dualSite.value = false
  priorityStars.value = 3
  syncTaskName()
}

async function submit() {
  syncTaskName()
  if (!sources.value.length) {
    ElMessage.warning('请选择音乐站点')
    return
  }
  loading.value = true
  try {
    const payload = {
      ...form.value,
      sources: sources.value,
      priority: priorityStars.value * 2,
    }
    const res = await createTask(payload)
    ElMessage.success('任务已创建')
    router.push(`/tasks/${res.data.task_id}`)
  } catch (e) {
    ElMessage.error('创建失败: ' + (e.response?.data?.detail || e.message))
  } finally {
    loading.value = false
  }
}

syncTaskName()
</script>
