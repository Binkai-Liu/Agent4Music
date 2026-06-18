<template>
  <div class="empty-state">
    <div class="empty-icon">{{ icon }}</div>
    <p class="empty-title">{{ title }}</p>
    <p v-if="hint" class="empty-hint">{{ hint }}</p>
    <slot />
  </div>
</template>

<script setup>
defineProps({
  icon: { type: String, default: '🎧' },
  title: { type: String, default: '暂无数据' },
  hint: String,
})
</script>

<style scoped>
.empty-state {
  text-align: center;
  padding: 48px 24px;
  color: #64748b;
}
.empty-icon { font-size: 3rem; margin-bottom: 12px; }
.empty-title { font-size: 1.1rem; font-weight: 600; color: var(--text-primary); margin: 0 0 8px; }
.empty-hint { font-size: 0.875rem; margin: 0 0 16px; }
</style>
