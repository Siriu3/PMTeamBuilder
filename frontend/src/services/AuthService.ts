// src/services/AuthService.ts
import axios from 'axios';
import { useAuthStore } from '@/stores/auth'; // Import the store here to use its actions
import router from '@/router'; // Import router if you want to redirect immediately


const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:5000/api';

const instance = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// ... request interceptor ...
// 全局标志，防止多个 401 同时触发刷新
let isRefreshing = false;
let failedQueue: Array<{ resolve: Function; reject: Function; }> = [];

// 将待处理的请求加入队列
const processQueue = (error: any | null, token: string | null = null) => {
  failedQueue.forEach(prom => {
    if (error) {
      prom.reject(error);
    } else {
      prom.resolve(token);
    }
  });
  failedQueue = [];
};

// Response interceptor for handling 401/token expiration
instance.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;
    // 检查是否是 401 错误，并且不是刷新令牌的请求本身，并且没有被标记为已重试
    if (error.response?.status === 401 && !originalRequest._retry) {
      // 标记为已重试，防止无限循环
      originalRequest._retry = true;

      const authStore = useAuthStore(); // 获取 store 实例

      // 如果当前正在刷新，则将当前请求加入队列
      if (isRefreshing) {
        return new Promise(function(resolve, reject) {
          failedQueue.push({ resolve, reject });
        }).then(token => {
          originalRequest.headers.Authorization = `Bearer ${token}`;
          return instance(originalRequest);
        }).catch(err => {
          return Promise.reject(err);
        });
      }

      isRefreshing = true; // 设置标志，表示正在进行令牌刷新

      try {
        console.log('Access token expired or unauthorized, attempting to refresh...');
        await authStore.refreshAuthToken(); // 调用刷新 action
        // 更新原始请求的授权头与新令牌
        originalRequest.headers.Authorization = `Bearer ${authStore.token}`;
        console.log('Token refreshed, retrying original request...');

        // 处理队列中的请求
        processQueue(null, authStore.token);
        return instance(originalRequest); // 使用新令牌重试原始请求

      } catch (refreshError) {
        console.error('Token refresh failed (refresh token might be expired/invalid), forcing logout:', refreshError);
        // 如果刷新失败，执行登出操作
        await authStore.logout();
        // 处理队列中的请求，抛出错误
        processQueue(refreshError);
        // 重定向到登录页面
        router.push('/login');
        return Promise.reject(refreshError); // 重新抛出刷新错误
      } finally {
        isRefreshing = false; // 无论成功失败，重置刷新标志
      }
    }
    // 对于其他错误或已经重试过的 401 请求，直接拒绝
    return Promise.reject(error);
  }
);

const AuthService = {
  async register(userData: any) {
    const response = await instance.post('/auth/register', userData);
    return response.data;
  },

  async login(email: string, password: string) {
    const response = await instance.post('/auth/login', { email, password });
    return response.data;
  },

  async verifyEmail(token: string) {
    const response = await instance.get(`/auth/verify-email?token=${token}`);
    return response.data;
  },

  async resendVerificationEmail(email: string) {
    const response = await instance.post('/auth/resend-verification-email', { email });
    return response.data;
  },

  async refreshAuthToken(refreshToken: string) {
    const response = await instance.post('/auth/refresh', { refresh_token: refreshToken });
    return response.data;
  },

  async getUserProfile() {
    const response = await instance.get('/auth/profile'); // <-- This is the problematic request
    return response.data;
  },

  async updateProfile(profileData: any) {
    const response = await instance.put('/auth/profile', profileData); 
    return response.data;
  },

  async getAdminData() {
    const response = await instance.get('/auth/admin-data');
    return response.data;
  },

};

export default AuthService;