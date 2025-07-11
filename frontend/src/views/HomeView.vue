<template>
  <div class="home-view">
    <!-- 页面主标题 -->
    <h1>欢迎来到宝可梦团队构建系统！</h1>
    <!-- 页面描述 -->
    <p>在这里，您可以构建、分享和管理您的宝可梦团队。</p>
    <!-- 未登录时显示的按钮组 -->
    <div v-if="!authStore.isAuthenticated" class="button-group">
      <el-button type="primary" @click="router.push('/login')">立即登录</el-button>
      <el-button @click="router.push('/register')">立即注册</el-button>
    </div>
    <!-- 已登录时显示的按钮组 -->
    <div v-else class="button-group">
      <el-button type="primary" @click="router.push('/my-teams')">我的团队</el-button>
      <el-button @click="router.push('/favorites')">我的收藏</el-button>
    </div>
  </div>
</template>

<script setup>
import { useRouter } from 'vue-router';
import { useAuthStore } from '../stores/auth';

// 获取路由实例
const router = useRouter();
// 获取认证 store
const authStore = useAuthStore();
</script>

<style scoped>
/* 首页视图容器样式 */
.home-view {
  display: flex;
  flex-direction: column;
  align-items: center;
  /* justify-content: center; /* 垂直居中可能会导致内容被挤压，改为使用 margin-top */
  padding: 20px;
  margin-top: 80px; /* 添加顶部外边距，将内容向下推 */
}

/* 标题样式 */
.home-view h1 {
  margin-bottom: 20px; /* 标题下方间距 */
  font-size: 2.5em; /* 适当增大标题字号 */
  color: #333; /* 深色标题 */
}

/* 段落样式 */
.home-view p {
  margin-bottom: 40px; /* 段落下方间距 */
  font-size: 1.2em; /* 适当增大段落字号 */
  color: #666; /* 灰色段落 */
  text-align: center; /* 确保文本居中 */
  max-width: 600px; /* 限制段落宽度 */
}

/* 按钮组样式 */
.button-group {
    margin-top: 20px; /* 按钮组上方间距 */
}

/* 按钮样式 */
.button-group .el-button {
    margin: 0 10px; /* 按钮之间添加水平间距 */
}

</style>