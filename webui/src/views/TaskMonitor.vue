<template>
  <div class="space-y-6">
    <div class="card flex justify-between items-center">
      <div>
        <h2 class="text-xl font-bold">任务监控 — {{ taskId }}</h2>
        <el-tag v-if="task" :type="statusType(task.status)" class="mt-2">{{ task?.status }}</el-tag>
      </div>
      <div class="space-x-2">
        <el-button v-if="task?.status === 'running'" @click="doPause">暂停</el-button>
        <el-button v-if="task?.status === 'paused'" type="success" @click="doResume">恢复</el-button>
        <el-button type="danger" @click="doCancel">取消</el-button>
      </div>
    </div>

    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <div class="card">
        <h3 class="font-semibold mb-4">实时日志</h3>
        <div ref="logContainer" class="h-80 overflow-y-auto bg-slate-900 text-green-400 p-3 rounded font-mono text-sm">
          <div v-for="(log, i) in logs" :key="i" :class="logClass(log)">
            [{{ formatTime(log.timestamp) }}] {{ log.event_type }}: {{ log.message }}
          </div>
        </div>
      </div>
      <div class="card">
        <h3 class="font-semibold mb-4">Agent 链路图</h3>
        <div ref="mermaidRef" class="overflow-auto"></div>
      </div>
    </div>

    <div class="card" v-if="task?.error">
      <el-alert type="error" :title="task.error" show-icon />
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, nextTick } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import mermaid from 'mermaid'
import { getTask, pauseTask, resumeTask, cancelTask, connectLogs } from '../api'

const route = useRoute()
const taskId = route.params.id
const task = ref(null)
const logs = ref([])
const logContainer = ref(null)
const mermaidRef = ref(null)
let ws = null
let pollTimer = null

function statusType(s) {
  return { completed: 'success', running: 'warning', failed: 'danger' }[s] || 'info'
}

function logClass(log) {
  if (log.event_type?.includes('error') || log.event_type?.includes('failed')) return 'text-red-400'
  if (log.event_type?.includes('complete')) return 'text-yellow-300'
  return ''
}

function formatTime(ts) {
  if (!ts) return ''
  return new Date(ts).toLocaleTimeString()
}

async function renderMermaid() {
  const events = logs.value.slice(-8)
  let diagram = 'flowchart LR\n    Start[任务开始]'
  let prev = 'Start'
  events.forEach((ev, i) => {
    const node = `N${i}`
    diagram += `\n    ${prev} --> ${node}[${ev.event_type}]`
    prev = node
  })
  diagram += `\n    ${prev} --> End[完成]`

  await nextTick()
  if (mermaidRef.value) {
    mermaidRef.value.innerHTML = ''
    const { svg } = await mermaid.render('flow' + Date.now(), diagram)
    mermaidRef.value.innerHTML = svg
  }
}

async function loadTask() {
  const res = await getTask(taskId)
  task.value = res.data
}

async function doPause() {
  await pauseTask(taskId)
  ElMessage.info('已暂停')
  loadTask()
}

async function doResume() {
  await resumeTask(taskId)
  ElMessage.success('已恢复')
  loadTask()
}

async function doCancel() {
  await cancelTask(taskId)
  ElMessage.warning('已取消')
  loadTask()
}

onMounted(async () => {
  mermaid.initialize({ startOnLoad: false, theme: 'dark' })
  await loadTask()

  ws = connectLogs(taskId, (data) => {
    logs.value.push(data)
    if (logContainer.value) logContainer.value.scrollTop = logContainer.value.scrollHeight
    renderMermaid()
    if (data.event_type === 'task_complete' || data.event_type === 'task_failed') {
      loadTask()
    }
  })

  pollTimer = setInterval(loadTask, 5000)
})

onUnmounted(() => {
  ws?.close()
  clearInterval(pollTimer)
})
</script>
