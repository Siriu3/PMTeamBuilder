<template>
  <div class="login-view">
    <!-- 登录表单组件 -->
    <LoginForm />
  </div>
</template>

<script setup>
// 导入登录表单组件
import LoginForm from '../components/Auth/LoginForm.vue';
</script>

<style scoped>
/* 登录视图容器样式 */
.login-view {
  display: flex;
  justify-content: center; /* 水平居中 */
  align-items: center; /* 垂直居中 */
  min-height: calc(60vh - 40px); /* 设置最小高度，减去头部高度 */
  margin-top: 100px; /* 顶部外边距 */
}
</style>