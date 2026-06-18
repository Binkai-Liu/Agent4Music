<template>
  <el-select
    :model-value="modelValue"
    :placeholder="placeholder"
    :clearable="clearable"
    :disabled="disabled"
    :style="{ width }"
    @update:model-value="emit('update:modelValue', $event)"
    @change="emit('change', $event)"
  >
    <el-option
      v-for="site in SITE_OPTIONS"
      :key="site.value"
      :label="site.label"
      :value="site.value"
    >
      <span>{{ site.icon }} {{ site.label }}</span>
    </el-option>
  </el-select>
</template>

<script setup>
import { SITE_OPTIONS } from '../constants/sites'

defineProps({
  modelValue: { type: String, default: 'qq' },
  placeholder: { type: String, default: '选择音乐站点' },
  clearable: { type: Boolean, default: false },
  disabled: { type: Boolean, default: false },
  width: { type: String, default: '180px' },
})

const emit = defineEmits(['update:modelValue', 'change'])
</script>
