<script setup lang="ts">
import { defineOptions, ref } from 'vue';

// 定义组件名称
defineOptions({
  name: 'StepsList'
});

// 定义响应式变量
const currentStatus = ref<'error' | 'process' | 'wait' | 'finish'>('process');

defineProps<{ current: number }>();
</script>

<template>
  <NSpace vertical>
    <!-- 步骤条 -->
    <NSteps :current="current" :status="currentStatus" class="custom-steps card-wrapper">
      <NStep title="上传文件" />
      <NStep title="预览文件" />
      <NStep title="确认Prompt" />
      <NStep title="生成" />
    </NSteps>
  </NSpace>
</template>

<style scoped>
/* 设置步骤条的背景色为白色 */
.custom-steps {
  background-color: white;
  padding: 20px; /* 添加一些内边距，避免内容靠得太紧 */
  border-radius: 8px; /* 可选：设置圆角 */
  align-items: center;
}
</style>
