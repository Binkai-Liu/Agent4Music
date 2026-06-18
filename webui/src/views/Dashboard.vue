<template>
  <div class="space-y-6">
    <!-- 快捷入口 -->
    <div class="grid grid-cols-1 sm:grid-cols-3 gap-4">
      <div class="card quick-card" @click="$router.push('/charts')">
        <div class="text-2xl mb-2">📊</div>
        <div class="font-bold">查看最新榜单</div>
        <div class="text-sm text-gray-500 mt-1">默认 QQ 音乐热歌榜，一键刷新</div>
      </div>
      <div class="card quick-card" @click="$router.push('/recommend')">
        <div class="text-2xl mb-2">✨</div>
        <div class="font-bold">喜好推荐歌单</div>
        <div class="text-sm text-gray-500 mt-1">拖拽或点选标签，智能匹配</div>
      </div>
      <div class="card quick-card" @click="quickFetch">
        <div class="text-2xl mb-2">⚡</div>
        <div class="font-bold">一键采集 QQ 热榜</div>
        <div class="text-sm text-gray-500 mt-1">快速拉取 Top50 并入库</div>
      </div>
    </div>

    <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
      <div class="card" v-for="item in summaryCards" :key="item.label">
        <div class="text-sm text-gray-500">{{ item.label }}</div>
        <div class="text-3xl font-bold mt-2" :class="item.color">{{ item.value }}</div>
      </div>
    </div>

    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <div class="card">
        <h3 class="text-lg font-semibold mb-4">站点数据分布</h3>
        <v-chart v-if="hasBarData" :option="barOption" style="height: 300px" autoresize />
        <EmptyState v-else icon="📭" title="暂无采集数据" hint="点击上方「一键采集」或前往榜单页拉取" />
      </div>
      <div class="card">
        <h3 class="text-lg font-semibold mb-4">曲风占比</h3>
        <v-chart v-if="hasPieData" :option="pieOption" style="height: 300px" autoresize />
        <EmptyState v-else icon="🏷️" title="暂无标签统计" hint="采集数据后将自动展示曲风分布" />
      </div>
    </div>

    <div class="card">
      <div class="flex justify-between items-center mb-4">
        <h3 class="text-lg font-semibold">最近任务</h3>
        <el-button size="small" :loading="refreshing" @click="refresh">刷新</el-button>
      </div>
      <el-table v-if="tasks.length" :data="tasks" stripe>
        <el-table-column prop="id" label="ID" width="120" />
        <el-table-column prop="name" label="名称" />
        <el-table-column label="站点" width="120">
          <template #default="{ row }">{{ formatSource(row.source) }}</template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="statusType(row.status)">{{ statusLabel(row.status) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="120">
          <template #default="{ row }">
            <router-link :to="`/tasks/${row.id}`">
              <el-button size="small" type="primary" link>监控</el-button>
            </router-link>
          </template>
        </el-table-column>
      </el-table>
      <EmptyState v-else icon="📋" title="还没有任务" hint="创建第一个采集任务开始使用">
        <el-button type="primary" @click="$router.push('/tasks/new')">创建任务</el-button>
      </EmptyState>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { BarChart, PieChart } from 'echarts/charts'
import { TitleComponent, TooltipComponent, LegendComponent, GridComponent } from 'echarts/components'
import VChart from 'vue-echarts'
import { getStats, getTasks, createTask } from '../api'
import { getSiteLabel, DEFAULT_SOURCE } from '../constants/sites'
import EmptyState from '../components/EmptyState.vue'

use([CanvasRenderer, BarChart, PieChart, TitleComponent, TooltipComponent, LegendComponent, GridComponent])

const router = useRouter()
const stats = ref({})
const tasks = ref([])
const refreshing = ref(false)

const summaryCards = computed(() => [
  { label: '总歌曲数', value: stats.value.total_tracks || 0, color: 'text-blue-600' },
  { label: '总任务数', value: stats.value.total_tasks || 0, color: 'text-purple-600' },
  { label: '运行中', value: stats.value.running_tasks || 0, color: 'text-green-600' },
  { label: '站点数', value: Object.keys(stats.value.by_source || {}).length, color: 'text-orange-600' },
])

const hasBarData = computed(() => Object.keys(stats.value.by_source || {}).length > 0)
const hasPieData = computed(() => Object.keys(stats.value.by_tags || {}).length > 0)

const barOption = computed(() => {
  const bySource = stats.value.by_source || {}
  const labels = Object.keys(bySource).map(getSiteLabel)
  return {
    tooltip: {},
    xAxis: { type: 'category', data: labels },
    yAxis: { type: 'value' },
    series: [{ type: 'bar', data: Object.values(bySource), itemStyle: { color: '#1e6fff' }, barMaxWidth: 48 }],
  }
})

const pieOption = computed(() => {
  const byTags = stats.value.by_tags || {}
  return {
    tooltip: { trigger: 'item' },
    series: [{
      type: 'pie', radius: ['40%', '65%'],
      data: Object.entries(byTags).map(([name, value]) => ({ name, value })),
    }],
  }
})

const STATUS_MAP = { completed: '已完成', running: '运行中', failed: '失败', pending: '等待中', paused: '已暂停', cancelled: '已取消' }
function statusType(s) { return { completed: 'success', running: 'warning', failed: 'danger', pending: 'info' }[s] || 'info' }
function statusLabel(s) { return STATUS_MAP[s] || s }
function formatSource(s) { return (s || '').split(',').map(getSiteLabel).join(' + ') }

async function refresh() {
  refreshing.value = true
  try {
    const [statsRes, tasksRes] = await Promise.all([getStats(), getTasks({ limit: 10 })])
    stats.value = statsRes.data.stats
    tasks.value = tasksRes.data.tasks
  } finally { refreshing.value = false }
}

async function quickFetch() {
  try {
    const res = await createTask({
      name: 'QQ热歌榜快捷采集',
      sources: [DEFAULT_SOURCE],
      task_type: 'hot_chart',
      config: { chart_type: 'hot', limit: 50 },
      priority: 8,
    })
    ElMessage.success('任务已创建，正在采集…')
    router.push(`/tasks/${res.data.task_id}`)
  } catch (e) {
    ElMessage.error('创建失败')
  }
}

onMounted(refresh)
</script>
