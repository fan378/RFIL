<script setup lang="ts">
import { onMounted } from 'vue';
import { onUpdated } from 'vue';

const props = defineProps<{
  items: string[][];
  highlightedItems: string[];
  isEditing?: boolean;
  prefix?: string;
}>();

// 添加计算属性来判断是否应该显示为 highlightnull
const shouldHighlightNull = (section: string, gIndex: number, index: number) => {
  const elementId = `${props.prefix || ''}-${section}-${gIndex}-${index}`;
  console.log('elementId', elementId);
  const element = document.getElementById(elementId);
  console.log('element', element);
  if (!element) return false;

  // 检查元素是否应该显示为 highlightnull
  const isNone = element.getAttribute('data-highlightnull') === 'active';
  if (!isNone) return false;

  // 根据ID前缀返回不同的样式类名
  return elementId.startsWith('病人-') ? 'highlightnull' : 'dhighlightnull';
};

const emit = defineEmits(['highlight', 'removeHighlight', 'showSource', 'edit']);

const handleEvent = (type: string, section: string, gIndex: number, index: number) => {
  const id = `${props.prefix || ''}-${section}-${gIndex}-${index}`;
  if (type === 'enter') emit('highlight', id);
  if (type === 'leave') emit('removeHighlight', id);
  if (type === 'click') emit('showSource', id);
};
const handleEdit = (value: string, rowIndex: number, cellIndex: number) => {
  const newItems = props.items.map((row, rIdx) => {
    if (rIdx === rowIndex) {
      return row.map((cell, cIdx) => (cIdx === cellIndex ? value : cell));
    }
    return row;
  });
  emit('edit', newItems);
};

onMounted(() => {
  setTimeout(() => {
    document.querySelectorAll('.cell-wrapper').forEach(el => {
      //console.log('[调试] onMounted cell id:', el.id, 'classList:', Array.from(el.classList));
    });
  }, 0);
});

onUpdated(() => {
  setTimeout(() => {
    document.querySelectorAll('.cell-wrapper').forEach(el => {
      //console.log('[调试] onUpdated cell id:', el.id, 'classList:', Array.from(el.classList));
    });
  }, 0);
});
</script>

<template>
  <table class="dynamic-table">
    <tr>
      <td colspan="8" class="table-cell">住院期间医疗情况</td>
    </tr>
    <template v-for="(row, rowIndex) in items" :key="`row-${rowIndex}`">
      <tr>
        <td colspan="8" class="normal-text table-cell">
          <template v-if="isEditing">
            <div class="edit-row">
              <NInput
                v-for="(cell, cellIndex) in row"
                :key="`edit-${rowIndex}-${cellIndex}`"
                :value="cell"
                type="textarea"
                autosize
                @update:value="v => handleEdit(v, rowIndex, cellIndex)"
              />
            </div>
          </template>
          <template v-else>
            <span
              v-for="(cell, cellIndex) in row"
              :id="`${prefix || ''}-住院期间医疗情况-${rowIndex}-${cellIndex}`"
              :key="`display-${rowIndex}-${cellIndex}`"
              class="cell-wrapper"
              :class="['cell-wrapper', { [shouldHighlightNull('住院期间医疗情况', rowIndex, cellIndex)]: shouldHighlightNull('住院期间医疗情况', rowIndex, cellIndex) }]"
              @mouseover="handleEvent('enter', '住院期间医疗情况', rowIndex, cellIndex)"
              @mouseout="handleEvent('leave', '住院期间医疗情况', rowIndex, cellIndex)"
              @click="handleEvent('click', '住院期间医疗情况', rowIndex, cellIndex)"
            >
              {{ cell }}
            </span>
          </template>
        </td>
      </tr>
    </template>
  </table>
</template>

<style scoped>
/* 移除分隔符相关样式 */
.edit-row {
  display: flex;
  gap: 8px;
  flex-wrap: nowrap;
}

.cell-wrapper {
  display: inline-block;
  white-space: normal;
  max-width: 100%;
  word-wrap: break-word;
  vertical-align: top;
  padding: 2px 4px;
  margin: 2px;
  border: 1px solid transparent; /* 保持hover效果稳定性 */
  transition: all 0.3s ease;
}

.normal-text {
  word-break: break-all;
  padding: 8px;
}

/* 统一所有字体为宋体 */
.dynamic-table {
  font-family: 'SimSun', serif;
  width: 100%; /* 让表格撑满容器 */
  table-layout: fixed; /* 保持表格稳定性 */
}

.dynamic-table tr:nth-child(odd) {
  background-color: rgba(238, 239, 241, 0.5);
}

/* 移除原有字体设置 */
.dynamic-table td:nth-child(even),
.dynamic-table td:nth-child(odd) {
  font-family: 'SimSun', serif;
}

.highlight {
  background-color: #e8efff;
  border-radius: 6px;
  color: var(--blue-15);
  transition: 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}
:deep(.highlightnull) {
  background-color: #d2f410 !important;
  border-radius: 6px;
  color: #000;
  transition: 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}
:deep(.dhighlightnull) {
  background-color: #10f410 !important;
  border-radius: 6px;
  color: #000;
  transition: 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}
:deep(.highlightrellynull) {
  background: #f0511c !important;
  border-radius: 6px !important;
  color: #000 !important;
  transition: 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
}
</style>
