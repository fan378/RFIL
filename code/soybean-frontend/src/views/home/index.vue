<script setup lang="ts">
import { computed } from 'vue';
import { useAppStore } from '@/store/modules/app';
// import HeaderBanner from './modules/header-banner.vue';
import CardData from './modules/card-data.vue';
import LineChart from './modules/line-chart.vue';
import BarChart from './modules/bar-chart.vue';
import HeatmapChart from './modules/heatmap-chart.vue';
import BoxplotChart from './modules/boxplot-chart.vue';
import PieChart from './modules/pie-chart.vue';
import ProjectNews from './modules/project-news.vue';
import CreativityBanner from './modules/creativity-banner.vue';

const appStore = useAppStore();

const gap = computed(() => (appStore.isMobile ? 0 : 16));
</script>

<template>
  <NSpace vertical :size="16">
    <NGrid :x-gap="gap" :y-gap="16" responsive="screen" item-responsive>
      <NGi span="24 s:24 m:8">
        <CardData />
      </NGi>
      <NGi span="24 s:24 m:16">
        <PieChart />
      </NGi>
    </NGrid>
    <NGrid :x-gap="gap" :y-gap="16" responsive="screen" item-responsive>
      <NGi span="24 s:24 m:10">
        <HeatmapChart />
      </NGi>
      <NGi span="24 s:24 m:14">
        <BoxplotChart />
      </NGi>
    </NGrid>
    <NGrid :x-gap="gap" :y-gap="16" responsive="screen" item-responsive>
      <NGi span="24 s:24 m:24">
        <BarChart />
      </NGi>
    </NGrid>
  </NSpace>
</template>

<style scoped></style>
