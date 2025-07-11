// src/services/UserService.ts
import axios from 'axios';
import { useAuthStore } from '@/stores/auth';
// import { type TeamData } from '@/types';

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

// 定义 ProfileData 接口 (您可以根据实际情况调整字段)
export interface ProfileData {
  id: string | number | null;
  username: string | null;
  email: string | null;
  emailVerified: boolean;
  isAdmin: boolean;
  // [key: string]: any; // 如果有其他未知字段
}

// 定义一个简单的 Moves 数组类型，可以根据实际返回数据结构细化
interface MoveData {
  id: number;
  name: string;
  name_zh: string;
  type: string;
  category: string;
  power: number | null;
  accuracy: number | null;
  pp: number | null;
  desc: string;
  // 添加其他可能的字段
}

const UserService = {
  async getProfile(): Promise<ProfileData> { // 假设返回 ProfileData 类型
    const response = await instance.get('/auth/profile');
    return response.data;
  },

  async updateProfile(profileData: ProfileData): Promise<ProfileData> { // 使用 ProfileData 类型
    const response = await instance.put('/auth/profile', profileData);
    return response.data;
  },

  async getUserTeams(page = 1, perPage = 10, generation: string | null = null, status: string | null = null, format: string | null = null, privacy: boolean | null = null): Promise<any> { // Add privacy parameter
    const params: any = {
      page,
      per_page: perPage
    };

    // Manually add parameters only if they have a value (including false for boolean)
    if (generation !== null) params.generation = generation;
    if (status !== null) params.status = status;
    if (format !== null) params.format = format;

    // Explicitly include is_public parameter only if it's true or false
    if (privacy === true || privacy === false) {
         params.is_public = privacy;
    }

    // Log the params object before sending the request
    // console.log('Axios request params:', params); // Comment out frequent logging

    const response = await instance.get('/team/user', { // Ensure path is correct /api/team/user
      params
    });
    return response.data;
  },

  async getFavoriteTeams(page = 1, perPage = 10): Promise<any> { // 同上
    const response = await instance.get('/team/favorites', { // Ensure path is correct /api/team/favorites
      params: { page, per_page: perPage }
    });
    return response.data;
  },

  async addFavorite(teamId: string): Promise<any> { // teamId 为 string
    const response = await instance.post(`/team/${teamId}/favorite`); // Ensure path is correct /api/team/{id}/favorite
    return response.data;
  },

  async removeFavorite(teamId: string): Promise<any> { // teamId 为 string
    const response = await instance.delete(`/team/${teamId}/favorite`); // Ensure path is correct /api/team/{id}/favorite
    return response.data;
  },

  async createTeam(teamData: any): Promise<any> { // TeamData 已从 @/types 导入
    const response = await instance.post('/team', teamData); // Ensure path is correct /api/team
    return response.data;
  },

  async updateTeam(teamId: string, teamData: Partial<any>): Promise<any> { // teamId 为 string
    const response = await instance.put(`/team/${teamId}`, teamData); // Ensure path is correct /api/team/{id}
    return response.data;
  },

  async deleteTeam(teamId: string): Promise<any> { // teamId 为 string
    const response = await instance.delete(`/team/${teamId}`); // Ensure path is correct /api/team/{id}
    return response.data;
  },

  async getTeamDetails(teamId: string): Promise<any> { // teamId 为 string
    // No change needed here, the backend now handles including token based on user_id
    const response = await instance.get(`/team/${teamId}`); // Ensure path is correct /api/team/{id}
    return response.data;
  },

  async reportTeam(teamId: string, reason: string): Promise<any> { // teamId 和 reason 为 string
    const response = await instance.post(`/team/${teamId}/report`, { reason }); // Ensure path is correct /api/team/{id}/report
    return response.data;
  },

  // Add new method to get team by token
  async getTeamByToken(token: string): Promise<any> {
      try {
          const response = await instance.post('/team/import', { token }); // Ensure path is correct /api/team/import
          return response.data;
      } catch (error) {
           console.error('Error importing team by token:', error);
           throw error; // Re-throw to be handled by calling component
      }
  },

  async getPokemonList(query: string = ''): Promise<any[]> { // query 为 string
    const response = await instance.get('/pokemon', { params: { search: query } });
    return response.data;
  },

  async getPokemonAbilities(pokemonId: number): Promise<any[]> { // pokemonId 为 number
    const response = await instance.get(`/pokemon/${pokemonId}/abilities`);
    return response.data;
  },

  async getPokemonMoves(pokemonId: number): Promise<any[]> { // pokemonId 为 number
    const response = await instance.get(`/pokemon/${pokemonId}/moves`);
    return response.data;
  },

  async getAllPokemon(limit: number = 50, offset: number = 0, generationId?: number | null, searchQuery?: string | null, types?: string): Promise<{ count: number; results: any[] }> {
    try {
      const params: any = { limit, offset };
      if (generationId !== undefined && generationId !== null) { // Check for undefined and null
        params.generation_id = generationId;
      }
      if (searchQuery) {
        params.search_query = searchQuery;
      }
      if (types) {
        params.types = types;
      }
      const response = await instance.get('/pokemon/list', { params });
      return response.data;
    } catch (error) {
      console.error('Error fetching all pokemon:', error);
      throw error;
    }
  },

  async getAllAbilities(generation?: string | number): Promise<any[]> {
    try {
      const params: any = {};
      if (generation) {
        let genId = typeof generation === 'string' && generation.toLowerCase().startsWith('gen ')
                    ? parseInt(generation.split(' ')[1])
                    : generation;
        if (genId) params.generation_id = genId;
      }
      const response = await instance.get('/pokemon/ability/list', { params }); // Ensure path is correct /api/pokemon/ability/list
      return response.data;
    } catch (error) {
      console.error('Error fetching abilities:', error);
      throw error;
    }
  },

  async getAllMoves(generation?: string | number): Promise<any[]> {
    try {
      const params: any = {};
      if (generation) {
        let genId = typeof generation === 'string' && generation.toLowerCase().startsWith('gen ')
                    ? parseInt(generation.split(' ')[1])
                    : generation;
        if (genId) params.generation_id = genId;
      }
      const response = await instance.get('/pokemon/move/list', { params }); // Ensure path is correct /api/pokemon/move/list
      return response.data;
    } catch (error) {
      console.error('Error fetching moves:', error);
      throw error;
    }
  },

  async getAllItems(generation?: string | number, categories?: string[]): Promise<any[]> {
    try {
      const params: any = {};
      if (generation) {
        let genId = typeof generation === 'string' && generation.toLowerCase().startsWith('gen ')
                    ? parseInt(generation.split(' ')[1])
                    : generation;
        if (genId) params.generation_id = genId;
      }
      if (categories && categories.length > 0) {
        params.categories = categories.join(',');
      }
      const response = await instance.get('/pokemon/item/list', { params }); // Ensure path is correct /api/pokemon/item/list
      return response.data;
    } catch (error) {
      console.error('Error fetching items:', error);
      throw error;
    }
  },

  async getLearnableMoves(pokemonSpeciesId: number, versionGroupId: number): Promise<any[]> {
    const response = await instance.get(`/pokemon/learnable-moves/${pokemonSpeciesId}/${versionGroupId}`); // Ensure path is correct
    return response.data;
  },

  // === 新增方法：根据物种ID和世代ID获取可学习招式 ===
  async getLearnableMovesByGeneration(pokemonSpeciesId: number, generationId: number): Promise<MoveData[]> {
    try {
      const response = await instance.get(`/pokemon/learnable-moves-by-generation/${pokemonSpeciesId}/${generationId}`); // Ensure path is correct
      return response.data;
    } catch (error) {
      console.error(`Error fetching learnable moves for species ${pokemonSpeciesId} in generation ${generationId}:`, error);
      throw error;
    }
  },
  // ================================================

  async getPokemonFormAbilities(pokemonFormId: number): Promise<any[]> {
    const response = await instance.get(`/pokemon/form-abilities/${pokemonFormId}`); // Ensure path is correct
    return response.data;
  },

  async getGenerationsWithVersionGroups(): Promise<any[]> {
    const response = await instance.get('/pokemon/generations-with-version-groups'); // Ensure path is correct
    return response.data;
  },

  // updateTeamName and updateTeamTags are now handled by the general updateTeam method
  // async updateTeamName(teamId: string, name: string): Promise<any> { ... }
  // async updateTeamTags(teamId: string, tags: string[]): Promise<any> { ... }

   // Team copy is handled by the backend copy API
   async copyTeam(teamId: string): Promise<any> {
      console.log(`Attempting to copy team with ID: ${teamId}`);
      const response = await instance.post(`/team/${teamId}/copy`); // Ensure path is correct /api/team/{id}/copy
      return response.data;
   },

   async updateTeamPrivacy(teamId: string, isPublic: boolean): Promise<any> {
     console.log(`Attempting to update team ${teamId} privacy to: ${isPublic}`);
     // Using the existing updateTeam API for is_public update
     const response = await instance.put(`/team/${teamId}`, { is_public: isPublic }); // Ensure path is correct /api/team/{id}
     return response.data;
   },

   // --- Start: New methods for Team Square --- // 新增注释行
   async getPublicTeams(page = 1, perPage = 10, searchQuery: string | null = null, generation: string | null = null, format: string | null = null): Promise<any> {
        const params: any = {
            page,
            per_page: perPage
        };
        if (searchQuery) params.search = searchQuery; // 使用 'search' 参数名与后端对应
        if (generation) params.generation = generation;
        if (format) params.format = format;

        const response = await instance.get('/team/public', { params }); // 调用新的公共团队接口
        return response.data;
   },

   async addLike(teamId: string): Promise<any> {
       const response = await instance.post(`/team/${teamId}/like`); // 调用点赞接口
       return response.data;
   },

   async removeLike(teamId: string): Promise<any> {
       const response = await instance.delete(`/team/${teamId}/like`); // 调用取消点赞接口
       return response.data;
   },
   // --- End: New methods for Team Square --- // 新增注释行

};

export default UserService;
