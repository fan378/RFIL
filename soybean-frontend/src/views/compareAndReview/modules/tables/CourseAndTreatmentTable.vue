<script setup lang="ts">
import { NGi, NGrid, NInput } from 'naive-ui';
import { onMounted, onUpdated, watch, nextTick, ref } from 'vue';

const props = defineProps<{
  treatment: string[][];
  status: string[][];
  advice: string[][];
  isEditing?: boolean;
  prefix?: string;
}>();

// 添加一个响应式变量来存储高亮状态
const highlightStates = ref<Record<string, string>>({});

// 添加计算属性来判断是否应该显示为 highlightnull
const shouldHighlightNull = (section: string, gIndex: number, index: number) => {
  const elementId = `${props.prefix || ''}-${section}-${gIndex}-${index}`;
  return highlightStates.value[elementId] || '';
};

// 更新高亮状态的函数
const updateHighlightStates = async () => {
  await nextTick();
  const elements = document.querySelectorAll('.content-item');
  elements.forEach(el => {
    const elementId = el.id;
    const element = document.getElementById(elementId);
    if (element) {
      const isNone = element.getAttribute('data-highlightnull') === 'active';
      if (isNone) {
        highlightStates.value[elementId] = props.prefix === '病人' ? 'highlightnull' : 'dhighlightnull';
      } else {
        highlightStates.value[elementId] = '';
      }
    }
  });
};

// 监听 props.prefix 的变化
watch(() => props.prefix, () => {
  updateHighlightStates();
}, { immediate: true });

// 监听 DOM 更新
onUpdated(() => {
  updateHighlightStates();
});

const emit = defineEmits(['highlight', 'removeHighlight', 'showSource']);

const handleEvent = (type: string, section: string, gIndex: number, index: number) => {
  const id = `${props.prefix || ''}-${section}-${gIndex}-${index}`;
  if (type === 'enter') emit('highlight', id);
  if (type === 'leave') emit('removeHighlight', id);
  if (type === 'click') emit('showSource', id);
};

onMounted(() => {
  updateHighlightStates();
});
</script>

<template>
  <div class="dynamic-container">
    <!-- 病程与治疗情况 -->
    <div class="section-group">
      <div class="section-title">病程与治疗情况:</div>
      <NGrid v-if="isEditing" :cols="24" :x-gap="8">
        <NGi v-for="(group, gIndex) in treatment" :key="gIndex" :span="24">
          <NInput
            v-for="(item, index) in group"
            :key="index"
            v-model:value="treatment[gIndex][index]"
            type="textarea"
            autosize
          />
        </NGi>
      </NGrid>
      <NGrid v-else :cols="24" :x-gap="8">
        <NGi v-for="(group, gIndex) in treatment" :key="gIndex" :span="24" class="content-row">
          <span
            v-for="(item, index) in group"
            :id="`${prefix}-病程与治疗情况-${gIndex}-${index}`"
            :key="index"
            :class="['content-item', { [shouldHighlightNull('病程与治疗情况', gIndex, index)]: shouldHighlightNull('病程与治疗情况', gIndex, index) }]"
            @mouseenter="handleEvent('enter', '病程与治疗情况', gIndex, index)"
            @mouseleave="handleEvent('leave', '病程与治疗情况', gIndex, index)"
            @click="handleEvent('click', '病程与治疗情况', gIndex, index)"
          >
            {{ item }}
          </span>
        </NGi>
      </NGrid>
    </div>

    <!-- 出院时情况 -->
    <div class="section-group">
      <div class="section-title">出院时情况:</div>
      <NGrid v-if="isEditing" :cols="24" :x-gap="8">
        <NGi v-for="(group, gIndex) in status" :key="gIndex" :span="24">
          <NInput
            v-for="(item, index) in group"
            :key="index"
            v-model:value="status[gIndex][index]"
            type="textarea"
            autosize
          />
        </NGi>
      </NGrid>
      <NGrid v-else :cols="24" :x-gap="8">
        <NGi v-for="(group, gIndex) in status" :key="gIndex" :span="24" class="content-row">
          <span
            v-for="(item, index) in group"
            :id="`${prefix}-出院时情况-${gIndex}-${index}`"
            :key="index"
            :class="{ [shouldHighlightNull('出院时情况', gIndex, index)]: shouldHighlightNull('出院时情况', gIndex, index) }"
            class="content-item"
            @mouseenter="handleEvent('enter', '出院时情况', gIndex, index)"
            @mouseleave="handleEvent('leave', '出院时情况', gIndex, index)"
            @click="handleEvent('click', '出院时情况', gIndex, index)"
          >
            {{ item }}
          </span>
        </NGi>
      </NGrid>
    </div>

    <!-- 出院后用药建议 -->
    <div class="section-group">
      <div class="section-title">出院后用药建议:</div>
      <NGrid v-if="isEditing" :cols="24" :x-gap="8">
        <NGi v-for="(group, gIndex) in advice" :key="gIndex" :span="24">
          <NInput
            v-for="(item, index) in group"
            :key="index"
            v-model:value="advice[gIndex][index]"
            type="textarea"
            autosize
          />
        </NGi>
      </NGrid>
      <NGrid v-else :cols="24" :x-gap="8">
        <NGi v-for="(group, gIndex) in advice" :key="gIndex" :span="24" class="content-row">
          <span
            v-for="(item, index) in group"
            :id="`${prefix}-出院后用药建议-${gIndex}-${index}`"
            :key="index"
            :class="{ [shouldHighlightNull('出院后用药建议', gIndex, index)]: shouldHighlightNull('出院后用药建议', gIndex, index) }"
            class="content-item"
            @mouseenter="handleEvent('enter', '出院后用药建议', gIndex, index)"
            @mouseleave="handleEvent('leave', '出院后用药建议', gIndex, index)"
            @click="handleEvent('click', '出院后用药建议', gIndex, index)"
          >
            {{ item }}
          </span>
        </NGi>
      </NGrid>
    </div>
  </div>
</template>

<style scoped>
.dynamic-container {
  border: 2px solid rgba(238, 239, 241, 0.5);
  border-radius: 4px;
}

.section-group {
  padding: 8px;
  border-bottom: 1px solid #eee;
  &:last-child {
    border-bottom: none;
  }
}

.section-title {
  font-weight: 700;
  padding: 6px 0;
  font-family: 'Times New Roman', 'SimSun', sans-serif;
}

.content-row {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  padding: 4px 0;
}

.content-item {
  font-family: 'SimSun', serif;
  cursor: pointer;
  transition: background-color 0.3s;
  padding: 2px 4px;
  border-radius: 3px;

  &:hover {
    background-color: #f0f5ff;
  }
}

.highlight {
  background-color: #e8efff !important;
  box-shadow: 0 0 4px rgba(56, 114, 255, 0.3);
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
