<script setup lang="ts">
import { defineOptions, ref } from 'vue';

defineOptions({
  name: 'TreeNode'
});

const props = defineProps({
  node: Object
});

const isOpen = ref(false);

function toggle() {
  isOpen.value = !isOpen.value;
}
</script>

<template>
  <div class="tree-node">
    <div>
      <button :aria-expanded="isOpen.toString()" @click="toggle">
        {{ isOpen ? '[-]' : '[+]' }}
      </button>
      <span>{{ node.label }}</span>
    </div>
    <div v-for="(child, index) in node.children" v-if="isOpen" :key="index">
      <TreeNode :node="child" />
    </div>
  </div>
</template>

<style scoped>
.tree-node {
  margin-left: 20px;
}

button {
  margin-right: 8px;
  cursor: pointer;
}
</style>
