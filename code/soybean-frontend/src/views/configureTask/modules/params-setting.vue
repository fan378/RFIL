<script setup lang="ts">
import { defineExpose, defineOptions, reactive, ref } from 'vue';
import type { FormInst } from 'naive-ui';
import { $t } from '@/locales';
import { useTaskStore } from '@/store/modules/task';

defineOptions({
  name: 'ParamsSetting'
});

const formRef = ref<FormInst | null>(null);
const size = ref<'small' | 'medium' | 'large'>('medium');
const taskStore = useTaskStore();
const form = reactive({
  key_id: taskStore.processedJson.patientId,
  model: 'EMR-LLM',
  department: $t('page.home.breastSurgery'),
  topk: 3,
  topp: 0.7,
  max_tokens: 8096
});
const rules = {
  model: {
    required: true,
    trigger: ['blur', 'input'],
    message: 'Please choose model'
  },
  departments: {
    required: true,
    trigger: ['blur', 'input'],
    message: 'Please choose departments'
  }
};

const departments = [
  $t('page.home.breastSurgery'),
  $t('page.home.gastrointestinalSurgery'),
  $t('page.home.thyroidAndVascularSurgery'),
  $t('page.home.otorhinolaryngology'),
  $t('page.home.neurosurgery'),
  $t('page.home.neurology'),
  $t('page.home.gastroenterology'),
  $t('page.home.pulmonology'),
  $t('page.home.endocrinology'),
  $t('page.home.nephrology'),
  $t('page.home.oncology'),
  $t('page.home.traditionalChineseMedicine'),
  $t('page.home.pediatrics'),
  $t('page.home.ophthalmology'),
  $t('page.home.gynecology'),
  "肿瘤医院头颈外科"
];
const models = ['BenTaso', 'Alpacare', 'Qwen2', 'Chatglm3', 'HuaTuoGPT', 'EMR-LLM'];
const ModelOptions = models.map(v => ({
  label: v,
  value: v,
  disabled: v !== 'EMR-LLM' // 只有 EMR-LLM 启用，其他选项禁用
}));
const DepartmentOptions = departments.map(v => ({ label: v, value: v }));
// 导出表单数据
defineExpose({
  getFormData: () => form
});
</script>

<template>
  <NCard
    :segmented="{
      content: true,
      footer: 'soft'
    }"
    size="small"
    :bordered="false"
    class="margin-6px card-wrapper"
  >
    <template #header>
      <strong>配置参数</strong>
    </template>
    <NForm ref="formRef" :model="form" :rules="rules" :size="size" label-placement="top">
      <NGrid :cols="12" :x-gap="8" :y-gap="0">
        <NFormItemGi :span="12" label="模型" path="selectValue">
          <NSelect v-model:value="form.model" placeholder="Select Model" :options="ModelOptions" />
        </NFormItemGi>
        <NFormItemGi :span="12" label="科室" path="selectValue">
          <NSelect v-model:value="form.department" placeholder="Select Department" :options="DepartmentOptions" />
        </NFormItemGi>
        <NFormItemGi :span="12">
          <NCollapse>
            <NCollapseItem title="更多设置" name="1" :expanded="true">
              <NCollapse>
                <NFormItemGi :span="12" label="topk" path="topkValue">
                  <NSlider v-model:value="form.topk" :max="10" :step="1" />
                </NFormItemGi>
                <NFormItemGi :span="12" label="topp" path="toppValue">
                  <NSlider v-model:value="form.topp" :max="1" :step="0.1" />
                </NFormItemGi>
                <NFormItemGi :span="12" label="最大tokens" path="tokensValue">
                  <NSlider v-model:value="form.max_tokens" :max="8096" :step="5" />
                </NFormItemGi>
              </NCollapse>
            </NCollapseItem>
          </NCollapse>
        </NFormItemGi>
      </NGrid>
    </NForm>
  </NCard>
</template>

<style scoped>
.margin-6px {
  /* margin-left: 12px; */
  height: 72vh;
}
:deep(.n-form-item .n-form-item-feedback-wrapper) {
  min-height: 12px;
}
</style>
