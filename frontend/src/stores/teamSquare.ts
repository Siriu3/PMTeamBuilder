import { defineStore } from 'pinia';
import { ref, reactive } from 'vue';
import { ElMessage } from 'element-plus';
import UserService from '@/services/UserService'; // 导入 UserService 来调用 API 方法
import { useUserStore } from '@/stores/user'; // 导入 UserStore 来处理收藏和举报
import { useAuthStore } from '@/stores/auth'; // 导入 AuthStore 来处理认证

// 定义团队列表项的类型（根据后端 /api/team/public 返回的数据结构）
interface PublicTeamItem {
  id: number | string;
  name: string;
  creator_username: string;
  generation: string;
  format: string;
  pokemon_count: number;
  created_at: string;
  favorites_count: number; // 从后端获取收藏数
  likes_count: number;     // 从后端获取点赞数
  is_liked?: boolean;      // 当前用户是否已点赞
  is_favorited?: boolean;  // 当前用户是否已收藏
  pokemons?: { // Assuming pokemons array is included with sprite_url
      name: string;
      sprite_url: string;
  }[];
  token?: string | null; // 添加 token_id 属性
  external_link?: string | null; // Add external_link property
  custom_tags?: string[]; // 添加 custom_tags 属性
}

interface PaginationData {
  total: number;
  page: number;
  per_page: number;
  pages?: number; // 后端返回的总页数
  has_next?: boolean; // 后端返回是否有下一页
}

// 定义世代数据的类型
interface GenerationData {
    id: number;
    name: string; // e.g., generation-ix
    version_groups: { id: number; name: string; }[];
}

export const useTeamSquareStore = defineStore('teamSquare', () => {
  // 状态
  const publicTeams = ref<PublicTeamItem[]>([]);
  const pagination = reactive<PaginationData>({
    total: 0,
    page: 1,
    per_page: 10,
    pages: 0,
    has_next: false,
  });
  const searchQuery = ref('');
  const generationFilter = ref<string | null>(null);
  const formatFilter = ref<string | null>(null);
  const isLoading = ref(false);
  const generations = ref<GenerationData[]>([]); // 新增状态：存储世代列表

  // 操作 (Actions)

  // 新增 action：获取世代列表
  const fetchGenerations = async () => {
      try {
          // 调用 UserService 中的方法获取世代数据
          const response = await UserService.getGenerationsWithVersionGroups();
          // 将获取到的数据存储到 generations 状态中
          generations.value = response;
          console.log('Fetched Generations:', response); // Debug log
      } catch (error: any) {
          console.error('获取世代列表失败:', error);
          // ElMessage.error('获取世代选项失败。'); // 避免频繁提示
      }
  };

  const fetchPublicTeams = async (page = pagination.page, perPage = pagination.per_page) => {
    isLoading.value = true;
    try {
      const response = await UserService.getPublicTeams(
        page,
        perPage,
        searchQuery.value,
        generationFilter.value,
        formatFilter.value
      );

      publicTeams.value = response.items || [];
      pagination.total = response.total || 0;
      pagination.page = response.page || page;
      pagination.per_page = response.per_page || perPage;
      pagination.pages = response.pages || 0;
      pagination.has_next = response.has_next || false;

      // ElMessage.success('公开团队列表加载成功！'); // 可能过于频繁，按需显示
    } catch (error: any) {
      console.error('获取公开团队列表失败:', error);
      ElMessage.error(error.response?.data?.message || '获取公开团队列表失败。');
    } finally {
      isLoading.value = false;
    }
  };

  const handlePageChange = (newPage: number) => {
    pagination.page = newPage;
    fetchPublicTeams(newPage); // 触发加载新页数据
  };

  const handleSearch = (query: string) => {
    searchQuery.value = query;
    pagination.page = 1; // 搜索时重置回第一页
    fetchPublicTeams(1); // 触发搜索
  };

  const handleFilter = (generation: string | null, format: string | null) => {
      generationFilter.value = generation;
      formatFilter.value = format;
      pagination.page = 1; // 筛选时重置回第一页
      fetchPublicTeams(1); // 触发筛选
  };

  const handleLike = async (teamId: number | string) => {
      const authStore = useAuthStore(); // 获取 authStore 实例

      // 使用 authStore 的认证状态判断用户是否登录
      if (!authStore.isAuthenticated) {
           ElMessage.warning('请登录后进行点赞操作。');
           return;
      }

      const teamIndex = publicTeams.value.findIndex(team => team.id === teamId);
      if (teamIndex === -1) return; // Team not found in current list

      const team = publicTeams.value[teamIndex];
      const originalIsLiked = team.is_liked;
      const originalLikesCount = team.likes_count;

      // Optimistic update
      team.is_liked = !originalIsLiked;
      team.likes_count = (team.likes_count || 0) + (originalIsLiked ? -1 : 1);
      team.likes_count = Math.max(0, team.likes_count); // Ensure count doesn't go below zero

      try {
          // Use UserService directly for API call
          if (originalIsLiked) {
               await UserService.removeLike(teamId as string); // 转换为 string
          } else {
               await UserService.addLike(teamId as string); // 转换为 string
          }
           // Optional: Fetch list again or show success message only if needed
           // ElMessage.success(originalIsLiked ? '取消点赞成功！' : '点赞成功！');

      } catch (error: any) {
          console.error('点赞/取消点赞失败:', error);
          console.error('点赞/取消点赞失败 Error Details:', error.response || error.message || error); // Added detailed error log
          ElMessage.error(error.response?.data?.message || '点赞操作失败。');
          // Revert state on error
          team.is_liked = originalIsLiked;
          team.likes_count = originalLikesCount;
      }
  };

  const handleFavorite = async (teamId: number | string) => {
      console.log('handleFavorite called for teamId:', teamId);
      const userStore = useUserStore();
      const authStore = useAuthStore();
      console.log('Auth isAuthenticated:', authStore.isAuthenticated);
      console.log('Auth currentUser:', authStore.currentUser);
      // console.log('User currentUser (in TeamSquareStore):', userStore.currentUser); // 移除此行日志


      if (!authStore.isAuthenticated) { // 使用 authStore 的认证状态
           ElMessage.warning('请登录后进行收藏操作。');
           return;
      }

      const teamIndex = publicTeams.value.findIndex(team => team.id === teamId);
      if (teamIndex === -1) return;

      const team = publicTeams.value[teamIndex];
      const originalIsFavorited = team.is_favorited;
      const originalFavoritesCount = team.favorites_count;

      // Optimistic update
      team.is_favorited = !originalIsFavorited;
      team.favorites_count = (team.favorites_count || 0) + (originalIsFavorited ? -1 : 1);
      team.favorites_count = Math.max(0, team.favorites_count); // Ensure count doesn't go below zero

      try {
          // userStore actions show ElMessage
          // Call userStore actions directly
          if (originalIsFavorited) {
               await userStore.removeFavorite(teamId as string);
          } else {
               await userStore.addFavorite(teamId as string);
          }

      } catch (error: any) {
          console.error('收藏/取消收藏失败:', error);
          console.error('收藏/取消收藏失败 Error Details:', error.response || error.message || error); // Added detailed error log
          ElMessage.error(error.response?.data?.message || '收藏操作失败。');
          // Revert state on error
          team.is_favorited = originalIsFavorited;
          // 修正收藏数回滚错误
          team.favorites_count = originalFavoritesCount; // Changed from likes_count
      }
      // Note: isLoading is typically managed at the view or individual action level for optimistic updates
  };

  const handleReport = async (teamId: number | string, reason: string) => {
       console.log('handleReport called for teamId:', teamId, 'reason:', reason);
       const userStore = useUserStore();
       const authStore = useAuthStore();
       console.log('Auth isAuthenticated:', authStore.isAuthenticated);
       console.log('Auth currentUser:', authStore.currentUser);
       // console.log('User currentUser (in TeamSquareStore):', userStore.currentUser); // 移除此行日志


       if (!authStore.isAuthenticated) { // 使用 authStore 的认证状态
            ElMessage.warning('请登录后进行举报操作。');
            return false;
       }

       try {
            isLoading.value = true;
            // Calling reportTeam from UserService
            await UserService.reportTeam(teamId as string, reason); // 转换为 string
            ElMessage.success('举报已提交，感谢您的反馈！');
            return true;
       } catch (error: any) {
            console.error('提交举报失败:', error);
            console.error('提交举报失败 Error Details:', error.response || error.message || error); // Added detailed error log
            ElMessage.error(error.response?.data?.message || '提交举报失败。');
            return false;
       } finally {
            isLoading.value = false;
       }
  };

  return {
    publicTeams,
    pagination,
    searchQuery,
    generationFilter,
    formatFilter,
    isLoading,
    generations, // 暴露 generations 状态
    fetchPublicTeams,
    handlePageChange,
    handleSearch,
    handleFilter,
    handleLike,
    handleFavorite,
    handleReport,
    fetchGenerations, // 暴露 fetchGenerations action
  };
}); 