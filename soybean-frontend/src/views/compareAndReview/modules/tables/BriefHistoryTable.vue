<script setup lang="ts">
import { NInput } from 'naive-ui';
import { onMounted, onUpdated } from 'vue';

const props = defineProps<{
  data: {
    '体温(T)': string;
    '脉搏(P)': string;
    '呼吸(R)': string;
    '高压(BP高)': string;
    '低压(BP低)': string;
    入院时简要病史: string[][];
  };
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

const vitals = [
  { label: 'T:', key: '体温(T)', useful_name: '体温', unit: '℃' },
  { label: 'P:', key: '脉搏(P)', useful_name: '脉搏', unit: 'bpm' },
  { label: 'R:', key: '呼吸(R)', useful_name: '呼吸', unit: 'bpm' },
  { label: 'BP:', key: ['高压(BP高)', '低压(BP低)'], useful_name: ['高压', '低压'], unit: 'mmHg' }
];

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
      <col style="width: 7%" />
      <col style="width: 18%" />
      <col style="width: 7%" />
      <col style="width: 18%" />
      <col style="width: 7%" />
      <col style="width: 13%" />
      <col style="width: 7%" />
      <col style="width: 23%" />
    </colgroup>
    <tbody>
      <tr>
        <td colspan="8" class="table-cell">入院时简要病史:</td>
      </tr>
      <tr>
        <template v-for="(vital, index) in vitals" :key="index">
          <td class="table-cell">{{ vital.label }}</td>
          <td class="table-cell">
            <template v-if="isEditing">
              <template v-if="Array.isArray(vital.key)">
                <NInput
                  v-if="isEditing"
                  v-model:value="data[vital.key[0]]"
                  type="text"
                  size="small"
                  style="width: auto"
                  autosize
                />
                /
                <NInput
                  v-if="isEditing"
                  v-model:value="data[vital.key[1]]"
                  type="text"
                  size="small"
                  style="width: auto"
                  autosize
                />
              </template>
              <template v-else>
                <NInput v-if="isEditing" v-model:value="data[vital.key]" type="textarea" autosize style="width: auto" />
              </template>
            </template>
            <template v-else>
              <template v-if="Array.isArray(vital.key)">
                <span
                  :id="`${prefix || ''}-${vital.useful_name[0]}`"
                  :class="{ [shouldHighlightNull(vital.useful_name[0])]: shouldHighlightNull(vital.useful_name[0]) }"
                  style="font-weight: normal"
                  @mouseover="handleMouseOver(`${vital.useful_name[0]}`)"
                  @mouseout="handleMouseOut(`${vital.useful_name[0]}`)"
                  @click="handleClick(`${vital.useful_name[0]}`)"
                >
                  {{ data[vital.key[0]] }}
                </span>
                /
                <span
                  :id="`${prefix || ''}-${vital.useful_name[1]}`"
                  :class="{ [shouldHighlightNull(vital.useful_name[1])]: shouldHighlightNull(vital.useful_name[1]) }"
                  style="font-weight: normal"
                  @mouseover="handleMouseOver(`${vital.useful_name[1]}`)"
                  @mouseout="handleMouseOut(`${vital.useful_name[1]}`)"
                  @click="handleClick(`${vital.useful_name[1]}`)"
                >
                  {{ data[vital.key[1]] }}
                </span>
              </template>
              <template v-else>
                <span
                  :id="`${prefix || ''}-${vital.useful_name}`"
                  :class="['cell-wrapper', { [shouldHighlightNull(vital.useful_name)]: shouldHighlightNull(vital.useful_name) }]"
                  style="font-weight: normal"
                  @mouseover="handleMouseOver(`${vital.useful_name}`)"
                  @mouseout="handleMouseOut(`${vital.useful_name}`)"
                  @click="handleClick(`${vital.useful_name}`)"
                >
                  {{ data[vital.key] }}
                </span>
              </template>
            </template>
            {{ vital.unit }}
          </td>
        </template>
      </tr>
      <tr></tr>
      <tr>
        <td colspan="8" class="table-cell">
          <div class="medical-history">
            <template v-if="isEditing">
              <!-- 编辑模式：支持二维数组结构 -->
              <div v-for="(group, gIndex) in data['入院时简要病史']" :key="`group-${gIndex}`" class="history-group">
                <NInput
                  v-for="(item, index) in group"
                  :key="`入院时简要病史-${gIndex}-${index}`"
                  v-model:value="data['入院时简要病史'][gIndex][index]"
                  type="textarea"
                  autosize
                  class="nested-input"
                />
              </div>
            </template>
            <template v-else>
              <!-- 展示模式：平铺显示二维数组内容 -->
              <div v-for="(group, gIndex) in data['入院时简要病史']" :key="`group-${gIndex}`" class="history-group">
                <span
                  v-for="(item, index) in group"
                  :id="`${prefix || ''}-入院时简要病史-${gIndex}-${index}`"
                  :key="`入院时简要病史-${gIndex}-${index}`"
                  :class="{ [shouldHighlightNull(`入院时简要病史-${gIndex}-${index}`)]: shouldHighlightNull(`入院时简要病史-${gIndex}-${index}`) }"
                  class="history-item"
                  @mouseover="handleMouseOver(`入院时简要病史-${gIndex}-${index}`)"
                  @mouseout="handleMouseOut(`入院时简要病史-${gIndex}-${index}`)"
                  @click="handleClick(`入院时简要病史-${gIndex}-${index}`)"
                >
                  {{ item }}
                  <!-- 添加间隔符，最后一个元素不显示 -->
                  <span v-if="index !== group.length - 1" class="separator">/</span>
                </span>
              </div>
            </template>
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
  font-family: 'SimSun', serif;
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
.medical-history {
  padding: 8px;
}

.history-group {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 8px;
}

.history-item {
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

.nested-input {
  margin-bottom: 8px;
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
