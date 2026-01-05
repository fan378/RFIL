<script setup lang="ts">
import { computed } from 'vue';
import { createReusableTemplate } from '@vueuse/core';
import { $t } from '@/locales';

defineOptions({
  name: 'CardData'
});

interface CardData {
  key: string;
  title: string;
  value: number;
  unit: string;
  decimals: number;
  color: {
    start: string;
    end: string;
  };
  suffix: string;
  icon: string;
}

const cardData = computed<CardData[]>(() => [
  {
    key: 'departmentCount',
    title: $t('page.home.departmentCount'),
    value: 15,
    unit: '',
    color: {
      start: 'white',
      end: 'white'
    },
    // icon: 'ant-design:bar-chart-outlined'
    icon: 'ant-design:subnode-outlined'
  },
  {
    key: 'modelCount',
    title: $t('page.home.modelCount'),
    value: 6,
    unit: '',
    color: {
      start: 'white',
      end: 'white'
    },
    icon: 'ant-design:global-outlined'
  },
  {
    key: 'indicatorCount',
    title: $t('page.home.indicatorCount'),
    value: 6,
    unit: '',
    color: {
      start: 'white',
      end: 'white'
    },
    icon: 'ant-design:rise-outlined'
  },
  // {
  //   key: 'qualityScore',
  //   title: $t('page.home.qualityScore'),
  //   value: 95.27,
  //   unit: '',
  //   color: {
  //     start: 'white',
  //     end: 'white'
  //   },
  //   icon: 'ant-design:trademark-circle-outlined'
  // },
  {
    key: 'caseCount',
    title: $t('page.home.caseCount'),
    value: 75000,
    unit: '',
    color: {
      start: 'white',
      end: 'white'
    },
    icon: 'ant-design:file-text-outlined'
  }
  // {
  //   key: 'modificationRate',
  //   title: $t('page.home.modificationRate'),
  //   value: 1.3,
  //   unit: '',
  //   color: {
  //     start: 'white',
  //     end: 'white'
  //   },
  //   suffix:'%',
  //   decimals:'2',
  //   icon: 'ant-design:edit-outlined'
  // }
]);

interface GradientBgProps {
  gradientColor: string;
}

const [DefineGradientBg, GradientBg] = createReusableTemplate<GradientBgProps>();

function getGradientColor(color: CardData['color']) {
  return `linear-gradient(to bottom right, ${color.start}, ${color.end})`;
}
</script>

<template>
  <NCard
    :segmented="{
      content: true,
      footer: 'soft'
    }"
    size="small"
    :bordered="false"
    class="card-wrapper text-18px"
    header-style="padding: 6px var(--n-padding-left) 6px var(--n-padding-left);"
  >
    <template #header>
      <strong>数据概览</strong>
    </template>
    <!-- define component start: GradientBg -->
    <DefineGradientBg v-slot="{ $slots, gradientColor }">
      <div class="border-custom rd-8px px-16px pb-4px pt-8px" :style="{ backgroundImage: gradientColor }">
        <component :is="$slots.default" />
      </div>
    </DefineGradientBg>
    <!-- define component end: GradientBg -->

    <NGrid cols="s:1 m:2 l:2" responsive="screen" :x-gap="16" :y-gap="16">
      <NGi v-for="item in cardData" :key="item.key">
        <GradientBg :gradient-color="getGradientColor(item.color)" class="flex justify-between">
          <div class="flex items-center justify-center">
            <SvgIcon :icon="item.icon" class="text-32px text-#999" />
          </div>
          <div class="flex flex-col items-center dark:text-light">
            <h3 class="text-12px dark:text-light">{{ item.title }}</h3>
            <CountTo
              :prefix="item.unit"
              :start-value="1.0"
              :end-value="item.value"
              :suffix="item.suffix"
              :decimals="item.decimals"
              class="text-14px text-blue dark:text-dark"
            />
          </div>
        </GradientBg>
      </NGi>
    </NGrid>
  </NCard>
</template>

<style scoped>
/* 在你的组件的样式中或全局样式中添加 */
.border-custom {
  border-radius: 8px; /* 圆角边框 */
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1); /* 添加阴影 */
  border: 1px solid #edeef050; /* 设置边框宽度和颜色 */
}
.n-card > .n-card-header .n-card-header__main {
  font-weight: 600;
  font-size: 20px;
}
</style>
