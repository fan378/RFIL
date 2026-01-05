<script setup lang="ts">
import { defineOptions, ref } from 'vue';
import { $t } from '@/locales';
import { useTaskStore } from '@/store/modules/task';

defineOptions({
  name: 'MetricScore'
});

const taskStore = useTaskStore();
</script>

<template>
  <!--
 <NCard
    :segmented="{
      content: true,
      footer: 'soft'
    }"
    title="Metric Score"
    size="small"
    :bordered="false"
    class="card-wrapper"
    header-style="padding: 6px var(--n-padding-left) 6px var(--n-padding-left);"
  >
    <template #header>
      <strong>Metric Score</strong>
    </template>
-->
  <NCard size="small" :bordered="false" class="card-wrapper">
    <NSpace>
      <NGrid :x-gap="16" :y-gap="16" responsive="screen" item-responsive>
        <NGi span="24 s:24 m:6">Metric Score:</NGi>
        <NGi span="24 s:24 m:6">ACC:0.7</NGi>
        <NGi span="24 s:24 m:6">Rouge:0.7</NGi>
        <NGi span="24 s:24 m:6">FACTKB:0.7</NGi>
      </NGrid>
    </NSpace>
  </NCard>
</template>

<style scoped>
:deep(.n-form-item .n-form-item-feedback-wrapper) {
  min-height: 0px;
}
/* 调整 NFormItem 的行高 */
.form-item {
  line-height: 1; /* 设置较小的行高 */
  padding: 5px 0; /* 减少上下内边距 */
}
</style>
