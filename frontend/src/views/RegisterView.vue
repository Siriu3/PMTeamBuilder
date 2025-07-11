<template>
  <div class="register-view">
    <!-- 注册表单组件 -->
    <RegisterForm />
  </div>
</template>

<script setup>
// 导入注册表单组件
import RegisterForm from '../components/Auth/RegisterForm.vue';
</script>

<style scoped>
/* 注册视图容器样式 */
.register-view {
  display: flex;
  justify-content: center; /* 水平居中 */
  align-items: center; /* 垂直居中 */
  min-height: calc(60vh - 40px); /* 设置最小高度，减去头部高度 */
  margin-top: 100px; /* 顶部外边距 */
}
</style>