<script setup lang="ts">
import { computed, defineOptions, onMounted, ref } from 'vue';
import { useRoute, useRouter } from 'vue-router';

defineOptions({
  name: 'TumorHospitalResult'
});

const router = useRouter();
const route = useRoute();
const resultData = ref<any>(null);
const activeTab = ref('');

// 获取所有可用的标签页
const tabs = computed(() => {
  if (!resultData.value) return [];
  return Object.keys(resultData.value);
});

// 获取当前标签页的内容
const currentContent = computed(() => {
  if (!resultData.value || !activeTab.value) return '';
  const content = resultData.value[activeTab.value];

  // 如果内容是对象，转换为JSON字符串
  if (typeof content === 'object' && content !== null) {
    return JSON.stringify(content, null, 2);
  }

  // 如果内容是字符串，直接返回
  if (typeof content === 'string') {
    return content;
  }

  // 其他情况，转换为字符串
  return String(content);
});

// 返回上传页面
const handleBackToUpload = () => {
  router.push({ path: '/tumorhospital' });
};

// 重新生成
const handleRegenerate = () => {
  router.push({ path: '/tumorhospital' });
};

onMounted(() => {
  try {
    const result = route.query.result;
    if (result) {
      resultData.value = JSON.parse(result as string);
      console.log('结果数据:', resultData.value);

      // 设置默认标签页
      if (tabs.value.length > 0) {
        activeTab.value = tabs.value[0];
      }
    }
  } catch (error) {
    console.error('解析结果数据失败:', error);
  }
});
</script>

<template>
  <div>
    <NCard title="肿瘤医院生成结果" class="mb-4">
      <NText depth="3">
        以下是使用 zhongliu.py 处理后的生成结果，您可以查看各个部分的详细信息。
      </NText>

      <!-- 操作按钮 -->
      <div class="mt-4 flex gap-4">
        <NButton @click="handleBackToUpload">
          <template #icon>
            <NIcon>
              <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M19 12H5"/>
                <path d="M12 19l-7-7 7-7"/>
              </svg>
            </NIcon>
          </template>
          返回上传页面
        </NButton>

        <NButton type="primary" @click="handleRegenerate">
          <template #icon>
            <NIcon>
              <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M3 12a9 9 0 0 1 9-9 9.75 9.75 0 0 1 6.74 2.74L21 8"/>
                <path d="M21 3v5h-5"/>
                <path d="M21 12a9 9 0 0 1-9 9 9.75 9.75 0 0 1-6.74-2.74L3 16"/>
                <path d="M3 21v-5h5"/>
              </svg>
            </NIcon>
          </template>
          重新生成
        </NButton>
      </div>
    </NCard>

    <NCard>
      <!-- 调试信息 -->
      <div v-if="!tabs.length" class="mb-4">
        <NAlert type="warning" title="调试信息">
          <p>没有找到可用的结果数据</p>
          <p>resultData: {{ resultData }}</p>
          <p>tabs: {{ tabs }}</p>
        </NAlert>
      </div>

      <NTabs v-model:value="activeTab" type="line" animated>
        <NTabPane
          v-for="tab in tabs"
          :key="tab"
          :name="tab"
          :tab="tab"
        >
          <div class="result-content">
            <NAlert type="success" title="生成成功" class="mb-4">
              <p>这是 {{ tab }} 的生成结果，包含了处理后的医疗信息。</p>
            </NAlert>

            <NCard title="结果详情" size="small">
              <div
                class="content-display"
                v-html="currentContent.replace(/\n/g, '<br>')"
              ></div>
            </NCard>
          </div>
        </NTabPane>
      </NTabs>
    </NCard>
  </div>
</template>

<style scoped>
.result-content {
  padding: 16px 0;
}

.content-display {
  font-family: 'Courier New', monospace;
  line-height: 1.6;
  white-space: pre-wrap;
  word-wrap: break-word;
  background-color: #f8f9fa;
  padding: 16px;
  border-radius: 6px;
  border: 1px solid #e9ecef;
  max-height: 600px;
  overflow-y: auto;
}

.content-display :deep(br) {
  margin-bottom: 4px;
}
</style>
