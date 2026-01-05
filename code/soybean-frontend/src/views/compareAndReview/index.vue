<script setup lang="ts">
import { computed, ref } from 'vue';
import { useAppStore } from '@/store/modules/app';
import MenuBar from './modules/menu-bar.vue';
import CompareSummary from './modules/compare-summary.vue';
import SourceTracing from './modules/source-tracing.vue';
import MetricScore from './modules/metric-score.vue';

const appStore = useAppStore();
const gap = computed(() => (appStore.isMobile ? 0 : 16));

// 编辑功能
const isEditing = ref(false);
const toggleEdit = () => {
  isEditing.value = !isEditing.value;
};

// 来源展示
const receivedClickItem = ref('');
const handleClickItem = (value: string) => {
  receivedClickItem.value = value;
};

// 导出 patient 数据的方法
const exportFile = data => {
  if (!data) {
    alert('文件内容为空，无法导出！');
    return;
  }

  const blob = new Blob([data], { type: 'text/plain;charset=utf-8' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `export_${Date.now()}.json`; // 根据时间戳生成唯一文件名
  document.body.appendChild(a);
  a.click();

  document.body.removeChild(a);
  URL.revokeObjectURL(url);
};
const compareSummaryRef = ref(null); // 存储 cs.vue 的实例
const exportPatientData = () => {
  if (compareSummaryRef.value) {
    console.log('导出患者数据:', compareSummaryRef.value.patient);
    exportFile(JSON.stringify(compareSummaryRef.value.patient, null, 2)); // 将患者数据转换为 JSON 字符串并导出
    return compareSummaryRef.value.patient;
  }
  return null;
};
</script>

<template>
  <NSpace vertical :size="16">
    <NGrid :x-gap="gap" :y-gap="16" responsive="screen" item-responsive>
      <NGi span="24 s:24 m:24">
        <MenuBar :is-editing="isEditing" @toggle-edit="toggleEdit" @export-data="exportPatientData" />
      </NGi>
    </NGrid>
    <NGrid :x-gap="gap" :y-gap="16" responsive="screen" item-responsive>
      <NGi span="24 s:24 m:24">
        <CompareSummary ref="compareSummaryRef" :is-editing="isEditing" @update:click-item="handleClickItem" />
      </NGi>
    </NGrid>
    <NGrid :x-gap="gap" :y-gap="16" responsive="screen" item-responsive>
      <NGi span="24 s:24 m:24"><SourceTracing :received-click-item="receivedClickItem" /></NGi>
    </NGrid>
    <!--
 <NGrid :x-gap="gap" :y-gap="16" responsive="screen" item-responsive>
      <NGi span="24 s:24 m:24"><MetricScore /></NGi>
    </NGrid>
-->
  </NSpace>
</template>

<style scoped></style>
