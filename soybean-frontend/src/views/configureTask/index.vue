<script setup lang="ts">
import { computed, ref } from 'vue';
import { useAppStore } from '@/store/modules/app';
import { useTaskStore } from '@/store/modules/task';
import { PostParams } from '@/service/api';
import { $t } from '@/locales';
import StepsList from './modules/steps.vue';
import UploadFile from './modules/upload-file.vue';
import PreviewFile from './modules/preview.vue';
import PromptSetting from './modules/prompt-setting.vue';
import OnProgress from './modules/on-progress.vue';

// 发送参数，接收prompt对应

const appStore = useAppStore();
const taskStore = useTaskStore();
const gap = computed(() => (appStore.isMobile ? 0 : 16));

// 创建科室名称映射函数
const departmentNameMap: Record<string, string> = {
  [String($t('page.home.breastSurgery'))]: '乳腺外科',
  [String($t('page.home.gastrointestinalSurgery'))]: '胃肠外科',
  [String($t('page.home.thyroidAndVascularSurgery'))]: '甲状腺血管外科',
  [String($t('page.home.otorhinolaryngology'))]: '耳鼻喉科',
  [String($t('page.home.neurosurgery'))]: '神经外科',
  [String($t('page.home.neurology'))]: '神经内科',
  [String($t('page.home.gastroenterology'))]: '消化内科',
  [String($t('page.home.pulmonology'))]: '呼吸内科',
  [String($t('page.home.endocrinology'))]: '内分泌科',
  [String($t('page.home.nephrology'))]: '肾脏内科',
  [String($t('page.home.oncology'))]: '肿瘤科',
  [String($t('page.home.traditionalChineseMedicine'))]: '中医科',
  [String($t('page.home.pediatrics'))]: '小儿科',
  [String($t('page.home.ophthalmology'))]: '眼科',
  [String($t('page.home.gynecology'))]: '妇科'
};

// 映射科室名称
const mapDepartmentName = (translatedName: string): string => {
  return departmentNameMap[translatedName] || translatedName;
};

async function handlePostParams(formData: any) {
  try {
    const { data, error } = await PostParams(formData);
    if (!error) {
      taskStore.setSection(data);
    }
  } catch (err) {
    console.error('Error postParams:', err);
  }
}

const currentRef = ref(1);
const stepsMap = {
  1: UploadFile,
  2: PreviewFile,
  3: PromptSetting,
  4: OnProgress
};
const length = Object.keys(stepsMap).length;
const formData = ref<any>(null); // 用于存储 PreviewFile 的 form 数据
const formComponent = ref<any>(null); // 获取子组件的引用

const next = async () => {
  if (currentRef.value === 2 && formComponent.value) {
    formData.value = formComponent.value.getFormData();
    window.$loadingBar?.start();
    await handlePostParams(formData.value);
    window.$loadingBar?.finish();
  }
  if (currentRef.value === 3 && formComponent.value) {
    formData.value = formComponent.value.getFormData();
  }
  if (currentRef.value === 1) {
    // 添加调试信息
    console.log('检查下一步条件:');
    console.log('currentRef.value:', currentRef.value);
    console.log('taskStore.processedJson:', taskStore.processedJson);
    console.log('taskStore.processedJson.patientId:', taskStore.processedJson.patientId);
    console.log('taskStore.getPatientId():', taskStore.getPatientId());

    // 检查patientId是否为空
    if (!taskStore.processedJson.patientId || taskStore.processedJson.patientId === '') {
      window.$message?.error('Please upload files first!');
      return;
    }
  }
  if (currentRef.value < length) {
    currentRef.value += 1;
  }
};
const prev = () => {
  if (currentRef.value > 1) {
    currentRef.value -= 1;
  }
};
</script>

<template>
  <div>
    <NSpace vertical :size="16">
      <NGrid :x-gap="gap" :y-gap="16" responsive="screen" item-responsive>
        <NGi span="24 s:24 m:24"><StepsList :current="currentRef" /></NGi>
      </NGrid>
      <NGrid :x-gap="gap" :y-gap="16" responsive="screen" item-responsive>
        <NGi span="24 s:24 m:24">
          <!-- 特殊处理第3步：传递科室信息给 PromptSetting -->
          <PromptSetting
            v-if="currentRef === 3"
            ref="formComponent"
            :form-data="formData"
            :selected-department="mapDepartmentName(formData?.department || '')"
          />
          <!-- 其他步骤仍然使用动态组件 -->
          <component
            v-else
            :is="stepsMap[currentRef as keyof typeof stepsMap]"
            ref="formComponent"
            :form-data="formData"
          />
        </NGi>
      </NGrid>
    </NSpace>

    <!-- 固定按钮组在页面底部 -->
    <NFlex justify="center" class="fixed-footer">
      <NButtonGroup>
        <NButton :disabled="currentRef <= 1" @click="prev">返回</NButton>
        <NButton :disabled="currentRef >= length" @click="next">下一步</NButton>
      </NButtonGroup>
    </NFlex>
  </div>
</template>

<style scoped>
.fixed-footer {
  position: fixed;
  bottom: 16px;
  display: flex;
  justify-content: center;
  z-index: 9999;
  width: calc(100% - 220px);
}
</style>
