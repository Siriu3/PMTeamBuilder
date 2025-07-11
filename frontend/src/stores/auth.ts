// src/stores/auth.ts
import { defineStore } from 'pinia';
import { ref, computed } from 'vue';
import AuthService from '@/services/AuthService'; // Assuming this path
import router from '@/router'; // Make sure router is imported
import { ElMessage } from 'element-plus'; // Make sure ElMessage is imported
import { jwtDecode } from 'jwt-decode'; // <--- CHANGE: Changed to named import

// Define an interface for the CurrentUser structure
interface CurrentUser {
  id: string | number | null; // JWT 'sub' claim is string, but your mock might use number
  username: string | null;
  email: string | null;
  emailVerified: boolean;
  isAdmin: boolean;
  // Add other relevant user profile fields if needed
}

export const useAuthStore = defineStore('auth', () => {
  // States
  const token = ref(localStorage.getItem('accessToken') || '');
  const refreshToken = ref(localStorage.getItem('refreshToken') || '');
  const tokenExpiry = ref(parseInt(localStorage.getItem('tokenExpiry') || '0'));

  // Initialize currentUser from localStorage or default values
  const initialUsername = localStorage.getItem('username');
  const initialEmail = localStorage.getItem('email');
  const initialEmailVerified = localStorage.getItem('emailVerified') === 'true';
  const initialIsAdmin = localStorage.getItem('is_admin') === 'true';
  const initialUserId = localStorage.getItem('userId');

  const currentUser = ref<CurrentUser | null>(null);

  // Initialize Auth on store creation
  const initializeAuth = () => {
    if (token.value && refreshToken.value && tokenExpiry.value) {
      currentUser.value = {
        id: initialUserId,
        username: initialUsername,
        email: initialEmail,
        emailVerified: initialEmailVerified,
        isAdmin: initialIsAdmin,
      };
      // Optional: Check token expiry and try to refresh here on app load
      // if (Date.now() >= tokenExpiry.value) {
      //   refreshAuthToken().catch(() => logout());
      // }
    } else {
      logout(); // Clear any leftover data if tokens are incomplete or invalid
    }
  };

  // Getters (computed properties)
  const isAuthenticated = computed(() => {
    return !!token.value && Date.now() < tokenExpiry.value;
  });

  // Actions
  const login = async (credentials: { email: string; password: string }) => {
    try {
      const response = await AuthService.login(credentials.email, credentials.password);
      token.value = response.access_token;
      refreshToken.value = response.refresh_token;
      tokenExpiry.value = Date.now() + response.expires_in * 1000;

      // Populate currentUser from login response
      currentUser.value = {
        id: response.user_id || jwtDecode<{ sub: string }>(response.access_token).sub, // Use jwtDecode
        username: response.username,
        email: response.email,
        emailVerified: response.email_verified,
        isAdmin: response.is_admin,
      };

      // Persist to localStorage
      localStorage.setItem('accessToken', token.value);
      localStorage.setItem('refreshToken', refreshToken.value);
      localStorage.setItem('tokenExpiry', tokenExpiry.value.toString());
      localStorage.setItem('userId', currentUser.value.id?.toString() || '');
      localStorage.setItem('username', currentUser.value.username || '');
      localStorage.setItem('email', currentUser.value.email || '');
      localStorage.setItem('emailVerified', currentUser.value.emailVerified.toString());
      localStorage.setItem('is_admin', currentUser.value.isAdmin.toString());


      ElMessage.success('登录成功！');
      router.push('/');
    } catch (error: any) {
      const message = error.response?.data?.message || '登录失败，请检查您的凭据。';
      ElMessage.error(message);
      console.error('Login failed:', error);
      throw error;
    }
  };

  const logout = async () => {
    token.value = '';
    refreshToken.value = '';
    tokenExpiry.value = 0;
    currentUser.value = null;

    localStorage.removeItem('accessToken');
    localStorage.removeItem('refreshToken');
    localStorage.removeItem('tokenExpiry');
    localStorage.removeItem('userId');
    localStorage.removeItem('username');
    localStorage.removeItem('email');
    localStorage.removeItem('emailVerified');
    localStorage.removeItem('is_admin');

    ElMessage.info('您已安全退出。');
    router.push('/login');
  };

  const refreshAuthToken = async () => {
    const storedRefreshToken = localStorage.getItem('refreshToken');
    if (!storedRefreshToken) {
      console.warn('No refresh token available. Cannot refresh.');
      await logout();
      throw new Error('No refresh token available');
    }
    try {
      console.log('Attempting to refresh token...');
      const response = await AuthService.refreshAuthToken(storedRefreshToken);

      token.value = response.access_token;
      refreshToken.value = response.refresh_token;
      tokenExpiry.value = Date.now() + (response.expires_in * 1000);

      localStorage.setItem('accessToken', token.value);
      localStorage.setItem('refreshToken', refreshToken.value);
      localStorage.setItem('tokenExpiry', tokenExpiry.value.toString());

      // Decode the new access token to update currentUser details
      const decodedToken: any = jwtDecode(token.value); // Use jwtDecode
      if (currentUser.value) {
        currentUser.value.id = decodedToken.sub;
        currentUser.value.username = decodedToken.username || currentUser.value.username;
        currentUser.value.email = decodedToken.email || currentUser.value.email;
        currentUser.value.emailVerified = decodedToken.email_verified;
        currentUser.value.isAdmin = decodedToken.is_admin;

        localStorage.setItem('userId', currentUser.value.id?.toString() || '');
        localStorage.setItem('username', currentUser.value.username || '');
        localStorage.setItem('email', currentUser.value.email || '');
        localStorage.setItem('emailVerified', currentUser.value.emailVerified.toString());
        localStorage.setItem('is_admin', currentUser.value.isAdmin.toString());

      } else {
         currentUser.value = {
            id: decodedToken.sub,
            username: decodedToken.username,
            email: decodedToken.email,
            emailVerified: decodedToken.email_verified,
            isAdmin: decodedToken.is_admin,
         };
         localStorage.setItem('userId', currentUser.value.id?.toString() || '');
         localStorage.setItem('username', currentUser.value.username || '');
         localStorage.setItem('email', currentUser.value.email || '');
         localStorage.setItem('emailVerified', currentUser.value.emailVerified.toString());
         localStorage.setItem('is_admin', currentUser.value.isAdmin.toString());
      }

      console.log('Tokens refreshed and currentUser updated successfully.');
      return true;
    } catch (error) {
      console.error('Failed to refresh token, logging out:', error);
      await logout();
      throw error;
    }
  };

  const register = async (userData: any) => {
    try {
      const response = await AuthService.register(userData);
      ElMessage.success(response.message);
      router.push('/login');
      return true;
    } catch (error: any) {
      const message = error.response?.data?.message || '注册失败。';
      ElMessage.error(message);
      console.error('Registration failed:', error);
      throw error;
    }
  };

  // Call initializeAuth on store creation
  initializeAuth();

  return {
    isAuthenticated,
    token,
    refreshToken,
    tokenExpiry,
    currentUser,
    login,
    logout,
    register,
    refreshAuthToken,
  };
});