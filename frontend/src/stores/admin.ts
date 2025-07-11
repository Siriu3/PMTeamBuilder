// src/stores/admin.ts
import { defineStore } from 'pinia';
import { ref } from 'vue';
import { ElMessage } from 'element-plus';
import AdminService from '@/services/AdminService';

// 定义团队和举报的类型接口（根据后端返回的数据结构）
interface TeamForReview {
  id: number | string; // 假设id是数字或字符串
  name: string;
  creator_username?: string; // 添加可选的提交者用户名
  generation: string;
  format: string;
  pokemon_count: number;
  created_at: string;
  review_status: 'pending' | 'approved' | 'rejected';
  review_comment?: string | null;
  custom_tags?: string[]; // 添加可选的自定义词条
  pokemons?: any[]; // 宝可梦列表，可以进一步细化类型
}

interface Report {
  id: number | string; // 假设id是数字或字符串
  // 添加举报相关的其他字段
  reported_team_id?: number | string;
  reason: string;
  status: string; // 例如: 'pending', 'resolved', 'ignored'
  created_at: string;
  handler_username?: string; // 处理人用户名
}

// 定义敏感词的类型接口
interface SensitiveWord {
  id: number | string; // 假设id是数字或字符串
  content: string;
  // 添加其他可能的字段，例如 created_at, created_by
}

export const useAdminStore = defineStore('admin', () => {
  // 状态
  const teamsForReview = ref<TeamForReview[]>([]);   // 待审核团队列表
  const reports = ref<Report[]>([]);          // 举报信息列表
  const sensitiveWords = ref<SensitiveWord[]>([]);   // 敏感词列表
  const teamsForReviewPagination = ref({ total: 0, page: 1, per_page: 10 });
  const reportsPagination = ref({ total: 0, page: 1, per_page: 10 });
  const sensitiveWordsPagination = ref({ total: 0, page: 1, per_page: 20 });
  const isLoading = ref(false);     // 加载状态

  // 操作
  const fetchTeamsForReview = async (page = 1, perPage = 10) => {
    try {
      isLoading.value = true;
      const response = await AdminService.getTeamsForReview(page, perPage);
      
      teamsForReview.value = response.items || [];
      teamsForReviewPagination.value = {
        total: response.total || 0,
        page: response.page || page,
        per_page: response.per_page || perPage,
      };
      
      ElMessage.success('待审核团队列表加载成功！');
      return true;
    } catch (error: any) {
      console.error('获取待审核团队失败:', error);
      ElMessage.error(error.response?.data?.message || '获取待审核团队失败。');
      return false;
    } finally {
      isLoading.value = false;
    }
  };

  const reviewTeam = async (teamId: number | string, decision: 'approve' | 'reject', reason?: string | null) => {
    try {
      isLoading.value = true;
      const isApproved = decision === 'approve';
      await AdminService.reviewTeam(teamId, isApproved, reason);
      
      // 更新本地状态，移除已审核的团队
      teamsForReview.value = teamsForReview.value.filter((team: TeamForReview) => team.id !== teamId);
      teamsForReviewPagination.value.total--;
      
      ElMessage.success(`团队审核${isApproved ? '通过' : '拒绝'}成功！`);
      return true;
    } catch (error: any) {
      console.error('审核团队失败:', error);
      ElMessage.error(error.response?.data?.message || '审核团队失败。');
      return false;
    } finally {
      isLoading.value = false;
    }
  };

  const fetchReports = async (page = 1, perPage = 10) => {
    try {
      isLoading.value = true;
      const response = await AdminService.getReports(page, perPage);
      
      reports.value = response.items || [];
      reportsPagination.value = {
        total: response.total || 0,
        page: response.page || page,
        per_page: response.per_page || perPage,
      };
      
      ElMessage.success('举报列表加载成功！');
      return true;
    } catch (error: any) {
      console.error('获取举报列表失败:', error);
      ElMessage.error(error.response?.data?.message || '获取举报列表失败。利用 error.response?.data?.message 获取后端错误信息');
      return false;
    } finally {
      isLoading.value = false;
    }
  };

  const handleReport = async (reportId: number | string, action: string, note?: string | null) => {
    try {
      isLoading.value = true;
      await AdminService.handleReport(reportId, action, note);
      
      // 更新本地状态，移除已处理的举报
      reports.value = reports.value.filter((report: Report) => report.id !== reportId);
      reportsPagination.value.total--;
      
      ElMessage.success('举报处理成功！');
      return true;
    } catch (error: any) {
      console.error('处理举报失败:', error);
      ElMessage.error(error.response?.data?.message || '处理举报失败。');
      return false;
    } finally {
      isLoading.value = false;
    }
  };

  const fetchSensitiveWords = async (page = 1, perPage = 20) => {
    try {
      isLoading.value = true;
      const response = await AdminService.getSensitiveWords(page, perPage);
      
      sensitiveWords.value = response.items || [];
      sensitiveWordsPagination.value = {
        total: response.total || 0,
        page: response.page || page,
        per_page: response.per_page || perPage,
      };
      
      ElMessage.success('敏感词列表加载成功！');
      return true;
    } catch (error: any) {
      console.error('获取敏感词列表失败:', error);
      ElMessage.error(error.response?.data?.message || '获取敏感词列表失败。');
      return false;
    } finally {
      isLoading.value = false;
    }
  };

  const addSensitiveWord = async (content: string) => {
    try {
      isLoading.value = true;
      const response = await AdminService.addSensitiveWord(content);
      
      // 如果当前页面未满，添加到当前列表
      if (sensitiveWords.value.length < sensitiveWordsPagination.value.per_page) {
        sensitiveWords.value.push(response.word);
      }
      sensitiveWordsPagination.value.total++;
      
      ElMessage.success('敏感词添加成功！');
      return true;
    } catch (error: any) {
      console.error('添加敏感词失败:', error);
      ElMessage.error(error.response?.data?.message || '添加敏感词失败，可能已存在。');
      return false;
    } finally {
      isLoading.value = false;
    }
  };

  const removeSensitiveWord = async (wordId: number | string) => {
    try {
      isLoading.value = true;
      await AdminService.removeSensitiveWord(wordId);
      
      // 更新本地状态
      sensitiveWords.value = sensitiveWords.value.filter((word: SensitiveWord) => word.id !== wordId);
      sensitiveWordsPagination.value.total--;
      
      ElMessage.success('敏感词删除成功！');
      return true;
    } catch (error: any) {
      console.error('删除敏感词失败:', error);
      ElMessage.error(error.response?.data?.message || '删除敏感词失败。');
      return false;
    } finally {
      isLoading.value = false;
    }
  };

  const refreshSensitiveWordCache = async () => {
    try {
      isLoading.value = true;
      const response = await AdminService.refreshSensitiveWordCache();
      
      ElMessage.success(`敏感词缓存已刷新！共 ${response.count} 个词条。`);
      return true;
    } catch (error: any) {
      console.error('刷新敏感词缓存失败:', error);
      ElMessage.error(error.response?.data?.message || '刷新敏感词缓存失败。');
      return false;
    } finally {
      isLoading.value = false;
    }
  };

  return {
    teamsForReview,
    reports,
    sensitiveWords,
    teamsForReviewPagination,
    reportsPagination,
    sensitiveWordsPagination,
    isLoading,
    fetchTeamsForReview,
    reviewTeam,
    fetchReports,
    handleReport,
    fetchSensitiveWords,
    addSensitiveWord,
    removeSensitiveWord,
    refreshSensitiveWordCache
  };
});
