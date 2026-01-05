<script setup lang="ts">
import { defineOptions, onMounted, ref } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { useMessage } from 'naive-ui';
import { GenerateTumorHospital } from '@/service/api/configureTask';

defineOptions({
  name: 'TumorHospitalGenerating'
});

const router = useRouter();
const route = useRoute();
const message = useMessage();
const progress = ref(0);
const status = ref('正在初始化...');

// 模拟进度更新
const updateProgress = () => {
  const interval = setInterval(() => {
    if (progress.value < 90) {
      progress.value += Math.random() * 10;
      if (progress.value < 30) {
        status.value = '正在读取文件数据...';
      } else if (progress.value < 60) {
        status.value = '正在处理医疗数据...';
      } else if (progress.value < 90) {
        status.value = '正在生成结果...';
      }
    }
  }, 500);

  return interval;
};

// 调用后端生成API
const callGenerateAPI = async () => {
  try {
    const fileData = route.query.fileData;
    if (!fileData) {
      throw new Error('文件数据丢失');
    }

    // 解析文件数据
    const parsedFileData = JSON.parse(fileData as string);

    // 调用后端API
    const response = await GenerateTumorHospital(parsedFileData);

    // 处理成功响应
    progress.value = 100;
    status.value = '生成完成！';

    // 延迟跳转到结果页面
    setTimeout(() => {
      router.push({
        path: '/tumorhospital/result',
        query: {
          result: JSON.stringify(response)
        }
      });
    }, 1000);

  } catch (error) {
    console.error('生成失败:', error);
    message.error('生成失败，请重试');

    // 延迟返回上一页
    setTimeout(() => {
      router.back();
    }, 2000);
  }
};

onMounted(async () => {
  // 开始进度更新
  const progressInterval = updateProgress();

  // 调用生成API
  await callGenerateAPI();

  // 清理定时器
  clearInterval(progressInterval);
});
</script>

<template>
  <div class="generating-page">
    <NCard title="肿瘤医院数据生成" class="max-w-2xl mx-auto mt-8">
      <div class="text-center">
        <!-- 加载动画 -->
        <div class="mb-6">
          <NIcon size="64" class="text-blue-500 animate-spin">
            <svg xmlns="http://www.w3.org/2000/svg" width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M21 12a9 9 0 11-6.219-8.56"/>
            </svg>
          </NIcon>
        </div>

        <!-- 进度条 -->
        <div class="mb-6">
          <NProgress
            type="line"
            :percentage="progress"
            :show-indicator="false"
            :height="8"
            color="#1890ff"
          />
        </div>

        <!-- 状态信息 -->
        <div class="mb-6">
          <NText size="large" class="text-gray-700">
            {{ status }}
          </NText>
        </div>

        <!-- 进度百分比 -->
        <div class="mb-6">
          <NText size="x-large" class="text-blue-600 font-bold">
            {{ Math.round(progress) }}%
          </NText>
        </div>

        <!-- 提示信息 -->
        <NAlert type="info" class="text-left">
          <template #header>
            <NIcon>
              <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <circle cx="12" cy="12" r="10"/>
                <path d="M12 16v-4"/>
                <path d="M12 8h.01"/>
              </svg>
            </NIcon>
            处理提示
          </template>
          <p>正在使用 zhongliu.py 处理您的医疗数据，这可能需要一些时间。请耐心等待，不要关闭页面。</p>
        </NAlert>
      </div>
    </NCard>
  </div>
</template>

<style scoped>
.generating-page {
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 20px;
}

.animate-spin {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}
</style>
