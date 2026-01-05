<script setup lang="ts">
import { computed, defineOptions, onMounted, ref } from 'vue';
import { useRouter } from 'vue-router';

defineOptions({
  name: 'TumorHospitalFilePreview'
});

interface Props {
  fileData: any;
}

const props = defineProps<Props>();
const router = useRouter();
const isGenerating = ref(false);

const activeTab = ref('门急诊病历_2024.12.16 11:10');

// 获取所有可用的标签页
const tabs = computed(() => {
  if (!props.fileData) {
    console.log('fileData为空');
    return [];
  }
  const keys = Object.keys(props.fileData);
  console.log('可用的标签页:', keys);
  return keys;
});

// 格式化显示内容
const formatContent = (content: string) => {
  if (!content) return '';

  // 将换行符转换为HTML换行
  return content.replace(/\n/g, '<br>');
};

// 获取当前标签页的内容
const currentContent = computed(() => {
  if (!props.fileData || !activeTab.value) return '';
  const content = props.fileData[activeTab.value];

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

onMounted(() => {
  console.log('文件预览组件挂载，接收到的数据:', props.fileData);
  console.log('数据类型:', typeof props.fileData);
  console.log('数据键:', props.fileData ? Object.keys(props.fileData) : []);

  if (tabs.value.length > 0) {
    activeTab.value = tabs.value[0];
    console.log('设置默认标签页:', activeTab.value);
  }
});

// 处理生成按钮点击
const handleGenerate = async () => {
  try {
    isGenerating.value = true;

    // 跳转到等待页面，并传递文件数据
    router.push({
      path: '/tumorhospital/generating',
      query: {
        fileData: JSON.stringify(props.fileData)
      }
    });
  } catch (error) {
    console.error('跳转失败:', error);
    isGenerating.value = false;
  }
};
</script>

<template>
  <div>
    <NCard title="肿瘤医院文件内容预览" class="mb-4">
      <NText depth="3">
        以下是上传文件中的所有医疗数据内容，您可以查看各个部分的详细信息。
      </NText>

      <!-- 生成按钮 -->
      <div class="mt-4">
        <NButton
          type="primary"
          size="large"
          :loading="isGenerating"
          @click="handleGenerate"
        >
          <template #icon>
            <NIcon>
              <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M12 2v6m0 0v6m0-6h6m-6 0H6"/>
              </svg>
            </NIcon>
          </template>
          开始生成
        </NButton>
      </div>
    </NCard>

    <NCard>
      <!-- 调试信息 -->
      <div v-if="!tabs.length" class="mb-4">
        <NAlert type="warning" title="调试信息">
          <p>没有找到可用的标签页</p>
          <p>fileData: {{ fileData }}</p>
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
          <div class="file-content">
            <NAlert type="info" title="数据说明" class="mb-4">
              <p>这是 {{ tab }} 的详细内容，包含了相关的医疗信息。</p>
            </NAlert>

            <NCard title="内容详情" size="small">
              <div
                class="content-display"
                v-html="formatContent(currentContent)"
              ></div>
            </NCard>
          </div>
        </NTabPane>
      </NTabs>
    </NCard>
  </div>
</template>

<style scoped>
.file-content {
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
