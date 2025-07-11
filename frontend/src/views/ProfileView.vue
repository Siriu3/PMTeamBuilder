<template>
  <div class="profile-view">
    <!-- 页面标题 -->
    <h1 style="text-align: center;">个人中心</h1>
    <!-- 用户个人资料组件 -->
    <UserProfile />
  </div>
</template>

<script setup>
// 导入用户个人资料组件
import UserProfile from '../components/User/UserProfile.vue';
</script>

<style scoped>
/* 个人中心视图容器样式 */
.profile-view {
  padding: 20px;
  max-width: 800px;
  margin: 0 auto;
}
</style>