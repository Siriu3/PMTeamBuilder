<template>
  <el-menu :default-active="activeIndex" class="el-menu-demo" mode="horizontal" :ellipsis="false" @select="handleSelect" style="background-color: #fcfcfc;">
    <el-menu-item index="" class="title">宝可梦团队构建系统</el-menu-item>
    <div class="flex-grow" />

    <el-alert v-if="authStore.isAuthenticated && authStore.currentUser && !authStore.currentUser.emailVerified"
              title="您的邮箱尚未验证！"
              type="warning"
              show-icon
              :closable="false"
              class="email-verification-alert">
      <el-link type="primary" @click="goToVerifyEmail">立即验证</el-link>
      <el-link type="info" @click="resendVerificationEmail" class="ml-2">重发验证邮件</el-link>
    </el-alert>

    <template v-if="authStore.isAuthenticated">
      <el-menu-item index="team-builder">团队构建</el-menu-item>
      <el-menu-item index="square">团队广场</el-menu-item>
      <el-sub-menu index="user-menu">
        <template #title>
          欢迎, {{ authStore.currentUser?.username || '用户' }}
          <el-badge :value="unreadCount" :hidden="unreadCount === 0" type="danger" class="note" />
        </template>
        <el-menu-item index="profile">
          个人中心
          <el-badge :is-dot="unreadCount > 0" type="danger" class="note-sub" />
        </el-menu-item>
        <el-menu-item index="my-teams">我的团队</el-menu-item>
        <el-menu-item index="favorites">我的收藏</el-menu-item>
        <el-menu-item v-if="authStore.currentUser?.isAdmin" index="admin">管理员面板</el-menu-item>
        <el-menu-item index="logout">登出</el-menu-item>
      </el-sub-menu>

    </template>
    <template v-else>
      <el-menu-item index="login">登录</el-menu-item>
      <el-menu-item index="register" style="margin-right: 30px;">注册</el-menu-item>
    </template>
  </el-menu>
</template>

<script setup lang="ts">
import { ref, onMounted, watch } from 'vue';
import { useRoute, useRouter } from 'vue-router'; // Import useRouter
import { useAuthStore } from '@/stores/auth'; // Import your auth store
import { useNotificationStore } from '@/stores/notification'; // Import notification store
import { ElMessage, ElBadge } from 'element-plus'; // Import ElMessage and ElBadge
import AuthService from '@/services/AuthService'; // Import AuthService
import { storeToRefs } from 'pinia';

const authStore = useAuthStore();
const route = useRoute();
const router = useRouter(); // Initialize router
const notificationStore = useNotificationStore(); // Initialize notification store
const { unreadCount } = storeToRefs(notificationStore); // Get unreadCount state

const activeIndex = ref(route.path); // Use route.path for default-active for better routing integration

// Method to handle menu selection (if you want to manually navigate or trigger actions)
const handleSelect = (key: string) => {
  if (key === 'logout') {
    authStore.logout();
  } else if (key === 'profile') {
    router.push('/profile');
  } else if (key === 'login') {
    router.push('/login');
  } else if (key === 'register') {
    router.push('/register');
  } else if (key === 'home') {
    router.push('/');
  } else if (key === 'team-builder') {
    router.push('/team-builder');
  } else if (key === 'my-teams') {
    router.push('/my-teams');
  } else if (key === 'favorites') {
    router.push('/favorites');
  } else if (key === 'admin') {
    router.push('/admin');
  } else if (key === 'square') {
    router.push('/square');
  } else {
    router.push(`/${key}`); // Generic routing for other menu items if path matches key
  }
};

// Methods for email verification alert
const goToVerifyEmail = () => {
  router.push('/verify-email');
};

const resendVerificationEmail = async () => {
  if (authStore.currentUser?.email) {
    try {
      await AuthService.resendVerificationEmail(authStore.currentUser.email);
      ElMessage.success('新的验证邮件已发送，请检查您的收件箱。');
    } catch (error: any) {
      ElMessage.error(error.response?.data?.message || '重发验证邮件失败。');
    }
  } else {
    ElMessage.warning('无法获取用户邮箱，请尝试重新登录。');
  }
};

onMounted(() => {
  // Fetch unread count when the component is mounted IF already authenticated
  if (authStore.isAuthenticated) {
    notificationStore.fetchUnreadCount();
  }
});

// Watch for changes in authentication status
watch(() => authStore.isAuthenticated, (isAuthenticated) => {
  if (isAuthenticated) {
    notificationStore.fetchUnreadCount();
  }
});

</script>

<style scoped>
.title {
  font-size: 1.25em;
  font-weight: bold;
  margin-left: 30px;
}

.flex-grow {
  flex-grow: 1;
}

.email-verification-alert {
  /* Adjust margin/padding as needed to fit the menu bar */
  margin-left: auto; /* Push to the right */
  margin-right: 20px;
  max-width: 350px; /* Adjust width as needed */
  display: flex;
  align-items: center;
  justify-content: center; /* Center content within alert */
  font-size: 0.85em; /* Smaller font for alert text */
}

/* Ensure links in alert are properly spaced */
.email-verification-alert .el-link {
  margin-left: 8px;
}

.note {
  margin-left: 7px;
  margin-bottom: 37px;
}

.note-sub {
  margin-left: 5px;
  margin-bottom: 25px;
}

/* 自定义左侧标题菜单项的样式 */
.el-menu-item.title {
  background-color: transparent !important; /* 确保默认背景透明 */
  border-bottom-color: transparent !important; /* 确保默认底部边框透明 */
  color: var(--el-menu-text-color) !important; /* 确保默认文本颜色 */
}

/* 移除 hover/focus 特效 */
.el-menu-item.title:hover,
.el-menu-item.title:focus {
  background-color: transparent !important; /* 移除 hover 背景色 */
  color: var(--el-menu-text-color) !important; /* 保持默认文本颜色 */
  border-bottom-color: transparent !important; /* 确保 border 不会显示 */
}

/* 移除选中状态特效 */
.el-menu-item.title.is-active {
  background-color: transparent !important; /* 移除选中背景色 */
  border-bottom-color: transparent !important; /* 移除底部边框颜色 */
  color: var(--el-menu-text-color) !important; /* 确保使用默认文本颜色 */
}

</style>