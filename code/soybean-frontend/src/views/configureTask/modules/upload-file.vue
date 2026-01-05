<script setup lang="ts">
import { defineOptions, ref } from 'vue';
import { useMessage } from 'naive-ui';
import type { UploadFileInfo } from 'naive-ui';
import { ArchiveOutline as ArchiveIcon, DocumentAttachOutline, DownloadOutline } from '@vicons/ionicons5';
import { UploadFiles, quickUploadFiles } from '@/service/api';
import { useTaskStore } from '@/store/modules/task';

defineOptions({
  name: 'UploadFile'
});

const taskStore = useTaskStore();

const headers = { 'Content-Type': 'multipart/form-data' };
const fileList = ref<UploadFileInfo[]>([]); // 存储用户上传的文件列表
const message = useMessage();

async function UploadFilesRequest(options: { fileList: UploadFileInfo[] }) {
  const formData = new FormData();
  options.fileList.forEach(file => {
    if (file.file) {
      formData.append(file.name, file.file);
    }
  });

  const { data: info, error } = await UploadFiles(headers, formData);

  console.log('上传响应:', info);
  console.log('响应数据结构:', {
    hasData: Boolean(info),
    dataKeys: info ? Object.keys(info) : [],
    dataType: typeof info
  });

  if (!error) {
    // update store
    const patientId = Object.keys(info)[0];
    console.log('提取的patientId:', patientId);
    console.log('patientId类型:', typeof patientId);
    console.log('patientId长度:', patientId?.length);

    // 设置患者数据
    taskStore.setPatientData(info);
    // 设置患者ID
    taskStore.setPatientId(patientId);

    // 调试：检查设置后的状态
    console.log('设置后的processedJson:', taskStore.processedJson);
    console.log('设置后的patientId:', taskStore.getPatientId());
    console.log('processedJson.patientId:', taskStore.processedJson.patientId);
    console.log('patientId是否为空:', !taskStore.processedJson.patientId);
    console.log('patientId是否等于空字符串:', taskStore.processedJson.patientId === '');

    message.success('上传成功!');
  } else {
    console.error('上传失败:', error);
    message.error('上传失败，请重试');
  }
}

let timerId: NodeJS.Timeout | null = null;
const wait = 500;

const handleChange = (options: { fileList: UploadFileInfo[] }) => {
  if (timerId !== null) {
    clearTimeout(timerId);
  }

  timerId = setTimeout(() => {
    // console.log('handle', options.fileList.length);
    UploadFilesRequest(options);
    // 重置定时器
    timerId = null;
  }, wait);
};

// 新增的上传文件功能
async function uploadSampleFiles() {
  try {
    // 上传文件
    const { data, error } = await quickUploadFiles();

    console.log('示例文件上传响应:', data);
    console.log('示例文件响应数据结构:', {
      hasData: Boolean(data),
      dataKeys: data ? Object.keys(data) : [],
      dataType: typeof data
    });

    if (!error) {
      const patientId = Object.keys(data)[0];
      console.log('示例文件上传 - 提取的patientId:', patientId);
      console.log('示例文件patientId类型:', typeof patientId);
      console.log('示例文件patientId长度:', patientId?.length);

      // 设置患者数据
      taskStore.setPatientData(data);
      // 设置患者ID
      taskStore.setPatientId(patientId);

      // 调试：检查设置后的状态
      console.log('示例文件上传 - 设置后的processedJson:', taskStore.processedJson);
      console.log('示例文件上传 - 设置后的patientId:', taskStore.getPatientId());
      console.log('示例文件processedJson.patientId:', taskStore.processedJson.patientId);
      console.log('示例文件patientId是否为空:', !taskStore.processedJson.patientId);
      console.log('示例文件patientId是否等于空字符串:', taskStore.processedJson.patientId === '');

      message.success('上传成功!');
    } else {
      console.error('示例文件上传失败:', error);
      message.error('示例文件上传失败，请重试');
    }
  } catch (err) {
    console.error('Error uploading files:', err);
    message.error('上传过程中发生错误');
  }
}

// 支持的文件类型
const supportedFileTypes = [
  { label: 'JSON文件', extensions: ['.json'], description: '包含所有数据的合并JSON文件' },
  { label: 'CSV文件', extensions: ['.csv'], description: '分别的CSV数据文件' }
];

// CSV 示例文件列表
const sampleFiles = [
  { label: 'bingli.csv', url: '/static/samples/bingli.csv' },
  { label: 'hulijilu.csv', url: '/static/samples/hulijilu.csv' },
  { label: 'jiancha.csv', url: '/static/samples/jiancha.csv' },
  { label: 'jianyan.csv', url: '/static/samples/jianyan.csv' },
  { label: 'tizheng.csv', url: '/static/samples/tizheng.csv' },
  { label: 'wenshu.csv', url: '/static/samples/wenshu.csv' },
  { label: 'yizhu.csv', url: '/static/samples/yizhu.csv' },
  { label: 'zhenduan.csv', url: '/static/samples/zhenduan.csv' }
];

// JSON 示例文件
const jsonSampleFiles = [
  { label: '19010300000169.json', url: '/19010300000169.json', description: '包含完整患者数据的JSON文件' }
];
</script>

<template>
  <NUpload
    v-model:file-list="fileList"
    multiple
    :header="{}"
    directory-dnd
    :max="10"
    accept=".json,.csv"
    @change="handleChange"
  >
    <NUploadDragger>
      <div style="margin-bottom: 12px">
        <NIcon size="48" :depth="3">
          <ArchiveIcon />
        </NIcon>
      </div>
      <NText style="font-size: 16px">单击或将文件拖到此区域进行上传。</NText>
      <NP depth="3" style="margin: 8px 0 0 0">
        支持 JSON 和 CSV 文件格式，请不要上传敏感数据
      </NP>
    </NUploadDragger>
  </NUpload>

  <NGrid cols="2" x-gap="16">
    <!-- 左侧：文档说明 -->
    <NGridItem>
      <NAlert title="操作说明" type="info">
        <p>上传文件之前，请按照以下说明操作：</p>
        <ol>
          <li>
            <strong>JSON文件上传（推荐）：</strong> 您可以上传一个包含所有数据的JSON文件，系统会自动处理并转换为所需的格式。
          </li>
          <li>
            <strong>CSV文件上传：</strong> 如果您有分别的CSV文件，可以一次性上传所有8个CSV文件。拖放操作完成后，系统将立即处理文件格式。
          </li>
          <li>
            如果您不小心遗漏了某个文件，不用担心——只需重新上传文件，系统就会覆盖之前上传的文件。
          </li>
        </ol>

        <!-- 添加分割线 -->
        <NDivider />

        <!-- 便捷上传操作 -->
        <NText>
          为了提升您的体验，您可以点击下方按钮。它会直接将测试文件提交到后端，无需手动下载和上传。
        </NText>
        <br />
        <NButton type="primary" size="small" @click="uploadSampleFiles">
          <NIcon><DocumentAttachOutline /></NIcon>
          <span>上传示例文件</span>
        </NButton>
      </NAlert>

      <!-- 支持的文件类型说明 -->
      <NCard title="支持的文件类型" style="margin-top: 16px">
        <NList hoverable>
          <NListItem v-for="fileType in supportedFileTypes" :key="fileType.label">
            <div style="display: flex; justify-content: space-between; align-items: center; width: 100%">
              <div>
                <NText strong>{{ fileType.label }}</NText>
                <br />
                <NText depth="3" style="font-size: 12px">{{ fileType.description }}</NText>
              </div>
              <NTag :bordered="false" type="info" size="small">
                {{ fileType.extensions.join(', ') }}
              </NTag>
            </div>
          </NListItem>
        </NList>
      </NCard>
    </NGridItem>

    <!-- 右侧：示例文件列表 -->
    <NGridItem>
      <!-- JSON 示例文件 -->
      <NCard title="JSON 示例文件" style="margin-bottom: 16px">
        <NList hoverable style="overflow: auto; padding: 0; border: none">
          <NListItem v-for="file in jsonSampleFiles" :key="file.label" style="padding: 6px 12px; border-bottom: none">
            <div style="display: flex; justify-content: space-between; align-items: center; width: 100%">
              <div style="display: flex; align-items: center; gap: 6px; flex: 1;">
                <NIcon><DocumentAttachOutline /></NIcon>
                <div>
                  <NText>{{ file.label }}</NText>
                  <br />
                  <NText depth="3" style="font-size: 12px">{{ file.description }}</NText>
                </div>
              </div>
              <a :href="file.url" download style="color: inherit">
                <NIcon size="18"><DownloadOutline /></NIcon>
              </a>
            </div>
          </NListItem>
        </NList>
      </NCard>

      <!-- CSV 示例文件 -->
      <NCard title="CSV 示例文件">
        <NList hoverable style="overflow: auto; padding: 0; border: none">
          <NListItem v-for="file in sampleFiles" :key="file.label" style="padding: 6px 12px; border-bottom: none">
            <div style="display: flex; justify-content: space-between; align-items: center; width: 100%">
              <div style="display: flex; align-items: center; gap: 6px">
                <NIcon><DocumentAttachOutline /></NIcon>
                <span>{{ file.label }}</span>
              </div>
              <a :href="file.url" download style="color: inherit">
                <NIcon size="18"><DownloadOutline /></NIcon>
              </a>
            </div>
          </NListItem>
        </NList>
      </NCard>
    </NGridItem>
  </NGrid>
</template>

<style scoped>
::v-deep(.n-alert.n-alert--show-icon .n-alert-body) {
  padding-right: calc(var(--n-icon-margin-left) + var(--n-icon-size) + var(--n-icon-margin-right));
}
::v-deep(.n-divider:not(.n-divider--dashed) .n-divider__line) {
  background-color: var(--n-divider-color);
}
</style>
