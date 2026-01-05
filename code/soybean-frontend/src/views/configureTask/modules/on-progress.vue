<script setup lang="ts">
import { ref } from 'vue';
import { NButton, NProgress, useMessage } from 'naive-ui';
import axios from 'axios';
import { useRouter } from 'vue-router';
import { useTaskStore } from '@/store/modules/task';
import { GenerateDS } from '@/service/api';

defineOptions({
  name: 'OnProgress'
});

const props = defineProps<{
  formData: any;
}>();

const progress = ref(0); // 进度百分比
const status = ref('active'); // 进度条的状态（'active', 'success', 'exception'）
const processing = ref(true);
const show = ref(true);
const taskStore = useTaskStore();
const message = useMessage();
const router = useRouter(); // 获取 Vue Router 实例

async function handleGenerateDS(formData) {
  show.value = true;
  try {
    window.$loadingBar.start();
    const { data, error } = await GenerateDS(formData);
    if (!error) {
      await taskStore.setDischargeSummary(data);
      message.success('Generated successfully!');
      // 跳转到指定的页面 /review
      router.push('/compareandreview');
      show.value = false;
      window.$loadingBar.finish();
    }
  } catch (err) {
    console.error('Error Generation:', err);
    show.value = false;
    window.$loadingBar.finish();
  }
}
handleGenerateDS(props.formData);
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
    <!--
 <template #header>
      <strong>Configure Params</strong>
    </template>
-->
    <NSpin :show="show">
      <NSkeleton text :repeat="2" />
      <NSkeleton text style="width: 60%" />
      <NSkeleton text :repeat="2" />
      <NSkeleton text style="width: 40%" />
      <NSkeleton text :repeat="8" />
      <template #description>生成耗时约2分钟，请耐心等待 ~</template>
    </NSpin>

    <!--
 <NSpace vertical>
      <NProgress type="line" :percentage="progress" color="#1f61ff" :processing="processing" />
    </NSpace>
-->
  </NCard>
</template>

<style scoped>
.margin-6px {
  margin-left: 12px;
  margin-right: 12px;
  width: calc(100% - 12 * 2px);
  height: 70vh;
}
</style>
