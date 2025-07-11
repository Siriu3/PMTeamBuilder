<template>
  <div id="app">
    <!-- 主内容区域 -->
    <div class="main-content">
      <!-- 头部导航，在 TeamShare 页面不显示 -->
      <AppHeader v-if="$route.name !== 'TeamShare'" />
      <!-- 路由视图，显示当前路由对应的组件 -->
      <router-view />
    </div>
    <!-- 底部信息，在 TeamShare 页面不显示 -->
    <AppFooter v-if="$route.name !== 'TeamShare'" />
  </div>
</template>

<script setup>
// 导入 AppHeader 组件
import AppHeader from './components/Global/AppHeader.vue';
// 导入 AppFooter 组件
import AppFooter from './components/Global/AppFooter.vue';
</script>

<style>
/* 设置 html 和 body 高度为 100%，移除默认外边距 */
html, body {
  height: 100%; /* 确保 html 和 body 占满全高 */
  margin: 0; /* 移除默认 body 外边距 */
}

/* 设置 body 背景图和样式 */
body {
  background-image: url('/SideBarBg.png');
  background-size: cover;
  background-repeat: no-repeat;
  background-attachment: fixed;
}

/* 全局样式，如果需要 */
#app {
  font-family: Avenir, Helvetica, Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  text-align: center;
  color: #2c3e50;
  display: flex; /* 使用 Flexbox 布局 */
  flex-direction: column; /* 子元素垂直排列 */
  min-height: 100vh; /* 确保 #app 至少占满整个视口高度 */
}

/* 主要内容区域样式，flex-grow: 1 使其占据剩余空间 */
.main-content {
  flex-grow: 1; /* 让主要内容区域占据剩余空间，将页脚推到底部 */
  width: 100%; /* 确保内容区域宽度为100% */
  /* 移除 text-align: center; 以免影响内部元素的对齐 */
  text-align: initial;
}

/* AppHeader 和 router-view 可能需要的样式调整 */
#app > .main-content > * {
  /* 根据需要调整内部元素的样式 */
}
</style>