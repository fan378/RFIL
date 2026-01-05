<script setup lang="ts">
import { NInput } from 'naive-ui';
import { onMounted, onUpdated } from 'vue';

const props = defineProps<{
  data: Record<string, any>;
  columns: Array<{
    label: string;
    key: string;
    width?: string;
    colspan?: number;
  }>;
  isEditing?: boolean;
  prefix?: string;
}>();

// 添加计算属性来判断是否应该显示为 highlightnull
const shouldHighlightNull = (key: string) => {
  const elementId = `${props.prefix || ''}-${key}`;
  const element = document.getElementById(elementId);
  if (!element) return false;

  // 检查元素是否应该显示为 highlightnull
  const isNone = element.getAttribute('data-highlightnull') === 'active';
  if (!isNone) return false;

  // 根据ID前缀返回不同的样式类名
  return elementId.startsWith('病人-') ? 'highlightnull' : 'dhighlightnull';
};

// 定义父组件需要监听的事件
const emit = defineEmits(['highlight', 'removeHighlight', 'showSource']);

// 处理鼠标事件
const handleMouseOver = (index: string) => {
  emit('highlight', `${props.prefix || ''}-${index}`);
};

const handleMouseOut = (index: string) => {
  emit('removeHighlight', `${props.prefix || ''}-${index}`);
};

const handleClick = (index: string) => {
  emit('showSource', `${props.prefix || ''}-${index}`);
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
    <colgroup>
      <col style="width: 16%" />
      <col style="width: 18%" />
      <col style="width: 12%" />
      <col style="width: 18%" />
      <col style="width: 15%" />
      <col style="width: 20%" />
    </colgroup>
    <tbody>
      <tr v-for="(row, rowIndex) in columns" :key="rowIndex">
        <template v-for="col in row" :key="col.key">
          <td class="table-cell">{{ col.label }}</td>
          <td class="table-cell" :colspan="col.colspan">
            <NInput v-if="isEditing" v-model:value="data[col.key]" type="textarea" autosize />
            <span
              v-else
              :id="`${prefix || ''}-${col.key}`"
              :key="col.key"
              class="cell-wrapper"
              :class="['cell-wrapper', { [shouldHighlightNull(col.key)]: shouldHighlightNull(col.key) }]"
              @mouseover="handleMouseOver(`${col.key}`)"
              @mouseout="handleMouseOut(`${col.key}`)"
              @click="handleClick(`${col.key}`)"
            >
              {{ data[col.key] }}
            </span>
          </td>
        </template>
      </tr>
      <!-- 额外添加两块字段 -->
      <tr>
        <td class="table-cell" :colspan="6">体检摘要:</td>
      </tr>
      <tr>
        <td :colspan="6">
          <!-- 编辑模式 -->
          <div v-if="isEditing" class="medical-summary-edit">
            <div v-for="(group, gIndex) in data['体检摘要']" :key="`edit-group-${gIndex}`" class="edit-group">
              <NInput
                v-for="(item, index) in group"
                :key="`体检摘要-${gIndex}-${index}`"
                v-model:value="data['体检摘要'][gIndex][index]"
                type="textarea"
                autosize
                class="nested-input"
              />
            </div>
          </div>

          <!-- 展示模式 -->
          <div v-else class="medical-summary-display">
            <div v-for="(group, gIndex) in data['体检摘要']" :key="`display-group-${gIndex}`" class="display-group">
              <span
                v-for="(item, index) in group"
                :id="`${prefix || ''}-体检摘要-${gIndex}-${index}`"
                :key="`体检摘要-${gIndex}-${index}`"
                :class="{ [shouldHighlightNull(`体检摘要-${gIndex}-${index}`)]: shouldHighlightNull(`体检摘要-${gIndex}-${index}`) }"
                class="summary-item"
                @mouseover="handleMouseOver(`体检摘要-${gIndex}-${index}`)"
                @mouseout="handleMouseOut(`体检摘要-${gIndex}-${index}`)"
                @click="handleClick(`体检摘要-${gIndex}-${index}`)"
              >
                {{ item }}
                <span v-if="index !== group.length - 1" class="separator">/</span>
              </span>
            </div>
          </div>
        </td>
      </tr>
    </tbody>
  </table>
</template>

<style scoped>
.dynamic-table tr:nth-child(odd) {
  background-color: rgba(238, 239, 241, 0.5);
}
.dynamic-table td:nth-child(even) {
  font-family: 'SimSun', serif; /* 宋体 */
}
.dynamic-table td:nth-child(odd) {
  font-family: 'Times New Roman', 'SimSun', '黑体', sans-serif;
  font-weight: 700;
}
.highlight {
  background-color: #e8efff;
  /* transition:
    background-color 0.3s ease,
    box-shadow 0.2s ease-in-out,
    transform 0.2s ease-in-out; */
  transition: 0.3s cubic-bezier(0.4, 0, 0.2, 1);

  padding: 3px 6px;
  /* display: inline-block; */

  /* 主题变量（如果已定义 CSS 变量） */
  border-radius: 6px;
  color: var(--blue-15);
  /* color: white; */
  /* background: var(--blue-15); */
}
.medical-summary-edit {
  padding: 8px;
}

.edit-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-bottom: 12px;
}

.nested-input {
  margin-bottom: 6px;
}

.medical-summary-display {
  padding: 8px;
}

.display-group {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 8px;
}

.summary-item {
  padding: 4px 8px;
  background: rgba(238, 239, 241, 0.3);
  border-radius: 4px;
  cursor: pointer;
  transition: background-color 0.3s;

  &:hover {
    background-color: #f0f5ff;
  }
}

.separator {
  color: #999;
  margin-left: 4px;
}
.highlightnull {
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
