<script setup lang="ts">
import { defineOptions, ref } from 'vue';
import { JsonViewer } from 'vue3-json-viewer';
import 'vue3-json-viewer/dist/index.css';
import { useTaskStore } from '@/store/modules/task';
import ParamsSetting from './params-setting.vue';

defineOptions({
  name: 'PreviewFile'
});

const taskStore = useTaskStore();
const jsonData = taskStore.processedJson.data;
const childComponent = ref(null);
const getFormData = () => {
  const formData = childComponent.value.getFormData();
  return formData;
};
// 导出表单数据
defineExpose({
  getFormData
});
</script>

<template>
  <NSpace vertical>
    <NGrid :x-gap="24" :y-gap="16" responsive="screen" item-responsive>
      <NGi span="24 s:24 m:6">
        <ParamsSetting ref="childComponent" />
      </NGi>
      <NGi span="24 s:24 m:18">
        <JsonViewer :value="jsonData" :expand-depth="5" copyable sort class="card-wrapper"></JsonViewer>
      </NGi>
    </NGrid>
  </NSpace>
</template>

<style scoped>
:deep(.jv-container) {
  /* max-height: 500px; */
  height: 72vh;
  overflow-y: auto; /* 让内容超出时显示纵向滚动条 */
  background-color: white; /* 设置背景色为白色 */
  border: none; /* 去除边框 */
  border-radius: 8px; /* 设置边框圆角为 8px */
}
:deep(.jv-container .jv-key) {
  color: #1f61ff;
}
:deep(.jv-container .jv-item.jv-string) {
  color: #111111;
}

/* form-item高度 */
::v-deep(.n-form-item-feedback-wrapper) {
  --n-feedback-height: 0px;
}
::v-deep(.n-form-item.n-form-item--top-labelled) {
  grid-template-rows: unset;
}
</style>
