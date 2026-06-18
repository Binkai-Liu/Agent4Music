import { createRouter, createWebHistory } from 'vue-router'
import Dashboard from './views/Dashboard.vue'
import TaskCreate from './views/TaskCreate.vue'
import TaskMonitor from './views/TaskMonitor.vue'
import DataBrowse from './views/DataBrowse.vue'
import DataExport from './views/DataExport.vue'
import Charts from './views/Charts.vue'
import Recommend from './views/Recommend.vue'

const routes = [
  { path: '/', name: 'Dashboard', component: Dashboard },
  { path: '/charts', name: 'Charts', component: Charts },
  { path: '/recommend', name: 'Recommend', component: Recommend },
  { path: '/tasks/new', name: 'TaskCreate', component: TaskCreate },
  { path: '/tasks/:id', name: 'TaskMonitor', component: TaskMonitor },
  { path: '/data', name: 'DataBrowse', component: DataBrowse },
  { path: '/export', name: 'DataExport', component: DataExport },
]

export default createRouter({
  history: createWebHistory(),
  routes,
})
