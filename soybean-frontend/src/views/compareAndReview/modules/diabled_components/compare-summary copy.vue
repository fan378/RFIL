<script setup lang="ts">
import { computed, defineComponent, defineProps, h, nextTick, reactive, ref } from 'vue';
import { NIcon, NInput, useThemeVars } from 'naive-ui';
import { BookOutline as BookIcon } from '@vicons/ionicons5';
import { $t } from '@/locales';
import { useTaskStore } from '@/store/modules/task';
import { useAppStore } from '@/store/modules/app';

defineOptions({
  name: 'CompareSummary'
});
const appStore = useAppStore();
const gap = computed(() => (appStore.isMobile ? 0 : 16));
const taskStore = useTaskStore();

const displaying = ref(1);
const prev = () => {
  if (displaying.value > 1) {
    displaying.value -= 1;
  }
};
const next = () => {
  if (displaying.value < 4) {
    displaying.value += 1;
  }
};

const props = defineProps<{ isEditing: boolean }>();
const patient = taskStore.processedJson.patient;
const patient_original = reactive(taskStore.processedJson.patient_original);
const doctor = reactive(taskStore.processedJson.doctor);
const highlightText = id => {
  const elements = document.querySelectorAll(`#${id}`);
  elements.forEach(element => {
    element.classList.add('highlight');
  });
};
const removeHighlight = id => {
  const elements = document.querySelectorAll(`#${id}`);
  elements.forEach(element => {
    element.classList.remove('highlight');
  });
};
const showSource = id => {
  console.log(id);
};

// 检验检查
const highlightedItems = ref([]);
const extractTestName = item => {
  return item.split('：')[1]?.split(/\d/)[0].trim() || item.split(/\d/)[0].trim();
};
const highlightMatching = item => {
  console.log(item);
  const testName = extractTestName(item);
  highlightedItems.value = patient['住院期间医疗情况'].filter(modelItem => extractTestName(modelItem) === testName);
  highlightedItems.value = doctor['住院期间医疗情况'].filter(modelItem => extractTestName(modelItem) === testName);
};
const clearHighlight = () => {
  highlightedItems.value = [];
};

// 来源材料：
const source = reactive(taskStore.processedJson.source);
const menuOptions = reactive({
  患者基本信息: [
    {
      label: '全部诊断',
      key: '全部诊断'
    },
    {
      label: '新入院评估单',
      key: '新入院评估单'
    },
    {
      label: '乳腺中心入院记录',
      key: '乳腺中心入院记录'
    },
    {
      label: '入院告知书',
      key: '入院告知书'
    },
    {
      label: '24小时内入出院记录',
      key: '24小时内入出院记录'
    }
  ]
});

const collapsed = ref(false);
const selectedKey = ref('全部诊断');
const renderMenuLabel = (option: MenuOption) => {
  if ('href' in option) {
    return h('a', { href: option.href, target: '_blank' }, option.label as string);
  }
  return option.label as string;
};
const renderMenuIcon = (option: MenuOption) => {
  // 渲染图标占位符以保持缩进
  if (option.key === 'sheep-man') return true;
  // 返回 falsy 值，不再渲染图标及占位符
  if (option.key === 'food') return null;
  return h(NIcon, null, { default: () => h(BookIcon) });
};
const expandIcon = () => {
  return h(NIcon, null, { default: () => h(CaretDownOutline) });
};
// 监听菜单点击
const handleMenuSelect = key => {
  selectedKey.value = key;
};
const patterns = ref(['诊断名称:乳房肿块']);
const themeVars = useThemeVars();
</script>

<template>
  <NGrid :x-gap="gap" :y-gap="16" responsive="screen" item-responsive>
    <NGi span="24 s:24 m:12" style="display: flex">
      <NCard
        size="small"
        :bordered="false"
        title="LLM Discharge Summary"
        header-class="text-14px"
        header-style="padding: 6px var(--n-padding-left); text-align: center; font-weight: 600; position: sticky; top: 0; background: white; z-index: 10;"
        footer-style="padding: 0 6px 6px 6px;position: sticky; bottom: -1px; background: white; z-index: 10;"
        content-style="padding: 0 6px 0 6px;position: sticky;"
        style="flex: 1; display: flex; flex-direction: column; max-height: 45vh; min-height: 40vh; overflow: auto"
      >
        <div style="flex: 1; overflow: auto">
          <table
            v-if="displaying == 1"
            style="table-layout: fixed; width: 100%; border: 2px solid rgb(238, 239, 241, 0.5)"
          >
            <colgroup>
              <col style="width: 16%" />
              <col style="width: 18%" />
              <col style="width: 12%" />
              <col style="width: 18%" />
              <col style="width: 15%" />
              <col style="width: 20%" />
            </colgroup>
            <tr>
              <td>Name:</td>
              <td>
                <NInput
                  v-if="isEditing"
                  v-model:value="patient_original.患者基本信息.姓名"
                  type="textarea"
                  autosize="{ minRows: 1, maxRows: 10 }"
                  style="height: auto"
                />
                <span v-else>
                  <span
                    id="姓名"
                    @mouseover="highlightText('姓名')"
                    @mouseout="removeHighlight('姓名')"
                    @click="showSource('姓名')"
                  >
                    {{ patient.患者基本信息.姓名 }}
                  </span>
                </span>
              </td>
              <td>Age:</td>
              <td>
                <NInput
                  v-if="isEditing"
                  v-model:value="patient_original.患者基本信息.年龄"
                  type="textarea"
                  autosize="{ minRows: 1, maxRows: 10 }"
                  style="height: auto"
                />
                <span v-else>
                  <span
                    id="年龄"
                    @mouseover="highlightText('年龄')"
                    @mouseout="removeHighlight('年龄')"
                    @click="showSource('年龄')"
                  >
                    {{ patient.患者基本信息.年龄 }}
                  </span>
                </span>
              </td>
              <td>Gender:</td>
              <td>
                <NInput
                  v-if="isEditing"
                  v-model:value="patient_original.患者基本信息.性别"
                  type="textarea"
                  autosize="{ minRows: 1, maxRows: 10 }"
                  style="height: auto"
                />
                <span v-else>
                  <span
                    id="性别"
                    @mouseover="highlightText('性别')"
                    @mouseout="removeHighlight('性别')"
                    @click="showSource('性别')"
                  >
                    {{ patient.患者基本信息.性别 }}
                  </span>
                </span>
              </td>
            </tr>
            <tr>
              <td>Hospital No:</td>
              <td>
                <NInput
                  v-if="isEditing"
                  v-model:value="patient_original.患者基本信息.住院号"
                  type="textarea"
                  autosize="{ minRows: 1, maxRows: 10 }"
                  style="height: auto"
                />
                <span v-else>
                  <span
                    id="住院号"
                    @mouseover="highlightText('住院号')"
                    @mouseout="removeHighlight('住院号')"
                    @click="showSource('住院号')"
                  >
                    {{ patient.患者基本信息.住院号 }}
                  </span>
                </span>
              </td>
              <td>Bed No:</td>
              <td>
                <NInput
                  v-if="isEditing"
                  v-model:value="patient_original.患者基本信息.床号"
                  type="textarea"
                  autosize="{ minRows: 1, maxRows: 10 }"
                  style="height: auto"
                />
                <span v-else>
                  <span
                    id="Age"
                    @mouseover="highlightText('Age')"
                    @mouseout="removeHighlight('Age')"
                    @click="showSource('Age')"
                  >
                    {{ patient.患者基本信息.床号 }}
                  </span>
                </span>
              </td>
              <td></td>
              <td></td>
            </tr>
            <tr>
              <td>Department:</td>
              <td colspan="5">
                <NInput
                  v-if="isEditing"
                  v-model:value="patient_original.患者基本信息.科室"
                  type="textarea"
                  autosize="{ minRows: 1, maxRows: 10 }"
                  style="height: auto"
                />
                <span v-else>
                  <span
                    id="科室"
                    @mouseover="highlightText('科室')"
                    @mouseout="removeHighlight('科室')"
                    @click="showSource('科室')"
                  >
                    {{ patient.患者基本信息.科室 }}
                  </span>
                </span>
              </td>
            </tr>
            <tr>
              <td>In Time:</td>
              <td colspan="2">
                <NInput
                  v-if="isEditing"
                  v-model:value="patient_original.患者基本信息.入院时间"
                  type="textarea"
                  autosize="{ minRows: 1, maxRows: 10 }"
                  style="height: auto"
                />
                <span v-else>
                  <span
                    id="入院时间"
                    @mouseover="highlightText('入院时间')"
                    @mouseout="removeHighlight('入院时间')"
                    @click="showSource('入院时间')"
                  >
                    {{ patient.患者基本信息.入院时间 }}
                  </span>
                </span>
              </td>
              <td>Out Time:</td>
              <td colspan="2">
                <NInput
                  v-if="isEditing"
                  v-model:value="patient_original.患者基本信息.出院时间"
                  type="textarea"
                  autosize="{ minRows: 1, maxRows: 10 }"
                  style="height: auto"
                />
                <span v-else>
                  <span
                    id="出院时间"
                    @mouseover="highlightText('出院时间')"
                    @mouseout="removeHighlight('出院时间')"
                    @click="showSource('出院时间')"
                  >
                    {{ patient.患者基本信息.出院时间 }}
                  </span>
                </span>
              </td>
            </tr>
            <tr>
              <td>Cause:</td>
              <td colspan="5">
                <NInput
                  v-if="isEditing"
                  v-model:value="patient_original.患者基本信息.入院诊断"
                  type="textarea"
                  autosize="{ minRows: 1, maxRows: 10 }"
                  style="height: auto"
                />
                <span v-else>
                  <span
                    id="入院诊断"
                    @mouseover="highlightText('入院诊断')"
                    @mouseout="removeHighlight('入院诊断')"
                    @click="showSource('入院诊断')"
                  >
                    {{ patient.患者基本信息.入院诊断 }}
                  </span>
                </span>
              </td>
            </tr>
            <tr>
              <td style="vertical-align: top">Diagnosis:</td>
              <td colspan="5">
                <NInput
                  v-if="isEditing"
                  v-model:value="patient_original.出院诊断"
                  type="textarea"
                  autosize="{ minRows: 1, maxRows: 10 }"
                  style="height: auto"
                />
                <span v-else>
                  <span
                    id="出院诊断"
                    @mouseover="highlightText('出院诊断')"
                    @mouseout="removeHighlight('出院诊断')"
                    @click="showSource('出院诊断')"
                  >
                    {{ patient.出院诊断 }}
                  </span>
                </span>
              </td>
            </tr>
            <tr>
              <td colspan="6">Physical Examination:</td>
            </tr>
            <tr>
              <td colspan="6" style="vertical-align: top; font-weight: normal">
                <span class="hang-indent">
                  <NInput
                    v-if="isEditing"
                    v-model:value="patient_original.患者基本信息.体检摘要"
                    type="textarea"
                    autosize="{ minRows: 1, maxRows: 10 }"
                    style="height: auto"
                  />
                  <span v-else>
                    <span
                      v-for="(item, index) in patient.患者基本信息.体检摘要"
                      :id="`体检摘要-${index}`"
                      :key="`体检摘要-${index}`"
                      @mouseover="highlightText(`体检摘要-${index}`)"
                      @mouseout="removeHighlight(`体检摘要-${index}`)"
                      @click="showSource(`体检摘要-${index}`)"
                    >
                      {{ item }}
                    </span>
                  </span>
                </span>
              </td>
            </tr>
          </table>
          <table
            v-if="displaying == 2"
            style="table-layout: fixed; width: 100%; border: 2px solid rgb(238, 239, 241, 0.5)"
          >
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

            <tr>
              <td colspan="8" style="vertical-align: top">Brief History:</td>
            </tr>
            <tr>
              <td style="vertical-align: middle">T:</td>
              <td>
                <NInput
                  v-if="isEditing"
                  v-model:value="patient_original['患者基本信息']['体温(T)']"
                  type="textarea"
                  autosize="{ minRows: 1, maxRows: 10 }"
                  style="height: auto; width: auto"
                />
                <span v-else>
                  <span
                    id="体温"
                    @mouseover="highlightText('体温')"
                    @mouseout="removeHighlight('体温')"
                    @click="showSource('体温')"
                  >
                    {{ patient['患者基本信息']['体温(T)'] }}
                  </span>
                </span>
                ℃
              </td>
              <td>P:</td>
              <td>
                <NInput
                  v-if="isEditing"
                  v-model:value="patient_original['患者基本信息']['脉搏(P)']"
                  type="textarea"
                  autosize="{ minRows: 1, maxRows: 10 }"
                  style="height: auto; width: auto"
                />
                <span v-else>
                  <span
                    id="脉搏"
                    @mouseover="highlightText('脉搏')"
                    @mouseout="removeHighlight('脉搏')"
                    @click="showSource('脉搏')"
                  >
                    {{ patient['患者基本信息']['脉搏(P)'] }}
                  </span>
                </span>
                bpm
              </td>
              <td>R:</td>
              <td>
                <NInput
                  v-if="isEditing"
                  v-model:value="patient_original['患者基本信息']['呼吸(R)']"
                  type="textarea"
                  autosize="{ minRows: 1, maxRows: 10 }"
                  style="height: auto; width: auto"
                />
                <span v-else>
                  <span
                    id="呼吸"
                    @mouseover="highlightText('呼吸')"
                    @mouseout="removeHighlight('呼吸')"
                    @click="showSource('呼吸')"
                  >
                    {{ patient['患者基本信息']['呼吸(R)'] }}
                  </span>
                </span>
                bpm
              </td>
              <td>BP:</td>
              <td>
                <NInput
                  v-if="isEditing"
                  v-model:value="patient_original['患者基本信息']['高压(BP高)']"
                  type="textarea"
                  autosize="{ minRows: 1, maxRows: 10 }"
                  style="height: auto; width: auto"
                />
                <span v-else>
                  <span
                    id="高压"
                    @mouseover="highlightText('高压')"
                    @mouseout="removeHighlight('高压')"
                    @click="showSource('高压')"
                  >
                    {{ patient['患者基本信息']['高压(BP高)'] }}
                  </span>
                </span>
                /
                <NInput
                  v-if="isEditing"
                  v-model:value="patient_original['患者基本信息']['低压(BP低)']"
                  type="textarea"
                  autosize="{ minRows: 1, maxRows: 10 }"
                  style="height: auto; width: auto"
                />
                <span v-else>
                  <span
                    id="低压"
                    @mouseover="highlightText('低压')"
                    @mouseout="removeHighlight('低压')"
                    @click="showSource('低压')"
                  >
                    {{ patient['患者基本信息']['低压(BP低)'] }}
                  </span>
                </span>
                mmHg
              </td>
            </tr>
            <tr></tr>
            <tr>
              <td colspan="8" style="vertical-align: top; font-weight: normal">
                <span class="hang-indent">
                  <NInput
                    v-if="isEditing"
                    v-model:value="patient_original['患者基本信息']['入院时简要病史']"
                    type="textarea"
                    autosize="{ minRows: 1, maxRows: 10 }"
                    style="height: auto"
                  />
                  <span v-else>
                    <span
                      v-for="(item, index) in patient.患者基本信息.入院时简要病史"
                      :id="`入院时简要病史-${index}`"
                      :key="`入院时简要病史-${index}`"
                      @mouseover="highlightText(`入院时简要病史-${index}`)"
                      @mouseout="removeHighlight(`入院时简要病史-${index}`)"
                      @click="showSource(`入院时简要病史-${index}`)"
                    >
                      {{ item }}
                    </span>
                  </span>
                </span>
              </td>
            </tr>
          </table>
          <table
            v-if="displaying == 3"
            style="table-layout: fixed; width: 100%; border: 2px solid rgb(238, 239, 241, 0.5)"
          >
            <colgroup>
              <col style="width: 7%" />
              <col style="width: 18%" />
              <col style="width: 7%" />
              <col style="width: 18%" />
              <col style="width: 7%" />
              <col style="width: 18%" />
              <col style="width: 7%" />
              <col style="width: 18%" />
            </colgroup>

            <tr>
              <td colspan="8" style="vertical-align: top">Main Test And Examination Results During Hospitalization:</td>
            </tr>
            <tr>
              <td colspan="8" style="vertical-align: top; font-weight: normal">
                <NInput
                  v-if="isEditing"
                  v-model:value="patient_original['住院期间医疗情况']"
                  type="textarea"
                  autosize="{ minRows: 1, maxRows: 10 }"
                  style="height: auto"
                />
                <span v-else>
                  <span
                    v-for="(item, index) in patient['住院期间医疗情况']"
                    :id="`住院期间医疗情况-${index}`"
                    :key="item"
                    @mouseover="highlightMatching(item)"
                    @mouseout="clearHighlight"
                    @click="showSource(`住院期间医疗情况-${index}`)"
                  >
                    {{ item }}
                  </span>
                </span>
              </td>
            </tr>
          </table>
          <table
            v-if="displaying == 4"
            style="table-layout: fixed; width: 100%; border: 2px solid rgb(238, 239, 241, 0.5)"
          >
            <colgroup>
              <col style="width: 7%" />
              <col style="width: 18%" />
              <col style="width: 7%" />
              <col style="width: 18%" />
              <col style="width: 7%" />
              <col style="width: 18%" />
              <col style="width: 7%" />
              <col style="width: 18%" />
            </colgroup>

            <tr>
              <td colspan="8" style="vertical-align: top">Course And Treatment:</td>
            </tr>
            <tr>
              <td colspan="8" style="vertical-align: top; font-weight: normal">
                <NInput
                  v-if="isEditing"
                  v-model:value="patient_original['病程与治疗情况']"
                  type="textarea"
                  autosize="{ minRows: 1, maxRows: 10 }"
                  style="height: auto"
                />
                <span v-else>
                  <span
                    v-for="(item, index) in patient['病程与治疗情况']"
                    :id="`病程与治疗情况-${index}`"
                    :key="`病程与治疗情况-${index}`"
                    @mouseover="highlightText(`病程与治疗情况-${index}`)"
                    @mouseout="removeHighlight(`病程与治疗情况-${index}`)"
                    @click="showSource(`病程与治疗情况-${index}`)"
                  >
                    {{ item }}
                  </span>
                </span>
              </td>
            </tr>
            <tr>
              <td colspan="8" style="vertical-align: top">Condition at Discharge:</td>
            </tr>
            <tr>
              <td colspan="8" style="vertical-align: top; font-weight: normal">
                <NInput
                  v-if="isEditing"
                  v-model:value="patient_original['出院时情况']"
                  type="textarea"
                  autosize="{ minRows: 1, maxRows: 10 }"
                  style="height: auto"
                />
                <span v-else>
                  <span
                    v-for="(item, index) in patient['出院时情况']"
                    :id="`出院时情况-${index}`"
                    :key="`出院时情况-${index}`"
                    @mouseover="highlightText(`出院时情况-${index}`)"
                    @mouseout="removeHighlight(`出院时情况-${index}`)"
                    @click="showSource(`出院时情况-${index}`)"
                  >
                    {{ item }}
                  </span>
                </span>
              </td>
            </tr>
            <tr>
              <td colspan="8" style="vertical-align: top">Medication Recommendations After Discharge:</td>
            </tr>
            <tr>
              <td colspan="8" style="vertical-align: top; font-weight: normal">
                <NInput
                  v-if="isEditing"
                  v-model:value="patient_original['出院后用药建议']"
                  type="textarea"
                  autosize="{ minRows: 1, maxRows: 10 }"
                  style="height: auto"
                />
                <span v-else>
                  <span
                    v-for="(item, index) in patient['出院后用药建议']"
                    :id="`出院后用药建议-${index}`"
                    :key="`出院后用药建议-${index}`"
                    @mouseover="highlightText(`出院后用药建议-${index}`)"
                    @mouseout="removeHighlight(`出院后用药建议-${index}`)"
                    @click="showSource(`出院后用药建议-${index}`)"
                  >
                    {{ item }}
                  </span>
                </span>
              </td>
            </tr>
          </table>
        </div>
        <template #footer>
          <NSpace style="width: 100%; justify-content: right; padding-top: 6px; padding-bottom: 0">
            <NButton size="small" @click="prev"><</NButton>
            <NButton size="small" @click="next">></NButton>
          </NSpace>
        </template>
      </NCard>
    </NGi>
    <NGi span="24 s:24 m:12" style="display: flex">
      <NCard
        size="small"
        :bordered="false"
        title="Doctor Discharge Summary"
        header-class="text-14px"
        header-style="padding: 6px var(--n-padding-left); text-align: center; font-weight: 600; position: sticky; top: 0; background: white; z-index: 10;"
        footer-style="padding: 0 6px 6px 6px;position: sticky; bottom: -1px; background: white; z-index: 10;"
        content-style="padding: 0 6px 0 6px;position: sticky;"
        style="overflow: auto; flex: 1; max-height: 45vh; min-height: 40vh; display: flex; flex-direction: column"
      >
        <div style="flex: 1; overflow: auto">
          <table
            v-if="displaying == 1"
            style="table-layout: fixed; width: 100%; border: 1px solid rgb(238, 239, 241, 0.5)"
          >
            <colgroup>
              <col style="width: 16%" />
              <col style="width: 18%" />
              <col style="width: 12%" />
              <col style="width: 18%" />
              <col style="width: 15%" />
              <col style="width: 20%" />
            </colgroup>
            <tr>
              <td>Name:</td>
              <td>
                <span id="姓名" @mouseover="highlightText('姓名')" @mouseout="removeHighlight('姓名')">
                  {{ doctor.患者基本信息.姓名 }}
                </span>
              </td>
              <td>Age:</td>
              <td>
                <span id="年龄" @mouseover="highlightText('年龄')" @mouseout="removeHighlight('年龄')">
                  {{ doctor.患者基本信息.年龄 }}
                </span>
              </td>
              <td>Gender:</td>
              <td>
                <span id="性别" @mouseover="highlightText('性别')" @mouseout="removeHighlight('性别')">
                  {{ doctor.患者基本信息.性别 }}
                </span>
              </td>
            </tr>
            <tr>
              <td>Hospital No:</td>
              <td>
                <span id="住院号" @mouseover="highlightText('住院号')" @mouseout="removeHighlight('住院号')">
                  {{ doctor.患者基本信息.住院号 }}
                </span>
              </td>
              <td>Bed No:</td>
              <td>
                <span id="Age" @mouseover="highlightText('Age')" @mouseout="removeHighlight('Age')">
                  {{ doctor.患者基本信息.床号 }}
                </span>
              </td>
              <td></td>
              <td></td>
            </tr>
            <tr>
              <td>Department:</td>
              <td colspan="5">
                <span id="科室" @mouseover="highlightText('科室')" @mouseout="removeHighlight('科室')">
                  {{ doctor.患者基本信息.科室 }}
                </span>
              </td>
            </tr>
            <tr>
              <td>In Time:</td>
              <td colspan="2">
                <span id="入院时间" @mouseover="highlightText('入院时间')" @mouseout="removeHighlight('入院时间')">
                  {{ doctor.患者基本信息.入院时间 }}
                </span>
              </td>
              <td>Out Time:</td>
              <td colspan="2">
                <span id="出院时间" @mouseover="highlightText('出院时间')" @mouseout="removeHighlight('出院时间')">
                  {{ doctor.患者基本信息.出院时间 }}
                </span>
              </td>
            </tr>
            <tr>
              <td>Cause:</td>
              <td colspan="5">
                <span id="入院诊断" @mouseover="highlightText('入院诊断')" @mouseout="removeHighlight('入院诊断')">
                  {{ doctor.患者基本信息.入院诊断 }}
                </span>
              </td>
            </tr>
            <tr>
              <td style="vertical-align: top">Diagnosis:</td>
              <td colspan="5">
                <span id="出院诊断" @mouseover="highlightText('出院诊断')" @mouseout="removeHighlight('出院诊断')">
                  {{ doctor.出院诊断 }}
                </span>
              </td>
            </tr>
            <tr>
              <td colspan="6">Physical Examination:</td>
            </tr>
            <tr>
              <td colspan="6" style="vertical-align: top; font-weight: normal">
                <span class="hang-indent">
                  <span
                    v-for="(item, index) in doctor.患者基本信息.体检摘要"
                    :id="`体检摘要-${index}`"
                    :key="`体检摘要-${index}`"
                    @mouseover="highlightText(`体检摘要-${index}`)"
                    @mouseout="removeHighlight(`体检摘要-${index}`)"
                    @click="showSource(`体检摘要-${index}`)"
                  >
                    {{ item }}
                  </span>
                </span>
              </td>
            </tr>
          </table>
          <table
            v-if="displaying == 2"
            style="table-layout: fixed; width: 100%; border: 2px solid rgb(238, 239, 241, 0.5)"
          >
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

            <tr>
              <td colspan="8" style="vertical-align: top">Brief History:</td>
            </tr>
            <tr>
              <td style="vertical-align: middle">T:</td>
              <td>
                <span id="体温" @mouseover="highlightText('体温')" @mouseout="removeHighlight('体温')">
                  {{ doctor['患者基本信息']['体温(T)'] }}
                </span>
                ℃
              </td>
              <td>P:</td>
              <td>
                <span id="脉搏" @mouseover="highlightText('脉搏')" @mouseout="removeHighlight('脉搏')">
                  {{ doctor['患者基本信息']['脉搏(P)'] }}
                </span>
                bpm
              </td>
              <td>R:</td>
              <td>
                <span id="呼吸" @mouseover="highlightText('呼吸')" @mouseout="removeHighlight('呼吸')">
                  {{ doctor['患者基本信息']['呼吸(R)'] }}
                </span>
                bpm
              </td>
              <td>BP:</td>
              <td>
                <span id="高压" @mouseover="highlightText('高压')" @mouseout="removeHighlight('高压')">
                  {{ doctor['患者基本信息']['高压(BP高)'] }}
                </span>
                /

                <span id="低压" @mouseover="highlightText('低压')" @mouseout="removeHighlight('低压')">
                  {{ doctor['患者基本信息']['低压(BP低)'] }}
                </span>
                mmHg
              </td>
            </tr>
            <tr></tr>
            <tr>
              <td colspan="8" style="vertical-align: top; font-weight: normal">
                <span class="hang-indent">
                  <span
                    v-for="(item, index) in doctor['患者基本信息']['入院时简要病史']"
                    :id="`入院时简要病史-${index}`"
                    :key="`入院时简要病史-${index}`"
                    @mouseover="highlightText(`入院时简要病史-${index}`)"
                    @mouseout="removeHighlight(`入院时简要病史-${index}`)"
                    @click="showSource(`入院时简要病史-${index}`)"
                  >
                    {{ item }}
                  </span>
                </span>
              </td>
            </tr>
          </table>
          <table
            v-if="displaying == 3"
            style="table-layout: fixed; width: 100%; border: 2px solid rgb(238, 239, 241, 0.5)"
          >
            <colgroup>
              <col style="width: 7%" />
              <col style="width: 18%" />
              <col style="width: 7%" />
              <col style="width: 18%" />
              <col style="width: 7%" />
              <col style="width: 18%" />
              <col style="width: 7%" />
              <col style="width: 18%" />
            </colgroup>

            <tr>
              <td colspan="8" style="vertical-align: top">Main Test And Examination Results During Hospitalization:</td>
            </tr>
            <tr>
              <td colspan="8" style="vertical-align: top; font-weight: normal">
                <span
                  v-for="(item, index) in doctor['住院期间医疗情况']"
                  :id="`住院期间医疗情况-${index}`"
                  :key="item"
                  @mouseover="highlightMatching(item)"
                  @mouseout="clearHighlight"
                  @click="showSource(`住院期间医疗情况-${index}`)"
                >
                  {{ item }}
                  <!-- <br /> -->
                </span>
              </td>
            </tr>
          </table>
          <table
            v-if="displaying == 4"
            style="table-layout: fixed; width: 100%; border: 2px solid rgb(238, 239, 241, 0.5)"
          >
            <colgroup>
              <col style="width: 7%" />
              <col style="width: 18%" />
              <col style="width: 7%" />
              <col style="width: 18%" />
              <col style="width: 7%" />
              <col style="width: 18%" />
              <col style="width: 7%" />
              <col style="width: 18%" />
            </colgroup>

            <tr>
              <td colspan="8" style="vertical-align: top">Course And Treatment:</td>
            </tr>
            <tr>
              <td colspan="8" style="vertical-align: top; font-weight: normal">
                <span
                  v-for="(item, index) in doctor['病程与治疗情况']"
                  :id="`病程与治疗情况-${index}`"
                  :key="`病程与治疗情况-${index}`"
                  @mouseover="highlightText(`病程与治疗情况-${index}`)"
                  @mouseout="removeHighlight(`病程与治疗情况-${index}`)"
                  @click="showSource(`病程与治疗情况-${index}`)"
                >
                  {{ item }}
                </span>
              </td>
            </tr>
            <tr>
              <td colspan="8" style="vertical-align: top">Condition at Discharge:</td>
            </tr>
            <tr>
              <td colspan="8" style="vertical-align: top; font-weight: normal">
                <span
                  v-for="(item, index) in doctor['出院时情况']"
                  :id="`出院时情况-${index}`"
                  :key="`出院时情况-${index}`"
                  @mouseover="highlightText(`出院时情况-${index}`)"
                  @mouseout="removeHighlight(`出院时情况-${index}`)"
                  @click="showSource(`出院时情况-${index}`)"
                >
                  {{ item }}
                </span>
              </td>
            </tr>
            <tr>
              <td colspan="8" style="vertical-align: top">Medication Recommendations After Discharge:</td>
            </tr>
            <tr>
              <td colspan="8" style="vertical-align: top; font-weight: normal">
                <span
                  v-for="(item, index) in doctor['出院后用药建议']"
                  :id="`出院后用药建议-${index}`"
                  :key="`出院后用药建议-${index}`"
                  @mouseover="highlightText(`出院后用药建议-${index}`)"
                  @mouseout="removeHighlight(`出院后用药建议-${index}`)"
                  @click="showSource(`出院后用药建议-${index}`)"
                >
                  {{ item }}
                </span>
              </td>
            </tr>
          </table>
        </div>

        <template #footer>
          <NSpace style="width: 100%; justify-content: right; padding-top: 6px; padding-bottom: 0">
            <NButton size="small" @click="prev"><</NButton>
            <NButton size="small" @click="next">></NButton>
          </NSpace>
        </template>
      </NCard>
    </NGi>
    <NGi span="24 s:24 m:24" style="display: flex">
      <NLayout style="height: calc(30vh)">
        <NLayoutHeader
          class="text-14px"
          style="text-align: center; font-weight: 600; padding: 6px; height: 32px"
          bordered
        >
          来源文书
        </NLayoutHeader>
        <NLayout has-sider position="absolute" style="top: 32px">
          <NLayoutSider bordered :native-scrollbar="false">
            <NMenu
              :collapsed="collapsed"
              :collapsed-width="64"
              :collapsed-icon-size="22"
              :options="menuOptions['患者基本信息']"
              :render-label="renderMenuLabel"
              :render-icon="renderMenuIcon"
              :value="selectedKey"
              size="small"
              @update:value="handleMenuSelect"
            />
          </NLayoutSider>
          <NLayoutContent content-style="padding: 24px;" :native-scrollbar="false">
            <NHighlight
              :text="source['患者基本信息'][selectedKey]"
              :patterns="patterns"
              class="highlight-text"
              :highlight-style="{
                padding: '0 6px',
                borderRadius: themeVars.borderRadius,
                display: 'inline-block',
                color: themeVars.baseColor,
                background: themeVars.primaryColor,
                transition: `all .3s ${themeVars.cubicBezierEaseInOut}`
              }"
            />
          </NLayoutContent>
        </NLayout>
      </NLayout>
    </NGi>
  </NGrid>
</template>

<style scoped>
.n-card-header__main {
  font-weight: bold;
}

:deep(.n-form-item .n-form-item-feedback-wrapper) {
  min-height: 0px;
}
:deep(.n-descriptions-table-header) {
  border: 0 solid;
}

h2 {
  text-align: center;
  margin-bottom: 20px;
}

table {
  width: 100%;
  border-collapse: collapse;
  margin: 0 auto;
}
table tr {
  line-height: 1.2; /* 调整行高 */
}

td {
  padding: 4px;
  text-align: left;
}

td[colspan='5'] {
  text-align: justify;
}

table tr:nth-child(even) {
  background-color: rgb(238, 239, 241, 0.5);
}
table td:nth-child(odd) {
  font-family: 'Times New Roman', 'SimSun', '黑体', sans-serif;
  font-weight: 700;
}

/* 设置表格的第 2、4、6 列为宋体 */
table td:nth-child(even) {
  font-family: 'SimSun', serif; /* 宋体 */
}

.hang-indent {
  display: block;
  text-indent: 0em; /* 让首行 */
  padding-left: 0em; /* 让后续行缩进 1 个字符 */
}

.highlight {
  background-color: rgb(250, 250, 184);
  background-color: #e8efff;
  padding: 0px 0px;
  /* display: inline-block; 让 padding 生效/ */
}

highlight {
  background-color: yellow;
}

/* Ensure that line breaks are respected */
.n-timeline-item-content {
  white-space: pre-line !important;
}

/* 让换行符生效 */
.highlight-text {
  white-space: pre-line;
}
</style>
