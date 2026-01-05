<script setup lang="ts">
import { defineEmits, defineOptions, defineProps, ref } from 'vue';
import { NButton, NInput, NModal } from 'naive-ui';
import { $t } from '@/locales';
import { useTaskStore } from '@/store/modules/task';
import { PostComment } from '@/service/api';

defineOptions({
  name: 'MenuBar'
});

const taskStore = useTaskStore();
const current_section = ref($t('page.home.patientInfo'));
const sections = [
  $t('page.home.patientInfo'),
  $t('page.home.dischargeDiagnosis'),
  $t('page.home.medicalTestsAndExaminations'),
  $t('page.home.diseaseCourseAndTreatment'),
  $t('page.home.conditionAtDischarge'),
  $t('page.home.postDischargeMedicationAdvice')
];
const SectionOptions = sections.map(v => ({ label: v, value: v }));

// 控制编辑
const props = defineProps<{ isEditing: boolean }>();
const emit = defineEmits(['toggle-edit', 'export-data']);
const handleExport = () => {
  const data = emit('export-data');
};
const handleClick = () => {
  emit('toggle-edit'); // 通知 index.vue 切换 isEditing 状态
};
const handleSave = () => {
  emit('toggle-edit'); // 通知 index.vue 切换 isEditing 状态
};

// 控制 Modal 显示状态
const isModalVisible = ref(false);
const comment = ref(''); // 用于存储用户输入的评论

// 处理点击 comment 按钮
const handleCommentButtonClick = () => {
  isModalVisible.value = true; // 显示 Modal
};

// 提交修改意见
async function handleCommentSubmit() {
  isModalVisible.value = false; // 关闭 Modal
  const formData = new FormData();
  formData.append('comment', comment.value); // 将 comment.value 添加到 FormData
  formData.append('save_id', taskStore.processedJson.patientId);

  try {
    const { data, error } = await PostComment(formData); // 发送 FormData
    if (!error) {
      window.$message.success('Submission successful!');
    }
  } catch (err) {
    window.$message.error('Submission failed!');
  }

  comment.value = ''; // 清空输入框
}

// 取消评论
const handleCancel = () => {
  isModalVisible.value = false; // 关闭 Modal
};
</script>

<template>
  <NCard size="small" :bordered="false" class="card-wrapper">
    <NSpace :cols="12">
      <!-- <NButton type="primary" @click="">Regenerate</NButton> -->
      <NButton v-if="!isEditing" type="primary" @click="handleClick">编辑</NButton>
      <NButton v-else type="primary" @click="handleSave">Save</NButton>
      <NButton type="primary" @click="handleCommentButtonClick">评论</NButton>
      <NButton type="primary" @click="handleExport">导出</NButton>
    </NSpace>
  </NCard>

  <!-- Modal 弹窗 -->
  <NModal v-model:show="isModalVisible" title="Comments" preset="card" style="max-width: 600px; width: 90vw">
    <template #default>
      <NInput v-model:value="comment" type="textarea" placeholder="Please enter your comment" rows="4" />
    </template>
    <template #footer>
      <div class="modal-footer" style="display: flex; justify-content: flex-end; gap: 8px">
        <NButton type="primary" @click="handleCommentSubmit">Submit</NButton>
        <NButton @click="handleCancel">Cancel</NButton>
      </div>
    </template>
  </NModal>
</template>

<style scoped>
:deep(.n-form-item .n-form-item-feedback-wrapper) {
  min-height: 0px;
}
</style>
