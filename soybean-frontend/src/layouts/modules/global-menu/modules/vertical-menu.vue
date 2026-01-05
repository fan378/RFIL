<script setup lang="ts">
import { computed, ref, watch } from 'vue';
import { useRoute } from 'vue-router';
import { SimpleScrollbar } from '@sa/materials';
import { useAppStore } from '@/store/modules/app';
import { useThemeStore } from '@/store/modules/theme';
import { useRouteStore } from '@/store/modules/route';
import { useRouterPush } from '@/hooks/common/router';
import { GLOBAL_SIDER_MENU_ID } from '@/constants/app';
import { useMenu } from '../../../context';

// 自定义样式

defineOptions({
  name: 'VerticalMenu'
});

const route = useRoute();
const appStore = useAppStore();
const themeStore = useThemeStore();
const routeStore = useRouteStore();
const { routerPushByKeyWithMetaQuery } = useRouterPush();
const { selectedKey } = useMenu();

const inverted = computed(() => !themeStore.darkMode && themeStore.sider.inverted);

const expandedKeys = ref<string[]>([]);

const menuThemeOverrides = {
  itemColorActive: '#FFFFFF', // 选中时背景颜色
  itemColorActiveHover: '#e2eaf9', // 选中时背景颜色
  itemTextColor: '#000000',
  // itemTextColorHover: '  #e2eaf9',
  // itemTextColorActive: '#000000',
  // itemTextColorActiveHover: '#000000',
  itemIconColor: '#000000',
  // itemIconColorHover: '#000000',
  // itemIconColorActive: '#000000',
  // itemIconColorActiveHover: '#000000',
};

function updateExpandedKeys() {
  if (appStore.siderCollapse || !selectedKey.value) {
    expandedKeys.value = [];
    return;
  }
  expandedKeys.value = routeStore.getSelectedMenuKeyPath(selectedKey.value);
}

watch(
  () => route.name,
  () => {
    updateExpandedKeys();
  },
  { immediate: true }
);
</script>

<template>
  <Teleport :to="`#${GLOBAL_SIDER_MENU_ID}`">
    <SimpleScrollbar>
      <NMenu
        v-model:expanded-keys="expandedKeys"
        mode="vertical"
        :value="selectedKey"
        :collapsed="appStore.siderCollapse"
        :collapsed-width="themeStore.sider.collapsedWidth"
        :collapsed-icon-size="22"
        :options="routeStore.menus"
        :inverted="inverted"
        :indent="18"
        :theme-overrides="menuThemeOverrides"
        @update:value="routerPushByKeyWithMetaQuery"
      />
    </SimpleScrollbar>
  </Teleport>
</template>

<style scoped></style>
