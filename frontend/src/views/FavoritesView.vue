<template>
  <div class="favorites-view">
    <!-- 页面标题 -->
    <h1 style="text-align: center; margin-bottom: 50px;">我的收藏</h1>
    <!-- 用户收藏列表组件 -->
    <UserFavoriteList />
  </div>
</template>

<script setup>
// 导入用户收藏列表组件
import UserFavoriteList from '../components/User/UserFavoriteList.vue';
</script>

<style scoped>
/* 我的收藏视图容器样式 */
.favorites-view {
  padding: 20px;
  max-width: 1200px;
  margin: 0 auto;
}
</style>