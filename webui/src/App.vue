<template>
  <el-container class="min-h-screen app-shell">
    <el-aside width="220px" class="music-gradient text-white sidebar">
      <div class="p-4">
        <div class="text-xl font-bold">Agent4Music</div>
        <div class="text-xs opacity-75 mt-1">音乐数据智能体</div>
      </div>
      <el-menu
        :default-active="$route.path"
        router
        background-color="transparent"
        text-color="#fff"
        active-text-color="#ffd04b"
      >
        <el-menu-item v-for="item in navItems" :key="item.path" :index="item.path">
          <el-icon><component :is="item.icon" /></el-icon>
          <span>{{ item.label }}</span>
        </el-menu-item>
      </el-menu>
    </el-aside>
    <el-container>
      <el-header class="app-header">
        <div>
          <span class="text-lg font-medium">{{ pageMeta.title }}</span>
          <span class="text-sm text-gray-400 ml-3 hidden sm:inline">{{ pageMeta.desc }}</span>
        </div>
        <div class="flex items-center gap-3">
          <el-tooltip content="切换深/浅色主题">
            <el-switch v-model="isDark" active-text="暗色" inactive-text="亮色" @change="toggleDark" />
          </el-tooltip>
        </div>
      </el-header>
      <el-main class="app-main">
        <router-view v-slot="{ Component }">
          <transition name="fade" mode="out-in">
            <component :is="Component" />
          </transition>
        </router-view>
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { useRoute } from 'vue-router'
import { PAGE_META } from './constants/sites'

const route = useRoute()
const isDark = ref(localStorage.getItem('a4m-theme') === 'dark')

const navItems = [
  { path: '/', label: '仪表盘', icon: 'Odometer' },
  { path: '/charts', label: '最新榜单', icon: 'TrendCharts' },
  { path: '/recommend', label: '喜好推荐', icon: 'MagicStick' },
  { path: '/tasks/new', label: '创建任务', icon: 'Plus' },
  { path: '/data', label: '数据浏览', icon: 'Headset' },
  { path: '/export', label: '数据导出', icon: 'Download' },
]

const pageMeta = computed(() => {
  const base = PAGE_META[route.path]
  if (base) return base
  if (route.path.startsWith('/tasks/')) return { title: '任务监控', desc: '实时日志与执行链路' }
  return { title: 'Agent4Music', desc: '' }
})

function toggleDark(val) {
  document.documentElement.classList.toggle('dark', val)
  localStorage.setItem('a4m-theme', val ? 'dark' : 'light')
}

watch(isDark, (v) => toggleDark(v), { immediate: true })
</script>

<style scoped>
.app-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: var(--bg-card);
  box-shadow: 0 1px 3px rgba(0,0,0,0.06);
  height: 56px;
}
.app-main { padding: 24px; max-width: 1400px; margin: 0 auto; width: 100%; }
.sidebar { box-shadow: 2px 0 8px rgba(0,0,0,0.08); }
.fade-enter-active, .fade-leave-active { transition: opacity 0.15s ease; }
.fade-enter-from, .fade-leave-to { opacity: 0; }
</style>
