// src/main.ts
// 导入 Vue 的 createApp 函数
import { createApp } from 'vue';
// 导入 Pinia 的 createPinia 函数
import { createPinia } from 'pinia';
// 导入根组件 App
import App from './App.vue';
// 导入 Vue Router 实例
import router from './router';
// 导入 Element Plus 组件库
import ElementPlus from 'element-plus';
import 'element-plus/dist/index.css'; // 导入 Element Plus 样式

// 创建 Vue 应用实例
const app = createApp(App);

app.use(createPinia()); // 安装 Pinia
app.use(router);       // 安装 Vue Router
app.use(ElementPlus);  // 安装 Element Plus

// 将应用挂载到 DOM 元素 #app
app.mount('#app');