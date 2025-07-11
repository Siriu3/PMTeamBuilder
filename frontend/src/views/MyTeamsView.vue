<template>
  <div class="my-teams-view">
    <!-- 页面标题 -->
    <h1 style="text-align: center; margin-bottom: 50px;">我的团队</h1>
    <!-- 用户团队列表组件 -->
    <UserTeamList />
    <el-divider />
  </div>
</template>

<script setup>
// 导入用户团队列表组件
import UserTeamList from '../components/User/UserTeamList.vue';
</script>

<style scoped>
/* 我的团队视图容器样式 */
.my-teams-view {
  padding: 20px;
  max-width: 1200px;
  margin: 0 auto;
}
</style>