<script setup lang="ts">
import { watch } from 'vue';
import { $t } from '@/locales';
import { useAppStore } from '@/store/modules/app';
import { useEcharts } from '@/hooks/common/echarts';

defineOptions({
  name: 'PieChart'
});

const appStore = useAppStore();

const { domRef, updateOptions } = useEcharts(() => ({
  // title: {
  //   text: $t('page.home.schedule'), // 替换为你的图表标题
  //   left: '', // 标题居中
  //   top: '', // 距离顶部的间距
  //   textStyle: {
  //     fontSize: 16, // 标题字体大小
  //     fontWeight: 'bold'
  //   }
  // },
  tooltip: {
    trigger: 'item'
  },
  legend: {
    type: 'plain', // 设置图例类型为普通图例
    orient: 'vertical', // 图例垂直排列
    // left: '30%', // 图例位置调整到右侧
    right: '10%', // 图例距右侧10%
    top: 'center', // 垂直居中
    align: 'left', // 图例项文本左对齐
    // itemGap: '20', // 图例项之间的间距
    itemWidth: 20, // 图例图标宽度
    itemHeight: 10, // 图例图标高度
    // formatter(name) {
    //   return name; // 如果需要自定义名称，可以在这里格式化
    // },
    // pageIconSize: [5, 5], // 分页图标大小（如果图例超出时）
    textStyle: {
      fontSize: 12
    },
    itemStyle: {
      borderRadius: '50%' // 设置圆点形状
    }
  },
  series: [
    {
      color: [
        '#d4def8',
        '#C9D5F7',
        '#BCCCF5',
        '#B0C3F4',
        '#A1B9F2',
        '#8FADF0',
        '#7BA1EF',
        '#6495ED',
        '#608FE3',
        '#5B88D9',
        '#5681CE',
        '#517AC4',
        '#4C72B7',
        '#4569A9',
        '#3E5F9A'
      ],

      // name: $t('page.home.schedule'),
      type: 'pie',
      radius: ['70%', '95%'],
      avoidLabelOverlap: false,
      itemStyle: {
        // borderRadius: 10,
        // borderColor: '#fff',
        // borderWidth: 1
      },
      label: {
        show: true,
        position: 'center',
        color: 'var(--blue-15)', // 字体颜色（可选）
        fontSize: 24,
        formatter: '15' // 条件判断
      },
      // emphasis: {
      //   label: {
      //     show: true,
      //     fontSize: 18,
      //     fontWeight: 'bold',
      //     formatter: params => (params.name !== '15' ? params.name : 15) // 条件判断
      //   }
      // },
      labelLine: {
        show: false
      },
      center: ['15%', '50%'], // 调整饼图位置，'30%' 表示靠左
      data: [] as { name: string; value: number }[]
    }
  ]
}));

async function mockData() {
  await new Promise(resolve => {
    setTimeout(resolve, 1000);
  });

  updateOptions(opts => {
    opts.series[0].data = [
      { name: $t('page.home.breastSurgery'), value: 5000 },
      { name: $t('page.home.gastrointestinalSurgery'), value: 5000 },
      { name: $t('page.home.thyroidAndVascularSurgery'), value: 5000 },
      { name: $t('page.home.otorhinolaryngology'), value: 5000 },
      { name: $t('page.home.neurosurgery'), value: 5000 },
      { name: $t('page.home.neurology'), value: 5000 },
      { name: $t('page.home.gastroenterology'), value: 5000 },
      { name: $t('page.home.pulmonology'), value: 5000 },
      { name: $t('page.home.endocrinology'), value: 5000 },
      { name: $t('page.home.nephrology'), value: 5000 },
      { name: $t('page.home.oncology'), value: 5000 },
      { name: $t('page.home.traditionalChineseMedicine'), value: 5000 },
      { name: $t('page.home.pediatrics'), value: 5000 },
      { name: $t('page.home.ophthalmology'), value: 5000 },
      { name: $t('page.home.gynecology'), value: 5000 }
    ];

    return opts;
  });
}

function updateLocale() {
  updateOptions((opts, factory) => {
    const originOpts = factory();

    opts.series[0].name = originOpts.series[0].name;

    opts.series[0].data = [
      { name: $t('page.home.breastSurgery'), value: 5000 },
      { name: $t('page.home.gastrointestinalSurgery'), value: 5000 },
      { name: $t('page.home.thyroidAndVascularSurgery'), value: 5000 },
      { name: $t('page.home.otorhinolaryngology'), value: 5000 },
      { name: $t('page.home.neurosurgery'), value: 5000 },
      { name: $t('page.home.neurology'), value: 5000 },
      { name: $t('page.home.gastroenterology'), value: 5000 },
      { name: $t('page.home.pulmonology'), value: 5000 },
      { name: $t('page.home.endocrinology'), value: 5000 },
      { name: $t('page.home.nephrology'), value: 5000 },
      { name: $t('page.home.oncology'), value: 5000 },
      { name: $t('page.home.traditionalChineseMedicine'), value: 5000 },
      { name: $t('page.home.pediatrics'), value: 5000 },
      { name: $t('page.home.ophthalmology'), value: 5000 },
      { name: $t('page.home.gynecology'), value: 5000 }
    ];

    return opts;
  });
}

async function init() {
  mockData();
}

watch(
  () => appStore.locale,
  () => {
    updateLocale();
  }
);

// init
init();
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
      <strong>科室分布</strong>
    </template>
    <div ref="domRef" class="h-125px overflow-hidden"></div>
  </NCard>
</template>

<style scoped>
</style>
