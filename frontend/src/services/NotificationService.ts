// frontend/src/services/NotificationService.ts
// 导入 axios 库用于 HTTP 请求
import axios from 'axios';
// 导入认证相关的 Pinia store
import { useAuthStore } from '@/stores/auth';

// 从环境变量获取 API 基础 URL，如果不存在则使用默认值
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:5000/api';

// 创建 axios 实例，配置基础 URL 和默认请求头
const instance = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// 请求拦截器：在发送请求前检查是否存在认证 token，并将其添加到 Authorization 头部
instance.interceptors.request.use(
  (config) => {
    const authStore = useAuthStore();
    if (authStore.token) {
      // 如果存在 token，添加到 Bearer 认证头部
      config.headers.Authorization = `Bearer ${authStore.token}`;
    }
    return config; // 返回修改后的配置
  },
  (error) => {
    // 处理请求错误
    return Promise.reject(error);
  }
);

// 通知服务对象，包含各种通知相关的 API 调用方法
const NotificationService = {

  // 异步函数：获取用户的通知列表
  async getUserNotifications(page = 1, perPage = 10, isRead: boolean | null = null) {
    // 构建请求参数对象
    const params: any = { page, per_page: perPage };
    // 如果指定了 isRead 状态，则添加到参数中 (后端期望 'true' 或 'false' 字符串)
    if (isRead !== null) {
      params.is_read = isRead ? 'true' : 'false'; 
    }
    // 发送 GET 请求获取通知列表
    const response = await instance.get('/notifications', { params });
    return response.data; // 返回响应数据
  },

  // 异步函数：将指定 ID 的通知标记为已读
  async markNotificationAsRead(notificationId: number | string) {
    // 发送 PUT 请求到标记已读的 API 路径
    const response = await instance.put(`/notifications/${notificationId}/mark-read`);
    return response.data; // 返回响应数据
  },

  // 异步函数：获取未读通知数量
  async getUnreadCount() {
    // 发送 GET 请求获取未读数量
    const response = await instance.get('/notifications/unread_count');
    // 返回未读数量 (假设后端返回 { unread_count: number })
    return response.data.unread_count;
  },

  // 异步函数：将所有通知标记为已读
  async markAllNotificationsAsRead() {
    // 发送 POST 请求到标记全部已读的 API 路径
    const response = await instance.post('/notifications/mark_all_read');
    return response.data; // 返回响应数据
  }
};

// 导出 NotificationService 对象
export default NotificationService; 