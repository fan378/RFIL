<script setup lang="ts">
import { computed, reactive, ref, onMounted } from 'vue';
import { NButton, NSpace } from 'naive-ui';
import { BookOutline as BookIcon } from '@vicons/ionicons5';
import { useTaskStore } from '@/store/modules/task';
import { useAppStore } from '@/store/modules/app';
import BasicInfoTable from './tables/BasicInfoTable.vue';
import BriefHistoryTable from './tables/BriefHistoryTable.vue';
import MainTestAndExaminationTable from './tables/MainTestAndExaminationTable.vue';
import CourseAndTreatmentTable from './tables/CourseAndTreatmentTable.vue';

// 公共配置
const BASIC_INFO_COLUMNS = [
  [
    { label: '姓名:', key: '姓名', colspan: 1 },
    { label: '年龄:', key: '年龄', colspan: 1 },
    { label: '性别:', key: '性别', colspan: 1 }
  ],
  [
    { label: '住院号:', key: '住院号', colspan: 1 },
    { label: '床号:', key: '床号', colspan: 3 }
  ],
  [{ label: '科室:', key: '科室', colspan: 5 }],
  [
    { label: '入院时间:', key: '入院时间', colspan: 2 },
    { label: '出院时间:', key: '出院时间', colspan: 2 }
  ],
  [{ label: '入院诊断:', key: '入院诊断', colspan: 5 }],
  [{ label: '出院诊断:', key: '出院诊断', colspan: 5 }]
];

// 响应式数据
const appStore = useAppStore();
const taskStore = useTaskStore();
const gap = computed(() => (appStore.isMobile ? 0 : 16));
const displaying = ref(1);
const props = defineProps<{ isEditing: boolean }>();

// 高亮项目
const highlightedItems = ref([]);

// 显示控制
const DISPLAY_SECTIONS = 4;
const navigate = (direction: 'prev' | 'next') => {
  const newValue = displaying.value + (direction === 'prev' ? -1 : 1);
  displaying.value = Math.max(1, Math.min(DISPLAY_SECTIONS, newValue));
};

// 展示来源
const clickItem = ref('姓名');
const emit = defineEmits(['update:clickItem']);
// const showSource = (id: string) => {
//   // 去掉 '病人-' 或 '医生-' 前缀
//   let cleanId = id.replace(/^(病人-|医生-)/, '');

//   // 处理特定格式：模块-数字-数字
//   const pattern = /^(.+-\d+)-\d+$/;
//   const match = cleanId.match(pattern);
//   if (match) {
//     cleanId = match[1]; // 只保留第一个数字
//   }

//   clickItem.value = cleanId;
//   // 将click的值传给父组件
//   emit('update:clickItem', clickItem.value);
//   console.log(`你点击了: ${cleanId}`);
// };
const showSource = (id: string) => {
  // 检查是否以"病人-"开头
  if (!id.startsWith('病人-')) {
    return;
  }

  // 去掉 '病人-' 前缀
  let cleanId = id.replace(/^(病人-)/, '');

  // 判断是否以"住院期间医疗情况"开头
  if (!cleanId.startsWith('住院期间医疗情况')) {
    // 处理特定格式：模块-数字-数字
    const pattern = /^(.+-\d+)-\d+$/;
    const match = cleanId.match(pattern);
    if (match) {
      cleanId = match[1]; // 只保留第一个数字
    }
  }

  clickItem.value = cleanId;
  // 将click的值传给父组件
  emit('update:clickItem', clickItem.value);
  console.log(`你点击了: ${cleanId}`);
};
// 抽象数据模型
const createSummaryData = (data: any) => {
  // 如果是source_pattern格式的数据，需要转换
  if (data && data.姓名 && Array.isArray(data.姓名)) {
    return reactive({
      basicInfo: {
        姓名: data.姓名?.[0] || '',
        性别: data.性别?.[0] || '',
        年龄: data.年龄?.[0] || '',
        住院号: data.住院号?.[0] || '',
        床号: data.床号?.[0] || '',
        科室: data.科室?.[0] || '',
        入院时间: data.入院时间?.[0] || '',
        出院时间: data.出院时间?.[0] || '',
        低压: data.低压?.[0] || '',
        高压: data.高压?.[0] || '',
        脉搏: data.脉搏?.[0] || '',
        呼吸: data.呼吸?.[0] || '',
        体温: data.体温?.[0] || '',
        入院诊断: data.入院诊断?.[0] || '',
        出院诊断: data.出院诊断?.[0] || '',
        入院时简要病史: data.入院时简要病史 || [],
        体检摘要: data.体检摘要 || [],
        // 为了兼容BriefHistoryTable组件
        '体温(T)': data.体温?.[0] || '',
        '脉搏(P)': data.脉搏?.[0] || '',
        '呼吸(R)': data.呼吸?.[0] || '',
        '高压(BP高)': data.高压?.[0] || '',
        '低压(BP低)': data.低压?.[0] || ''
      },
      medicalInfo: data.住院期间医疗情况 || [],
      treatmentCourse: data.病程与治疗情况 || [],
      dischargeStatus: data.出院时情况 || [],
      medicationAdvice: data.出院后用药建议 || [],
      diagnosis: data.出院诊断?.[0] || ''
    });
  }

  // 如果是原有的格式
  return reactive({
    basicInfo: {
      ...data.患者基本信息, // 合并患者的基本信息
      出院诊断: data.出院诊断 // 添加出院诊断
    },
    medicalInfo: data.住院期间医疗情况,
    treatmentCourse: data.病程与治疗情况,
    dischargeStatus: data.出院时情况,
    medicationAdvice: data.出院后用药建议,
    diagnosis: data.出院诊断
  });
};

// 初始化数据
const processedJson = reactive(taskStore.getProcessedJson());
const patient = createSummaryData(processedJson.patient_new || processedJson.source_pattern);
const doctor = createSummaryData(processedJson.doctor_new || processedJson.source_pattern);
// console.log(patient, doctor);

// 初始化函数，用于在组件挂载时设置所有元素的 data-highlightnull 属性
const initializeHighlightNull = () => {
  //console.log('开始初始化高亮状态');

  // 使用 MutationObserver 监听 DOM 变化
  const observer = new MutationObserver((_mutations) => {
    // console.log('DOM发生变化，重新检查元素');
    applyHighlightNull();
  });

  // 开始观察整个文档
  observer.observe(document.body, {
    childList: true,
    subtree: true
  });

  // 应用高亮的函数
  const applyHighlightNull = () => {
    //console.log('当前doctor_pattern:', processedJson.doctor_pattern);

    // 检查doctor_pattern是否存在且不为空
    if (!processedJson.doctor_pattern || Object.keys(processedJson.doctor_pattern).length === 0) {
      console.log('doctor_pattern为空，跳过高亮处理');
      return;
    }

    // 遍历所有病人元素
    Object.entries(processedJson.doctor_pattern).forEach(([patientId, doctorId]) => {
      //console.log('处理病人元素:', { patientId, doctorId });

      // 如果医生ID是patient_None，直接应用highlightnull样式
      if (doctorId === 'patient_None') {
        // 尝试多种可能的ID格式
        const possibleIds = [
          patientId, // 原始ID
          `病人-${patientId}`, // 带前缀的ID
          `病人-${patientId.split('-').slice(1).join('-')}` // 去掉第一个数字的ID
        ];

        //console.log('尝试查找元素，可能的ID:', possibleIds);

        // 尝试所有可能的ID
        for (const id of possibleIds) {
          const elements = document.querySelectorAll(`[id^="${id}"]`);
          //console.log(`查找以${id}开头的元素:`, elements);

          if (elements.length > 0) {
            elements.forEach(el => {
              // 检查内容是否为时间格式
              const content = el.textContent?.trim() || '';
              if (!isTimeFormat(content, el.id)) {
                el.classList.add('highlightnull');
                el.setAttribute('data-highlightnull', 'active');
                //console.log(`已为元素添加高亮: ${el.id}`);
              } else {
                //console.log(`跳过时间格式内容的高亮: ${content}`);
              }
            });
            break; // 找到元素后退出循环
          }
        }
      }
    });

    // 遍历所有医生元素
    const doctorIds = new Set(Object.values(processedJson.doctor_pattern));
    //console.log('所有医生ID:', Array.from(doctorIds));

    doctorIds.forEach(doctorId => {
      //console.log('处理医生元素:', doctorId);

      // 检查是否有任何病人映射到这个医生
      const hasPatients = Object.values(processedJson.doctor_pattern).includes(doctorId);
      if (!hasPatients || doctorId === 'doctor_None') {
        if (doctorId === 'doctor_None') {
          // 如果是doctor_None，找到对应的病人ID并高亮
          const patientIds = Object.entries(processedJson.doctor_pattern)
            .filter(([_, dId]) => dId === 'doctor_None')
            .map(([pId]) => pId);

          //console.log('找到doctor_None对应的病人ID:', patientIds);

          patientIds.forEach(patientId => {
            // 尝试多种可能的ID格式
            const possibleIds = [
              patientId, // 原始ID
              `病人-${patientId}`, // 带前缀的ID
              `病人-${patientId.split('-').slice(1).join('-')}` // 去掉第一个数字的ID
            ];

            //console.log('尝试查找病人元素，可能的ID:', possibleIds);

            // 尝试所有可能的ID
            for (const id of possibleIds) {
              const elements = document.querySelectorAll(`[id^="${id}"]`);
              //console.log(`查找以${id}开头的元素:`, elements);

              if (elements.length > 0) {
                elements.forEach(el => {
                  // 检查内容是否为时间格式
                  const content = el.textContent?.trim() || '';
                  if (!isTimeFormat(content, el.id)) {
                    el.classList.add('highlightnull');
                    el.setAttribute('data-highlightnull', 'active');
                    //console.log(`已为病人元素添加高亮: ${el.id}`);
                  } else {
                    //console.log(`跳过时间格式内容的高亮: ${content}`);
                  }
                });
                break; // 找到元素后退出循环
              }
            }
          });
        } else {
          // 其他情况使用精确匹配的ID
          const exactId = `医生-${doctorId}`;
          //console.log('尝试查找医生元素，精确ID:', exactId);

          const element = document.getElementById(exactId);
          if (element) {
            // 检查内容是否为时间格式
            const content = element.textContent?.trim() || '';
            if (!isTimeFormat(content, element.id)) {
              element.classList.add('highlightnull');
              element.setAttribute('data-highlightnull', 'active');
              //console.log(`已为医生元素添加高亮: ${element.id}`);
            } else {
              //console.log(`跳过时间格式内容的高亮: ${content}`);
            }
          } else {
            //console.log(`未找到精确匹配的医生元素: ${exactId}`);
          }
        }
      }
    });
  };

  // 初始应用高亮
  applyHighlightNull();

  // 5秒后停止观察
  setTimeout(() => {
    observer.disconnect();
    console.log('停止观察DOM变化');
  }, 5000);
};

// 在组件挂载时初始化
onMounted(() => {
  initializeHighlightNull();
});

// 判断是否为时间格式的辅助函数
const isTimeFormat = (text: string, id: string): boolean => {
  // 如果是入院时间或出院时间，返回false（允许高亮）
  if (id.includes('入院时间') || id.includes('出院时间')) {
    return false;
  }

  // 匹配常见的时间格式
  const timePatterns = [
    /^\d{4}[-/]\d{1,2}[-/]\d{1,2}$/, // 2024-03-24 或 2024/03/24
    /^\d{4}[-/]\d{1,2}[-/]\d{1,2}\s+\d{1,2}:\d{1,2}(:\d{1,2})?$/, // 2024-03-24 14:30 或 2024-03-24 14:30:00
    /^\d{1,2}:\d{1,2}(:\d{1,2})?$/, // 14:30 或 14:30:00
    /^\d{4}年\d{1,2}月\d{1,2}日$/, // 2024年03月24日
    /^\d{4}年\d{1,2}月\d{1,2}日\s+\d{1,2}时\d{1,2}分(\d{1,2}秒)?$/ // 2024年03月24日 14时30分
  ];

  return timePatterns.some(pattern => pattern.test(text.trim()));
};

// 修改高亮逻辑
const highlight = (id: string) => {
  //console.log('开始高亮处理，目标ID:', id);

  // 判断当前触发高亮的是病人还是医生模块
  const isPatient = id.startsWith('病人-');
  const isDoctor = id.startsWith('医生-');
  //console.log('元素类型:', { isPatient, isDoctor });

  // 获取元素内容
  const getElementContent = (elementId: string): string => {
    const element = document.getElementById(elementId);
    const content = element ? element.textContent || '' : '';
    //console.log(`获取元素内容 [${elementId}]:`, content);
    return content;
  };

  // 核心高亮函数（处理单个元素）
  const applyHighlight = (targetId: string, isNone: boolean) => {
    //console.log(`应用高亮 [${targetId}], isNone:`, isNone);
    const element = document.getElementById(targetId);
    if (!element) {
      //console.warn(`未找到元素: ${targetId}`);
      return;
    }

    // 获取元素内容并判断是否为时间格式
    const content = getElementContent(targetId);
    if (isTimeFormat(content, targetId)) {
      //console.log(`跳过时间格式内容的高亮: ${content}`);
      return;
    }

    // 清除旧的高亮状态
    element.classList.remove('highlight');
    element.removeAttribute('data-highlight');

    // 根据是否是无匹配状态应用样式
    if (isNone) {
      element.classList.add('highlightnull');
      element.setAttribute('data-highlightnull', 'active');
      //console.log(`应用无匹配高亮样式到: ${targetId}`);
    } else {
      element.classList.add('highlight');
      element.setAttribute('data-highlight', 'active');
      //console.log(`应用正常高亮样式到: ${targetId}`);
    }
  };

  // 检查doctor_pattern是否存在且不为空
  if (!processedJson.doctor_pattern || Object.keys(processedJson.doctor_pattern).length === 0) {
    console.log('doctor_pattern为空，跳过高亮处理');
    return;
  }

  // 1. 处理正向映射（病人 → 医生）
  if (isPatient) {
    const doctorId = processedJson.doctor_pattern[id];
    //console.log('病人映射到医生:', { patientId: id, doctorId });
    // 高亮病人自己
    applyHighlight(id, doctorId === 'patient_None');
    // 如果有对应的医生，高亮医生（否则 doctorId 为 doctor_None）
    if (doctorId && doctorId !== 'patient_None') {
      applyHighlight(doctorId, false);
    }
  }

  // 2. 处理反向映射（医生 → 所有关联病人）
  if (isDoctor) {
    const patientIds = Object.entries(processedJson.doctor_pattern)
      .filter(([_, dId]) => dId === id)
      .map(([pId]) => pId);
    //console.log('医生关联的病人:', { doctorId: id, patientIds });
    const hasNoPatients = patientIds.length === 0;
    const isSpecialNoneCase = id === 'doctor_None';
    applyHighlight(id, isSpecialNoneCase || hasNoPatients);
    patientIds.forEach(patientId => {
      const isPatientNone = processedJson.doctor_pattern[patientId] === 'patient_None';
      applyHighlight(patientId, isPatientNone);
    });
  }
};

// 取消高亮逻辑（双向清理）
const removeHighlight = (id: string) => {
  //console.log('开始移除高亮:', id);

  const cleanup = (targetId: string) => {
    //console.log(`清理元素高亮: ${targetId}`);
    const element = document.getElementById(targetId);
    if (element) {
      element.classList.remove('highlight');
      element.removeAttribute('data-highlight');
      //console.log(`已清理元素: ${targetId}`);
    } else {
      //console.warn(`未找到要清理的元素: ${targetId}`);
    }
  };

  // 清理当前元素
  cleanup(id);

  // 检查doctor_pattern是否存在且不为空
  if (!processedJson.doctor_pattern || Object.keys(processedJson.doctor_pattern).length === 0) {
    console.log('doctor_pattern为空，跳过清理处理');
    return;
  }

  // 清理关联元素
  const isPatient = id.startsWith('病人-');
  const isDoctor = id.startsWith('医生-');
  //console.log('清理类型:', { isPatient, isDoctor });

  // 1. 如果是病人，清理对应的医生
  if (isPatient) {
    const doctorId = processedJson.doctor_pattern[id];
    //console.log('清理关联医生:', { patientId: id, doctorId });
    if (doctorId) cleanup(doctorId);
  }

  // 2. 如果是医生，清理所有关联病人
  if (isDoctor) {
    const patientIds = Object.entries(processedJson.doctor_pattern)
      .filter(([_, dId]) => dId === id)
      .map(([pId]) => pId);
    //console.log('清理关联病人:', { doctorId: id, patientIds });
    patientIds.forEach(patientId => cleanup(patientId));
  }
};
// 样式
const headerStyle = {
  padding: '6px var(--n-padding-left)',
  textAlign: 'center',
  fontWeight: '600',
  position: 'sticky',
  top: '0',
  background: 'white',
  zIndex: '10'
};
const footerStyle = {
  padding: '6px 6px 6px 6px',
  position: 'sticky',
  bottom: '-1px',
  background: 'white',
  zIndex: '10'
};
const contentStyle = {
  padding: '0 6px 0 6px',
  position: 'sticky'
};

// 导出
defineExpose({
  patient
});
</script>

<template>
  <NGrid :x-gap="gap" :y-gap="0" responsive="screen" item-responsive>
    <!-- 可复用的摘要卡片组件 -->
    <NGi v-for="(summary, index) in [patient, doctor]" :key="index" span="24 s:24 m:12">
      <NCard
        size="small"
        :bordered="false"
        :title="index === 0 ? '大模型版出院小结' : '医生版出院小结'"
        class="summary-card card-wrapper"
        :header-style="headerStyle"
        :footer-style="footerStyle"
        :content-style="contentStyle"
      >
        <!-- 基本信息表格 -->
        <BasicInfoTable
          v-show="displaying === 1"
          :data="summary.basicInfo"
          :columns="BASIC_INFO_COLUMNS"
          :is-editing="index === 0 && props.isEditing"
          :prefix="index === 0 ? '病人' : '医生'"
          @highlight="highlight"
          @remove-highlight="removeHighlight"
          @show-source="showSource"
        />

        <!-- 病史部分 -->
        <BriefHistoryTable
          v-show="displaying === 2"
          :data="summary.basicInfo"
          :is-editing="index === 0 && props.isEditing"
          :prefix="index === 0 ? '病人' : '医生'"
          @highlight="highlight"
          @remove-highlight="removeHighlight"
          @show-source="showSource"
        />

        <!-- 检查结果 -->
        <MainTestAndExaminationTable
          v-show="displaying === 3"
          :items="summary.medicalInfo"
          :highlighted-items="highlightedItems"
          :is-editing="index === 0 && props.isEditing"
          :prefix="index === 0 ? '病人' : '医生'"
          @highlight="highlight"
          @remove-highlight="removeHighlight"
          @show-source="showSource"
        />

        <!-- 治疗过程 -->
        <CourseAndTreatmentTable
          v-show="displaying === 4"
          :treatment="summary.treatmentCourse"
          :status="summary.dischargeStatus"
          :advice="summary.medicationAdvice"
          :is-editing="index === 0 && props.isEditing"
          :prefix="index === 0 ? '病人' : '医生'"
          @highlight="highlight"
          @remove-highlight="removeHighlight"
          @show-source="showSource"
        />

        <template #footer>
          <NSpace justify="end">
            <NButton size="small" :disabled="displaying === 1" @click="navigate('prev')">&lt;</NButton>
            <NButton size="small" :disabled="displaying === 4" @click="navigate('next')">&gt;</NButton>
          </NSpace>
        </template>
      </NCard>
    </NGi>

    <!-- 源代码部分保持原样 -->
    <NGi span="24 s:24 m:24">
      <!-- ... -->
    </NGi>
  </NGrid>
</template>

<style scoped>
/* 优化后的样式 */
.summary-card {
  flex: 1;
  display: flex;
  flex-direction: column;
  max-height: 43vh;
  min-height: 43vh;
  overflow: auto;
}

.dynamic-table {
  table-layout: fixed;
  width: 100%;
  border: 2px solid rgba(238, 239, 241, 0.5);
}

.table-cell {
  padding: 4px;
  vertical-align: top;
}
/* 蓝色高亮（正常关联） */
.highlight {
  background: #e8f4ff;
  border: 2px solid #b6d4fe;
}

/* 红色高亮（无关联） */
.highlightnull {
  background: #847979;
  border: 2px solid #facbcb;
}
.dhighlightnull {
  background: #847979;
  border: 2px solid #facbe8;
}

/* 平滑过渡 */
[class*="highlight"] {
  transition: all 0.3s ease;
}
</style>
