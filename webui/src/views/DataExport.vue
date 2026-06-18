<template>
  <div class="max-w-2xl mx-auto">
    <div class="card">
      <el-form label-width="100px">
        <el-form-item label="导出格式">
          <el-radio-group v-model="format">
            <el-radio-button label="csv">CSV</el-radio-button>
            <el-radio-button label="json">JSON</el-radio-button>
            <el-radio-button label="xlsx">Excel</el-radio-button>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="音乐站点">
          <SourceSelect v-model="source" width="200px" clearable placeholder="全部站点" />
          <div class="form-tip">默认 QQ 音乐，可清空导出全部站点</div>
        </el-form-item>
        <el-form-item label="任务 ID">
          <el-input v-model="taskId" placeholder="可选，留空导出该站点全部数据" clearable />
        </el-form-item>
        <el-alert type="info" :closable="false" show-icon class="mb-4">
          导出字段：track_id, title, artists, album, duration_ms, play_count, chart_rank, tags, source, fetched_at
        </el-alert>
        <el-form-item>
          <el-button type="primary" @click="doExport">
            <el-icon class="mr-1"><Download /></el-icon>
            下载导出
          </el-button>
        </el-form-item>
      </el-form>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import { exportData } from '../api'
import { DEFAULT_SOURCE } from '../constants/sites'
import SourceSelect from '../components/SourceSelect.vue'

const format = ref('csv')
const source = ref(DEFAULT_SOURCE)
const taskId = ref('')

function doExport() {
  const params = { format: format.value }
  if (source.value) params.source = source.value
  if (taskId.value) params.task_id = taskId.value
  window.open(exportData(params), '_blank')
  ElMessage.success('导出已开始下载')
}
</script>
