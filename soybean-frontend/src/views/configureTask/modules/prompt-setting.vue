<script setup lang="ts">
import { computed, h, reactive, ref, watch } from 'vue';
import {
  NButton,
  NCard,
  NCheckbox,
  NCollapse,
  NCollapseItem,
  NDatePicker,
  NDynamicInput,
  NForm,
  NFormItem,
  NGi,
  NGrid,
  NInput,
  NInputNumber,
  NModal,
  NSelect,
  NSpace,
  NTag
} from 'naive-ui';
import { $t } from '@/locales';
import { useAppStore } from '@/store/modules/app';
import { useTaskStore } from '@/store/modules/task';
import promptDefaultConfig from '@/constants/prompt-default-config.json';

// 添加 props 接收科室选择
interface Props {
  selectedDepartment?: string;
}

const props = withDefaults(defineProps<Props>(), {
  selectedDepartment: '乳腺外科'
});

const appStore = useAppStore();
const taskStore = useTaskStore();
const gap = computed(() => (appStore.isMobile ? 0 : 16));

const { logic_prompts, section_contents, section_keywords, section_columns } = taskStore.getPrompt();
const SPECIAL_FIELD = '住院期间医疗情况';

// modal
const showModal = ref(false);
const editingIndex = ref<number | null>(null);
const editingContent = ref('');
const saveEdit = () => {
  if (editingIndex.value !== null) {
    const index = editingIndex.value as unknown as keyof typeof logic_prompts;
    logic_prompts[index] = editingContent.value;
  }
  showModal.value = false;
};

const tagOptions = [
  { label: '抽取', value: '抽取' },
  { label: '推理', value: '推理' },
  { label: '摘要', value: '摘要' },
  { label: '判断', value: '判断' },
  { label: '知识', value: '知识' }
];

// 时间筛选类型选项
const timeFilterOptions = [
  { label: '全部时间', value: 'all' },
  { label: '最新一条', value: 'latest' },
  { label: '最早一条', value: 'earliest' },
  { label: '最近几天', value: 'recent_days' },
  { label: '时间范围', value: 'date_range' }
];

// 检验状态筛选选项
const labStatusFilterOptions = [
  { label: '全部状态', value: 'all' },
  { label: '仅看异常', value: 'abnormal' },
  { label: '仅看正常', value: 'normal' },
  { label: '仅看偏高', value: 'high' },
  { label: '仅看偏低', value: 'low' }
];

// 排序选项
const sortOrderOptions = [
  { label: '升序', value: 'asc' },
  { label: '降序', value: 'desc' }
];

// 渲染多选标签的函数（参考原代码）
const renderMultipleTag = ({ option, handleClose }: { option: any, handleClose: () => void }) => {
  return h(
    NTag,
    {
      type: 'info',
      closable: true,
      onClose: (e: Event) => {
        e.stopPropagation();
        handleClose();
      },
      style: { fontSize: '12px', borderRadius: '0', marginRight: '4px' }
    },
    { default: () => option.label || option }
  );
};

const onCreate = () => {
  return reactive({
    label: '推理',
    value: '',
    sourceRecords: [],
    fieldNames: ''
  });
};

interface FormDataItem {
  label: string;
  value: string;
  sourceRecords: string[];
  fieldNames: string;
}

// 检验信息配置接口
interface LabTestsConfig {
  timeFilterType: string;
  recentDays: number;
  startDate: number | null;
  endDate: number | null;
  statusFilter: string;
  keywords: string[]; // 改为数组类型
  includeTime: boolean;
  sortOrder: string;
}

// 检查信息配置接口
interface ExaminationsConfig {
  timeFilterType: string;
  recentDays: number;
  startDate: number | null;
  endDate: number | null;
  keywords: string[]; // 改为数组类型
  includeTime: boolean;
  sortOrder: string;
}

// 住院期间医疗情况的完整配置接口
interface MedicalSituationConfig {
  labTests: LabTestsConfig;
  examinations: ExaminationsConfig;
}

// 新增复选框控制变量
interface MedicalCheckboxState {
  labTestsEnabled: boolean;
  examinationsEnabled: boolean;
}

interface FormData {
  [key: string]: FormDataItem[] | string | MedicalSituationConfig;
}

// 总结指南数据
const summaryGuidance = reactive<Record<string, string>>({});

const formData = reactive<FormData>({
  [SPECIAL_FIELD]: {
    labTests: {
      timeFilterType: 'all',
      recentDays: 7,
      startDate: null,
      endDate: null,
      statusFilter: 'all',
      keywords: [], // 改为空数组
      includeTime: true,
      sortOrder: 'asc'
    },
    examinations: {
      timeFilterType: 'all',
      recentDays: 7,
      startDate: null,
      endDate: null,
      keywords: [], // 改为空数组
      includeTime: true,
      sortOrder: 'asc'
    }
  } as MedicalSituationConfig
});

// 复选框状态控制
const medicalCheckboxState = reactive<MedicalCheckboxState>({
  labTestsEnabled: true,
  examinationsEnabled: true
});

// 为不同字段创建个性化默认配置的函数（支持多个默认配置）
const createDefaultConfigs = (fieldName: string, department: string = '乳腺外科') => {
  // 从JSON配置文件中获取对应科室的默认配置
  const departmentConfig = promptDefaultConfig[department as keyof typeof promptDefaultConfig];

  if (departmentConfig && typeof departmentConfig === 'object' && !Array.isArray(departmentConfig)) {
    const defaultConfigurations = (departmentConfig as any).defaultConfigurations;
    if (defaultConfigurations) {
      const configs = defaultConfigurations[fieldName] || [
        promptDefaultConfig.fallbackConfig
      ];

      // 为每个配置添加reactive
      return Array.isArray(configs) ? configs.map((config: any) => reactive(config)) : [reactive(promptDefaultConfig.fallbackConfig)];
    }
  }

  // 如果没有找到科室配置，使用默认配置
  return [reactive(promptDefaultConfig.fallbackConfig)];
};

// 初始化配置函数
const initializeConfig = () => {
  Object.entries(logic_prompts).forEach(([key, value]) => {
    if (key !== SPECIAL_FIELD) {
      // 为每个字段添加个性化的默认配置
      const defaultConfigs = createDefaultConfigs(key, props.selectedDepartment);
      formData[key] = Array.isArray(value) && value.length > 0 ? value : defaultConfigs;

      // 为每个字段配置具体的总结指南
      const departmentConfig = promptDefaultConfig[props.selectedDepartment as keyof typeof promptDefaultConfig];
      const departmentSummaryGuidance = departmentConfig && typeof departmentConfig === 'object' && !Array.isArray(departmentConfig) ? (departmentConfig as any).summaryGuidance : null;
      summaryGuidance[key] = (departmentSummaryGuidance && departmentSummaryGuidance[key]) || `${key}应根据患者具体情况进行个性化总结，确保信息准确、完整、有临床指导意义。`;
      }
  });
};

// 初始化其他字段的数据
initializeConfig();

// 监听科室变化
watch(() => props.selectedDepartment, () => {
  initializeConfig();
});

// 响应式的获取选项函数
const getSourceOptions = computed(() => {
  return (prompt_index: string, currentIndex?: number) => {
    const allDocumentsOption = { label: '全部文书', value: '全部文书' };

    const currentFieldData = formData[prompt_index];

    const logicRuleOptions: Array<{label: string, value: string}> = [];

    if (Array.isArray(currentFieldData) && typeof currentIndex === 'number') {
      // 只添加当前规则之前的逻辑规则选项
      for (let i = 0; i < currentIndex; i += 1) {
        const item = currentFieldData[i];
        if (item && item.value && item.value.trim()) {
          logicRuleOptions.push({
            label: `第${i + 1}条逻辑规则`,
            value: `第${i + 1}条逻辑规则`
          });
        }
      }
    }

    if (!section_columns || !(section_columns as any)[prompt_index]) {
      return [allDocumentsOption, ...logicRuleOptions];
    }

    const options = Object.values((section_columns as any)[prompt_index]).map((item: any) => ({
      label: item,
      value: item
    }));

    return [allDocumentsOption, ...logicRuleOptions, ...options];
  };
});

// 关键词输入框的响应式变量
const labTestsKeywordsInput = ref('');
const examinationsKeywordsInput = ref('');

// 初始化输入框的值
labTestsKeywordsInput.value = (formData[SPECIAL_FIELD] as MedicalSituationConfig).labTests.keywords.join(' ');
examinationsKeywordsInput.value = (formData[SPECIAL_FIELD] as MedicalSituationConfig).examinations.keywords.join(' ');

// 更新关键词数组的方法
const updateLabTestsKeywords = () => {
  const keywords = labTestsKeywordsInput.value
    .split(' ')
    .map(k => k.trim())
    .filter(k => k !== '');
  (formData[SPECIAL_FIELD] as MedicalSituationConfig).labTests.keywords = keywords;
};

const updateExaminationsKeywords = () => {
  const keywords = examinationsKeywordsInput.value
    .split(' ')
    .map(k => k.trim())
    .filter(k => k !== '');
  (formData[SPECIAL_FIELD] as MedicalSituationConfig).examinations.keywords = keywords;
};

// 自动更新value（按动作类型定制格式）
watch(formData, (newVal) => {
  Object.entries(newVal).forEach(([promptIndex, items]) => {
    if (promptIndex === SPECIAL_FIELD) return; // 跳过特殊字段

    // 其他字段的处理
    if (!Array.isArray(items)) return;

    (items as FormDataItem[]).forEach(item => {
      if (!item.label || !item.sourceRecords || !item.fieldNames) return;

      // 确保 sourceRecords 是数组
      if (!Array.isArray(item.sourceRecords)) {
        item.sourceRecords = item.sourceRecords ? [item.sourceRecords] : [];
      }

      switch(item.label) {
        case '抽取':
          item.value = `从 ${item.sourceRecords.join('、')} 抽取 ${item.fieldNames}`;
          break;
        case '推理':
          item.value = `根据 ${item.sourceRecords.join('、')} 推理得出：${item.fieldNames}`;
          break;
        case '摘要':
          item.value = `从 ${item.sourceRecords.join('、')} 摘要关键点：${item.fieldNames}`;
          break;
        case '判断':
          item.value = `基于 ${item.sourceRecords.join('、')} 判断结果为：${item.fieldNames}`;
          break;
        case '知识':
          item.value = `将 ${item.sourceRecords.join('、')} 与知识库匹配，得到：${item.fieldNames}`;
          break;
        default:
          item.value = `${item.label}：${item.sourceRecords.join('、')} → ${item.fieldNames}`;
      }
    });
  });
}, { deep: true });

// 生成时间筛选配置
const buildTimeFilter = (config: { type: string; days: number; startDate: number | null; endDate: number | null }) => {
  switch (config.type) {
    case 'recent_days':
      return { type: 'recent_days', days: config.days || 7 };
    case 'date_range':
      return {
        type: 'date_range',
        start_date: config.startDate ? new Date(config.startDate).toISOString().split('T')[0] : '',
        end_date: config.endDate ? new Date(config.endDate).toISOString().split('T')[0] : ''
      };
    default:
      return { type: config.type };
  }
};

// 解析关键词数组为数组（保持数组格式）
const parseKeywords = (keywordsArray: string[]): string[] => {
  if (!keywordsArray || !Array.isArray(keywordsArray)) {
    return [];
  }
  return keywordsArray.filter(Boolean);
};

// 生成检验信息配置
const buildLabTestsConfig = (config: LabTestsConfig) => {
  return {
    time_filter: buildTimeFilter({
      type: config.timeFilterType,
      days: config.recentDays,
      startDate: config.startDate,
      endDate: config.endDate
    }),
    filter: {
      status: config.statusFilter,
      keywords: parseKeywords(config.keywords)
    },
    output_format: {
      include_time: config.includeTime,
      time_sort_order: config.sortOrder
    }
  };
};

// 生成检查信息配置
const buildExaminationsConfig = (config: ExaminationsConfig) => {
  return {
    time_filter: buildTimeFilter({
      type: config.timeFilterType,
      days: config.recentDays,
      startDate: config.startDate,
      endDate: config.endDate
    }),
    filter: {
      keywords: parseKeywords(config.keywords)
    },
    output_format: {
      include_time: config.includeTime,
      time_sort_order: config.sortOrder
    }
  };
};

// 生成完整的医疗配置JSON
const generateMedicalConfig = (config: MedicalSituationConfig) => {
  const result: any = {};

  // 根据复选框状态决定是否包含配置
  if (medicalCheckboxState.labTestsEnabled) {
    result.lab_tests_config = buildLabTestsConfig(config.labTests);
  }

  if (medicalCheckboxState.examinationsEnabled) {
    result.examinations_config = buildExaminationsConfig(config.examinations);
  }

  return JSON.stringify(result, null, 2);
};

// 监听formData和medicalCheckboxState的变化
watch(
  [formData, medicalCheckboxState],
  () => {
    Object.entries(formData).forEach(([promptIndex, items]) => {
      if (promptIndex === SPECIAL_FIELD) {
        // 对于医疗情况，生成配置JSON
        const config = items as MedicalSituationConfig;
        logic_prompts[SPECIAL_FIELD] = generateMedicalConfig(config);
        return;
      }

      // 添加数组校验
      if (!Array.isArray(items)) {
        console.error(`Invalid data structure for ${promptIndex}:`, items);
        return;
      }

      items.forEach(item => {
        // 生成value逻辑
        if (!item.label) return;

        // 确保 sourceRecords 是数组
        if (!Array.isArray(item.sourceRecords)) {
          item.sourceRecords = item.sourceRecords ? [item.sourceRecords] : [];
        }

        const sources = item.sourceRecords.join('、');
        const fields = item.fieldNames;

        switch (item.label) {
          case '抽取':
            item.value = `从 ${sources} 抽取 ${fields}`;
            break;
          case '推理':
            item.value = `根据 ${sources} 推理得出：${fields}`;
            break;
          case '摘要':
            item.value = `从 ${sources} 摘要关键点：${fields}`;
            break;
          case '判断':
            item.value = `基于 ${sources} 判断结果为：${fields}`;
            break;
          case '知识':
            item.value = `将 ${sources} 与知识库匹配，得到：${fields}`;
            break;
          default:
            item.value = `${item.label}：${sources} → ${fields}`;
        }
      });
    });
  },
  { deep: true }
);

defineExpose({
  getFormData: () => {
    const result: Record<string, any> = {};
    Object.entries(formData).forEach(([key, value]) => {
      if (key === SPECIAL_FIELD) {
        // 对于特殊字段，返回生成的配置JSON而不是原始数据
        const config = value as MedicalSituationConfig;
        const medicalConfig: any = {};

        // 根据复选框状态决定是否包含配置
        if (medicalCheckboxState.labTestsEnabled) {
          medicalConfig.lab_tests_config = buildLabTestsConfig(config.labTests);
        }

        if (medicalCheckboxState.examinationsEnabled) {
          medicalConfig.examinations_config = buildExaminationsConfig(config.examinations);
        }

        result[key] = medicalConfig;
      } else if (Array.isArray(value)) {
        // 对于其他字段，返回新的格式：包含logic_rule和user_guidance
        result[key] = {
          logic_rule: value.map(item => ({
            label: item.label,
            value: item.value,
            sourceRecords: item.sourceRecords,
            fieldNames: item.fieldNames
          })),
          user_guidance: summaryGuidance[key] || `${key}总结指南`
        };
      }
    });
    return result;
  }
});
</script>

<template>
  <div style="height: 72vh; overflow: auto">
    <NSpace vertical :size="16">
      <NGrid :x-gap="gap" cols="1">
        <NGi v-for="(logic_prompt, prompt_index) in logic_prompts" :key="prompt_index">
          <NCard
            size="small"
            :title="$t('page.task.' + prompt_index)"
            class="card-wrapper"
            header-style="font-weight: 1000;"
          >
            <NForm :model="formData">
              <NFormItem label="执行逻辑：">
                <template v-if="prompt_index === SPECIAL_FIELD">
                  <!-- 住院期间医疗情况的配置界面 -->
                  <div class="medical-config-container">

                    <!-- 检验信息配置区 -->
                    <fieldset class="config-fieldset">
                      <legend class="config-legend">
                        <NCheckbox
                          v-model:checked="medicalCheckboxState.labTestsEnabled"
                        >
                          检验信息 (Lab Tests)
                        </NCheckbox>
                      </legend>
                      <div v-if="medicalCheckboxState.labTestsEnabled" class="controls-row">
                        <!-- 时间筛选 -->
                        <div class="control-group">
                          <label>时间:</label>
                          <NSelect
                            v-model:value="(formData[SPECIAL_FIELD] as MedicalSituationConfig).labTests.timeFilterType"
                            :options="timeFilterOptions"
                            style="width: 120px"
                          />

                          <!-- 条件性显示的时间输入 -->
                          <div v-if="(formData[SPECIAL_FIELD] as MedicalSituationConfig).labTests.timeFilterType === 'recent_days'" class="time-extra-input">
                            <NInputNumber
                              v-model:value="(formData[SPECIAL_FIELD] as MedicalSituationConfig).labTests.recentDays"
                              :min="1"
                              :max="365"
                              style="width: 80px"
                            />
                            <span>天内</span>
                          </div>

                          <div v-if="(formData[SPECIAL_FIELD] as MedicalSituationConfig).labTests.timeFilterType === 'date_range'" class="time-extra-input">
                            <NDatePicker
                              v-model:value="(formData[SPECIAL_FIELD] as MedicalSituationConfig).labTests.startDate"
                              type="date"
                              placeholder="开始日期"
                              style="width: 140px"
                            />
                            <span>-</span>
                            <NDatePicker
                              v-model:value="(formData[SPECIAL_FIELD] as MedicalSituationConfig).labTests.endDate"
                              type="date"
                              placeholder="结束日期"
                              style="width: 140px"
                            />
                          </div>
                        </div>

                        <!-- 状态筛选 -->
                        <div class="control-group">
                          <label>状态:</label>
                          <NSelect
                            v-model:value="(formData[SPECIAL_FIELD] as MedicalSituationConfig).labTests.statusFilter"
                            :options="labStatusFilterOptions"
                            style="width: 120px"
                          />
                        </div>

                        <!-- 关键词输入框 -->
                        <div class="control-group">
                          <label>关键词:</label>
                          <NInput
                            v-model:value="labTestsKeywordsInput"
                            style="width: 400px"
                            placeholder="输入关键词，用空格分隔"
                            @blur="updateLabTestsKeywords"
                          />
                        </div>

                        <!-- 输出格式控制 -->
                        <div class="output-controls">
                          <NCheckbox
                            v-model:checked="(formData[SPECIAL_FIELD] as MedicalSituationConfig).labTests.includeTime"
                          >
                            包含时间
                          </NCheckbox>
                          <NSelect
                            v-model:value="(formData[SPECIAL_FIELD] as MedicalSituationConfig).labTests.sortOrder"
                            :options="sortOrderOptions"
                            :disabled="!(formData[SPECIAL_FIELD] as MedicalSituationConfig).labTests.includeTime"
                            style="width: 80px"
                          />
                        </div>
                      </div>
                    </fieldset>

                    <!-- 检查信息配置区 -->
                    <fieldset class="config-fieldset">
                      <legend class="config-legend">
                        <NCheckbox
                          v-model:checked="medicalCheckboxState.examinationsEnabled"
                        >
                          检查信息 (Examinations)
                        </NCheckbox>
                      </legend>
                      <div v-if="medicalCheckboxState.examinationsEnabled" class="controls-row">
                        <!-- 时间筛选 -->
                        <div class="control-group">
                          <label>时间:</label>
                          <NSelect
                            v-model:value="(formData[SPECIAL_FIELD] as MedicalSituationConfig).examinations.timeFilterType"
                            :options="timeFilterOptions"
                            style="width: 120px"
                          />

                          <!-- 条件性显示的时间输入 -->
                          <div v-if="(formData[SPECIAL_FIELD] as MedicalSituationConfig).examinations.timeFilterType === 'recent_days'" class="time-extra-input">
                            <NInputNumber
                              v-model:value="(formData[SPECIAL_FIELD] as MedicalSituationConfig).examinations.recentDays"
                              :min="1"
                              :max="365"
                              style="width: 80px"
                            />
                            <span>天内</span>
                          </div>

                          <div v-if="(formData[SPECIAL_FIELD] as MedicalSituationConfig).examinations.timeFilterType === 'date_range'" class="time-extra-input">
                            <NDatePicker
                              v-model:value="(formData[SPECIAL_FIELD] as MedicalSituationConfig).examinations.startDate"
                              type="date"
                              placeholder="开始日期"
                              style="width: 140px"
                            />
                            <span>-</span>
                            <NDatePicker
                              v-model:value="(formData[SPECIAL_FIELD] as MedicalSituationConfig).examinations.endDate"
                              type="date"
                              placeholder="结束日期"
                              style="width: 140px"
                            />
                          </div>
                        </div>

                        <!-- 关键词输入框 -->
                        <div class="control-group">
                          <label>关键词:</label>
                          <NInput
                            v-model:value="examinationsKeywordsInput"
                            style="width: 400px"
                            placeholder="输入关键词，用空格分隔"
                            @blur="updateExaminationsKeywords"
                          />
                        </div>

                        <!-- 输出格式控制 -->
                        <div class="output-controls">
                          <NCheckbox
                            v-model:checked="(formData[SPECIAL_FIELD] as MedicalSituationConfig).examinations.includeTime"
                          >
                            包含时间
                          </NCheckbox>
                          <NSelect
                            v-model:value="(formData[SPECIAL_FIELD] as MedicalSituationConfig).examinations.sortOrder"
                            :options="sortOrderOptions"
                            :disabled="!(formData[SPECIAL_FIELD] as MedicalSituationConfig).examinations.includeTime"
                            style="width: 80px"
                          />
                        </div>
                      </div>
                    </fieldset>
                  </div>
                </template>

                <template v-else>
                  <NDynamicInput v-model:value="formData[prompt_index] as FormDataItem[]" :on-create="onCreate" show-sort-button>
                    <template #default="{ value, index }">
                      <div style="display: flex; align-items: center; width: 100%; gap: 8px; flex-wrap: nowrap">
                        <span style="flex-shrink: 0; font-weight: 600; color: #1890ff; min-width: 120px;">第{{ index + 1 }}条逻辑规则:</span>
                        <NSelect
                          v-model:value="value.label"
                          :options="tagOptions"
                          style="width: 100px; flex-shrink: 0"
                          class="select"
                        />

                        <!-- 抽取类型 -->
                        <template v-if="value.label === '抽取'">
                          <span style="flex-shrink: 0">从</span>
                          <NSelect
                            v-model:value="value.sourceRecords"
                            :options="getSourceOptions(prompt_index, index)"
                            multiple
                            filterable
                            tag
                            style="min-width: 200px; flex: 1; width: 200px"
                            :render-tag="renderMultipleTag"
                            placeholder="选择来源文书"
                          />
                          <span style="flex-shrink: 0">抽取</span>
                          <NInput
                            v-model:value="value.fieldNames"
                            type="text"
                            style="min-width: 200px; flex: 1; width: 200px"
                            placeholder="输入字段"
                          />
                        </template>

                        <!-- 推理类型 -->
                        <template v-else-if="value.label === '推理'">
                          <span style="flex-shrink: 0">根据</span>
                          <NSelect
                            v-model:value="value.sourceRecords"
                            :options="getSourceOptions(prompt_index, index)"
                            multiple
                            filterable
                            tag
                            style="min-width: 200px; flex: 1; width: 200px"
                            :render-tag="renderMultipleTag"
                            placeholder="选择依据"
                          />
                          <span style="flex-shrink: 0">推理</span>
                          <NInput
                            v-model:value="value.fieldNames"
                            type="text"
                            style="min-width: 200px; flex: 1; width: 200px"
                            placeholder="输入推理内容"
                          />
                        </template>

                        <!-- 摘要类型 -->
                        <template v-else-if="value.label === '摘要'">
                          <span style="flex-shrink: 0">从</span>
                          <NSelect
                            v-model:value="value.sourceRecords"
                            :options="getSourceOptions(prompt_index, index)"
                            multiple
                            filterable
                            tag
                            style="min-width: 200px; flex: 1; width: 200px"
                            :render-tag="renderMultipleTag"
                            placeholder="选择来源"
                          />
                          <span style="flex-shrink: 0">摘要</span>
                          <NInput
                            v-model:value="value.fieldNames"
                            type="text"
                            style="min-width: 200px; flex: 1; width: 200px"
                            placeholder="输入摘要要点"
                          />
                        </template>

                        <!-- 判断类型 -->
                        <template v-else-if="value.label === '判断'">
                          <span style="flex-shrink: 0">基于</span>
                          <NSelect
                            v-model:value="value.sourceRecords"
                            :options="getSourceOptions(prompt_index, index)"
                            multiple
                            filterable
                            tag
                            style="min-width: 200px; flex: 1; width: 200px"
                            :render-tag="renderMultipleTag"
                            placeholder="选择判断依据"
                          />
                          <span style="flex-shrink: 0">判断</span>
                          <NInput
                            v-model:value="value.fieldNames"
                            type="text"
                            style="min-width: 200px; flex: 1; width: 200px"
                            placeholder="输入判断结果"
                          />
                        </template>

                        <!-- 知识类型 -->
                        <template v-else-if="value.label === '知识'">
                          <span style="flex-shrink: 0">匹配</span>
                          <NSelect
                            v-model:value="value.sourceRecords"
                            :options="getSourceOptions(prompt_index, index)"
                            multiple
                            filterable
                            tag
                            style="min-width: 200px; flex: 1; width: 200px"
                            :render-tag="renderMultipleTag"
                            placeholder="选择匹配内容"
                          />
                          <span style="flex-shrink: 0">知识库</span>
                          <NInput
                            v-model:value="value.fieldNames"
                            type="text"
                            style="min-width: 200px; flex: 1; width: 200px"
                            placeholder="输入知识条目"
                          />
                        </template>

                        <!-- 最终生成的value -->
                        <NInput
                          v-model:value="value.value"
                          type="text"
                          style="flex: 1; min-width: 200px; width: 200px"
                          :placeholder="`请完成${value.label}配置`"
                          readonly
                        />
                      </div>
                    </template>
                  </NDynamicInput>
                </template>
              </NFormItem>
              <!-- 为非特殊字段添加总结指南输入框 -->
              <NFormItem
                v-if="prompt_index !== SPECIAL_FIELD"
                label="总结指南："
                class="summary-guidance-form-item"
              >
                <NInput
                  v-model:value="summaryGuidance[prompt_index]"
                  type="textarea"
                  :placeholder="`${prompt_index}总结指南`"
                  :autosize="{ minRows: 2, maxRows: 4 }"
                />
              </NFormItem>
              <NFormItem>
                <NCollapse>
                  <NCollapseItem title="关键字名称">
                    <NCollapse>
                      <NCollapseItem
                        v-for="(items, actionType) in section_keywords[prompt_index]"
                        :key="actionType"
                        :title="actionType"
                      >
                        <NTag
                          v-for="(item, index) in items"
                          :key="index"
                          type="info"
                          style="margin-right: 8px; margin-bottom: 8px"
                        >
                          {{ item }}
                        </NTag>
                      </NCollapseItem>
                    </NCollapse>
                  </NCollapseItem>
                </NCollapse>
              </NFormItem>
              <NFormItem>
                <NCollapse>
                  <NCollapseItem title="详细来源内容:">
                    <div v-for="(value, key) in section_contents[prompt_index]" :key="key">
                      <strong>{{ key }}:</strong>
                      <div style="white-space: pre-line">{{ value }}</div>
                    </div>
                  </NCollapseItem>
                </NCollapse>
              </NFormItem>
            </NForm>
          </NCard>
        </NGi>
      </NGrid>
    </NSpace>
  </div>
  <NModal v-model:show="showModal" title="Modify Field Points" preset="card" style="max-width: 600px">
    <NInput v-model:value="editingContent" type="textarea" rows="6" />
    <template #footer>
      <div style="display: flex; justify-content: flex-end">
        <NButton type="primary" style="margin-right: 16px" @click="saveEdit">
          {{ $t('page.task.submit') }}
        </NButton>
        <NButton @click="showModal = false">
          {{ $t('page.task.cancel') }}
        </NButton>
      </div>
    </template>
  </NModal>
</template>

<style scoped>
.card-wrapper {
  margin-bottom: 16px;
}

.select {
  margin-right: 10px;
}

.medical-config-container {
  width: 100%;
  padding: 16px;
  background-color: #f8f9fa;
  border-radius: 8px;
}

.config-fieldset {
  border: 1px solid #d1d5db;
  border-radius: 6px;
  padding: 16px;
  margin-bottom: 20px;
  background-color: white;
}

.config-legend {
  font-size: 1.1em;
  font-weight: 600;
  padding: 0 10px;
  color: #374151;
  display: flex;
  align-items: center;
}

.controls-row {
  display: flex;
  align-items: center;
  gap: 16px;
  flex-wrap: wrap;
  padding-top: 12px;
}

.control-group {
  display: flex;
  align-items: center;
  gap: 8px;
  white-space: nowrap;
}

.time-extra-input {
  display: flex;
  align-items: center;
  gap: 6px;
  white-space: nowrap;
}

.output-controls {
  display: flex;
  align-items: center;
  gap: 8px;
}

label {
  font-weight: 500;
  color: #374151;
}

::v-deep(.n-form-item-feedback-wrapper) {
  --n-feedback-height: 0px;
}

::v-deep(.n-form-item.n-form-item--top-labelled) {
  grid-template-rows: unset;
}

::v-deep(.n-card .n-card-header .n-card-header__main) {
  font-weight: 1000;
}

.padding-top {
  padding-top: 12px;
}

.tag {
  font-size: 12px;
  border-radius: 0;
  margin-right: 6px;
}

.action_select_item {
  min-width: 200px;
  flex: 1;
  width: 200px;
}



.summary-guidance-form-item {
  margin-top: 24px;
  margin-bottom: 20px;
}

.summary-guidance-form-item ::v-deep(.n-form-item-label) {
  font-size: 1.2em !important;
  font-weight: 600 !important;
  color: #2563eb !important;
  margin-bottom: 12px !important;
  padding-bottom: 8px !important;
}
</style>
