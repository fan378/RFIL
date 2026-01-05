<script setup lang="ts">
import { computed, defineComponent, defineOptions, h, reactive, ref } from 'vue';
import { JsonViewer } from 'vue3-json-viewer';
import { $t } from '@/locales';
import { useTaskStore } from '@/store/modules/task';
import { useAppStore } from '@/store/modules/app';
import 'vue3-json-viewer/dist/index.css';
import TreeNode from './tree-node.vue';
import { NIcon } from 'naive-ui';

defineOptions({
  name: 'CompareSummary'
});

const appStore = useAppStore();
const gap = computed(() => (appStore.isMobile ? 0 : 16));
const taskStore = useTaskStore();
const jsonData = taskStore.processedJson.source;

// 将 JSON 数据转换为适合树形组件的结构
function formatJsonToTree(json: any, parentKey = ''): any[] {
  return Object.keys(json).map((key, index) => {
    const value = json[key];
    const nodeKey = `${parentKey}${index}`; // 生成唯一的 key

    if (typeof value === 'object') {
      return {
        label: key,
        key: nodeKey, // 必须添加 key
        children: formatJsonToTree(value, nodeKey)
      };
    }
    return {
      label: `${key}: ${value}`,
      key: nodeKey // 必须添加 key
    };
  });
}

const treeData = ref(formatJsonToTree(jsonData)); // 转换后的树形数据
// console.log(treeData.value);
const defaultExpandedKeys = ref([]); // 设置默认展开的节点
</script>

<template>
  <NGrid :x-gap="gap" :y-gap="16" responsive="screen" item-responsive>
    <NGi span="24 s:24 m:24">
      <NCard
        size="small"
        :bordered="false"
        title="LLM Discharge Summary --- Source Tracing"
        header-class="text-14px "
        header-style="padding: 6px var(--n-padding-left) 6px var(--n-padding-left);"
        class="container"
      >
        <NTree block-line :data="treeData" :default-expanded-keys="defaultExpandedKeys" selectable />
      </NCard>
    </NGi>
  </NGrid>
</template>

<style scoped>
.container {
  /* max-height: 500px; */
  height: 25vh;
  overflow-y: auto; /* 让内容超出时显示纵向滚动条 */
  background-color: white; /* 设置背景色为白色 */
  border: none; /* 去除边框 */
  border-radius: 8px; /* 设置边框圆角为 8px */
}

:deep(.n-tree-node-wrapper:nth-child(odd)) {
  background-color: #f4f4f4; /* 奇数节点背景色 */
}

:deep(.n-tree-node-wrapper:nth-child(even)) {
  background-color: #f4f4f450; /* 偶数节点背景色 */
}
</style>
