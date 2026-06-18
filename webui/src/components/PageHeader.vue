<template>
  <div v-if="title" class="page-header mb-6">
    <div>
      <h1 class="page-title">{{ title }}</h1>
      <p v-if="desc" class="page-desc">{{ desc }}</p>
    </div>
    <slot name="actions" />
  </div>
</template>

<script setup>
defineProps({
  title: String,
  desc: String,
})
</script>

<style scoped>
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
  gap: 16px;
}
.page-title {
  font-size: 1.5rem;
  font-weight: 700;
  margin: 0;
}
.page-desc {
  margin: 4px 0 0;
  font-size: 0.875rem;
  color: #64748b;
}
.dark .page-desc { color: #94a3b8; }
</style>
