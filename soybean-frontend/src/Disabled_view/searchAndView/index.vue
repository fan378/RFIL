<script setup lang="ts">
import { computed, defineComponent, ref } from 'vue';
import type { DataTableColumns } from 'naive-ui';
import { useAppStore } from '@/store/modules/app';

const appStore = useAppStore();
const gap = computed(() => (appStore.isMobile ? 0 : 16));

interface RowData {
  key: number;
  name: string;
  age: number;
  address: string;
}

// 搜索关键字
const searchQuery = ref('');

// 原始数据
const originalData = [
  {
    key: 0,
    name: 'John Brown',
    age: 32,
    address: 'New York No. 1 Lake Park'
  },
  {
    key: 1,
    name: 'Jim Green',
    age: 42,
    address: 'London No. 1 Lake Park'
  },
  {
    key: 2,
    name: 'Joe Black',
    age: 32,
    address: 'Sidney No. 1 Lake Park'
  }
];

// 根据搜索条件过滤数据
const filteredData = computed(() => {
  if (!searchQuery.value) return originalData;
  return originalData.filter(
    item =>
      item.name.toLowerCase().includes(searchQuery.value.toLowerCase()) ||
      item.address.toLowerCase().includes(searchQuery.value.toLowerCase())
  );
});

function createColumns(): DataTableColumns<RowData> {
  return [
    {
      type: 'selection'
    },
    {
      title: 'Name',
      key: 'name'
    },
    {
      title: 'Age',
      key: 'age'
    },
    {
      title: 'Address',
      key: 'address'
    }
  ];
}

const columns = createColumns();
</script>

<template>
  <div>
    <NCard size="small" :bordered="false" class="card-wrapper"></NCard>
    <NGrid :x-gap="gap" :y-gap="16" responsive="screen" item-responsive>
      <!-- 搜索框 -->
      <NGi span="24">
        <NCard size="small" :bordered="false">
          <NInput v-model:value="searchQuery" placeholder="Search by name or address" clearable size="large" />
        </NCard>
      </NGi>

      <!-- 数据表格（添加间隔） -->
      <NGi span="24" class="margin-top">
        <NCard size="small" :bordered="false">
          <NDataTable :columns="columns" :data="filteredData" striped />
        </NCard>
      </NGi>
    </NGrid>
  </div>
</template>

<style scoped>
.margin-top {
  margin-top: 16px; /* 添加顶部间距 */
}
.margin-6px {
  margin-left: 12px;
  margin-right: 12px;
  width: calc(100% - 12 * 2px);
  height: 70vh;
}
</style>
