// src/services/AdminService.ts
import axios from 'axios';
import { useAuthStore } from '@/stores/auth';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:5000/api';

// 创建axios实例，复用AuthService中的配置
const instance = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// 请求拦截器，添加认证令牌
instance.interceptors.request.use(
  (config) => {
    const authStore = useAuthStore();
    if (authStore.token) {
      config.headers.Authorization = `Bearer ${authStore.token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

const AdminService = {
  async getTeamsForReview(page = 1, perPage = 10) {
    const response = await instance.get('/admin/teams/pending', {
      params: { page, per_page: perPage }
    });
    return response.data;
  },

  async reviewTeam(teamId, approved, reason) {
    const response = await instance.post(`/admin/teams/${teamId}/review`, {
      approved,
      reason
    });
    return response.data;
  },

  async getReports(page = 1, perPage = 10) {
    const response = await instance.get('/admin/reports/pending', {
      params: { page, per_page: perPage }
    });
    return response.data;
  },

  async handleReport(reportId, action, note) {
    const response = await instance.post(`/admin/reports/${reportId}/resolve`, {
      action,
      note
    });
    return response.data;
  },

  async getReportHistory(page = 1, perPage = 10) {
    const response = await instance.get('/admin/reports/history', {
      params: { page, per_page: perPage }
    });
    return response.data;
  },

  async getSensitiveWords(page = 1, perPage = 20) {
    const response = await instance.get('/admin/sensitive-words', {
      params: { page, per_page: perPage }
    });
    return response.data;
  },

  async addSensitiveWord(content) {
    const response = await instance.post('/admin/sensitive-words', { content });
    return response.data;
  },

  async removeSensitiveWord(wordId) {
    const response = await instance.delete(`/admin/sensitive-words/${wordId}`);
    return response.data;
  },

  async refreshSensitiveWordCache() {
    const response = await instance.post('/admin/sensitive-words/refresh-cache');
    return response.data;
  },

  async getUsers(page = 1, perPage = 10) {
    const response = await instance.get('/admin/users', {
      params: { page, per_page: perPage }
    });
    return response.data;
  },

  async updateUserAdminStatus(userId, isAdmin) {
    const response = await instance.put(`/admin/users/${userId}/admin-status`, {
      is_admin: isAdmin
    });
    return response.data;
  },

  async deleteUser(userId) {
    const response = await instance.delete(`/admin/users/${userId}`);
    return response.data;
  }
};

export default AdminService;
