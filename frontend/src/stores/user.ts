// src/stores/user.ts
import { defineStore } from 'pinia';
import { ref, computed, reactive } from 'vue';
import UserService, { type ProfileData } from '@/services/UserService';
import { ElMessage } from 'element-plus';
import { useAuthStore } from '@/stores/auth';

interface PaginationData {
  total: number;
  page: number;
  per_page: number;
  total_pages?: number; // Make optional or ensure it's always included
}

// 定义用户信息的类型（根据后端返回的数据结构）
// Note: Using ProfileData from UserService for consistency
// interface UserInfo {
//   id: number;
//   username: string;
//   email: string;
//   is_admin: boolean; // Assuming the backend returns this
//   // 其他可能需要的字段
// }

export const useUserStore = defineStore('user', () => {
  // 状态
  // Using ProfileData type for currentUser
  const currentUser = ref<ProfileData | null>(null); 
  const userLoading = ref(false); // New loading state for user operations
  const userTeams = ref<any[]>([]);     // 用户创建的团队列表
  const favoriteTeams = ref<any[]>([]); // 用户收藏的团队列表
  const userTeamsPagination = ref<PaginationData>({ total: 0, page: 1, per_page: 10 }); // Explicitly type
  const favoriteTeamsPagination = ref<PaginationData>({ total: 0, page: 1, per_page: 10 }); // Explicitly type
  const isLoading = ref(false);  // 加载状态

  // 操作
  const fetchCurrentUser = async () => {
    // Check if user data already exists to avoid unnecessary requests
    if (currentUser.value) {
      return currentUser.value;
    }

    userLoading.value = true;
    try {
      // Attempt to fetch current user data from backend (requires JWT)
      // Use UserService.getProfile() as per available methods
      const response = await UserService.getProfile(); 
      currentUser.value = response; // Assuming response is the user object
      return response;
    } catch (error: any) {
        // Log out if token is invalid or user not found
        console.error('Failed to fetch current user profile:', error);
        // Optionally clear local storage token and state if error indicates invalid token
        // if (error.response && (error.response.status === 401 || error.response.status === 404)) {
        //      logout(); // Implement a logout action that clears token and state
        // }
        currentUser.value = null; // Ensure state is clear if fetch fails
        return null;
    } finally {
       userLoading.value = false;
    }
  };

  const setUser = (user: ProfileData | null) => {
    currentUser.value = user;
  };

  const logout = () => {
      // Clear user state and potentially remove JWT from local storage/cookies
      currentUser.value = null;
      // TODO: Call logout API if necessary and clear JWT from storage
      ElMessage.success('您已成功退出登录。');
  };

  const fetchUserProfile = async () => {
    try {
      isLoading.value = true;
      const authStore = useAuthStore();
      
      // 如果已经在auth store中有用户信息，则直接使用
      if (authStore.currentUser) {
        // authStore.currentUser should now match ProfileData structure
        currentUser.value = authStore.currentUser; // Directly assign
        return true;
      }
      
      // 否则从API获取
      const response = await UserService.getProfile(); // response is ProfileData
      currentUser.value = response; // Directly assign
      
      ElMessage.success('用户资料加载成功！');
      return true;
    } catch (error: any) { // Add type annotation
      console.error('获取用户资料失败:', error);
      ElMessage.error(error.response?.data?.message || '获取用户资料失败。');
      return false;
    } finally {
      isLoading.value = false;
    }
  };

  const updateUserProfile = async (profileData: ProfileData) => { // Add type annotation
    try {
      isLoading.value = true;
      const response = await UserService.updateProfile(profileData); // response is ProfileData
      currentUser.value = response; // Directly assign
      
      // 同步更新auth store中的用户信息
      const authStore = useAuthStore();
      if (authStore.currentUser) {
        authStore.currentUser = response; // Directly assign
      }
      
      ElMessage.success('用户资料更新成功！');
      return true;
    } catch (error: any) { // Add type annotation
      console.error('更新用户资料失败:', error);
      ElMessage.error(error.response?.data?.message || '更新用户资料失败。');
      return false;
    } finally {
      isLoading.value = false;
    }
  };

  const fetchUserTeams = async (page = 1, perPage = 10, generation: string | null = null, status: string | null = null, format: string | null = null, privacy: boolean | null = null) => {
    try {
      isLoading.value = true;
      const response = await UserService.getUserTeams(page, perPage, generation, status, format, privacy);
      
      userTeams.value = response.items || [];
      userTeamsPagination.value = {
        total: response.total || 0,
        page: response.page || page,
        per_page: response.per_page || perPage,
        total_pages: response.pages || Math.ceil((response.total || 0) / perPage)
      };
      
      return true;
    } catch (error: any) { // Add type annotation
      console.error('获取用户团队列表失败:', error);
      ElMessage.error(error.response?.data?.message || '获取用户团队列表失败。');
      return false;
    } finally {
      isLoading.value = false;
    }
  };

  const fetchFavoriteTeams = async (page = 1, perPage = 10) => {
    try {
      isLoading.value = true;
      const response = await UserService.getFavoriteTeams(page, perPage);
      
      favoriteTeams.value = response.items || [];
      favoriteTeamsPagination.value = {
        total: response.total || 0,
        page: response.page || page,
        per_page: response.per_page || perPage,
        total_pages: response.pages || Math.ceil((response.total || 0) / perPage)
      };
      
      return true;
    } catch (error: any) { // Add type annotation
      console.error('获取收藏团队列表失败:', error);
      ElMessage.error(error.response?.data?.message || '获取收藏团队列表失败。');
      return false;
    } finally {
      isLoading.value = false;
    }
  };

  const addFavorite = async (teamId: string): Promise<boolean> => {
    const authStore = useAuthStore();
    if (!authStore.isAuthenticated) {
        ElMessage.warning('请登录后进行收藏操作。');
        return false;
    }
    try {
         // Call the UserService method to add favorite
        const response = await UserService.addFavorite(teamId);
        // Optionally update the team's favorite count in the store or refetch the list
        // For optimistic update in TeamSquareStore, we just need to signal success
        ElMessage.success('收藏成功！');
        return true;
    } catch (error: any) {
        console.error('添加收藏失败:', error);
        ElMessage.error(error.response?.data?.message || '添加收藏失败。');
        return false;
    }
  };

  const removeFavorite = async (teamId: string): Promise<boolean> => {
    const authStore = useAuthStore();
    if (!authStore.isAuthenticated) {
        ElMessage.warning('请登录后进行取消收藏操作。');
        return false;
    }
    try {
        // Call the UserService method to remove favorite
        const response = await UserService.removeFavorite(teamId);
        // Optionally update the team's favorite count in the store or refetch the list
        // For optimistic update in TeamSquareStore, we just need to signal success
        ElMessage.success('取消收藏成功！');
        return true;
    } catch (error: any) {
         console.error('取消收藏失败:', error);
         ElMessage.error(error.response?.data?.message || '取消收藏失败。');
         return false;
    }
  };

  return {
    currentUser,
    isAuthenticated: computed(() => useAuthStore().isAuthenticated),
    userLoading,
    userTeams,
    favoriteTeams,
    userTeamsPagination,
    favoriteTeamsPagination,
    isLoading,
    fetchCurrentUser,
    setUser,
    logout,
    fetchUserProfile,
    updateUserProfile,
    fetchUserTeams,
    fetchFavoriteTeams,
    addFavorite,
    removeFavorite
  };
});
