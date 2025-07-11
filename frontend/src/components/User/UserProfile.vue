<template>
  <el-container class="user-profile-container">
    <el-card class="box-card">
      <el-tabs v-model="activeTab" class="profile-tabs">
        <el-tab-pane label="个人资料" name="profile">
          <template #label>
            <span class="tab-label-content">个人资料</span>
          </template>
          <div class="profile-content">
            <el-button v-if="!isEditMode" @click="toggleEditMode" type="primary" :icon="Edit" circle style="position: absolute; top: 20px; right: 20px; z-index: 10;"></el-button>
            <el-form :model="userProfile" label-width="120px" :rules="profileRules" ref="profileFormRef">
              <el-form-item label="用户名" prop="username">
                <el-input v-model="userProfile.username" :disabled="!isEditMode" class="profile-input"></el-input>
              </el-form-item>

              <el-form-item label="邮箱" prop="email">
                <el-input v-model="userProfile.email" disabled class="profile-input"></el-input> </el-form-item>

              <el-form-item label="邮箱已验证">
                <el-tag :type="userProfile.email_verified ? 'success' : 'danger'">
                  {{ userProfile.email_verified ? '是' : '否' }}
                </el-tag>
                <el-button v-if="!userProfile.email_verified" type="text" @click="resendVerification" style="margin-left: 10px;">
                  重发验证邮件
                </el-button>
              </el-form-item>
              
              <div class="save-buttons-item" v-if="isEditMode">
                <el-button @click="cancelEdit" style="margin-left: 10px;">取消</el-button>
                <el-button type="primary" @click="saveProfile">保存</el-button>
              </div>
            </el-form>

            <el-skeleton v-if="loading" :rows="5" animated />
            <el-alert v-if="errorMessage" :title="errorMessage" type="error" show-icon />
          </div>
        </el-tab-pane>
        <el-tab-pane label="我的通知" name="notifications">
          <template #label>
            <span class="tab-label-content">我的通知 <el-badge v-if="notificationStore.unreadCount > 0" :value="notificationStore.unreadCount" class="item" type="danger" style="margin-top: 4px;" /></span>
          </template>
          <div class="notification-content">
            <!-- NotificationPage.vue Template Content -->
            <el-card class="notification-card" shadow="never" v-loading="notificationStore.isLoading">
              <template #header>
                <div class="card-header">
                  <span>通知列表</span>
                  <el-select v-model="filterIsRead" placeholder="筛选已读状态" style="width: 120px; margin-right: 10px;" @change="fetchNotificationsByFilter">
                    <el-option label="全部" :value="'all'" />
                    <el-option label="未读" :value="false" />
                    <el-option label="已读" :value="true" />
                  </el-select>
                  <!-- Add Mark All as Read button -->
                  <el-button type="info" size="small" @click="handleMarkAllAsRead" :disabled="notificationStore.unreadCount === 0">
                      一键已读
                  </el-button>
                </div>
              </template>

              <el-table :data="notificationStore.notifications" style="width: 100%" v-if="notificationStore.notifications.length > 0">
                <el-table-column prop="created_at" label="时间" width="180">
                  <template #default="scope">
                    {{ new Date(scope.row.created_at).toLocaleString() }}
                  </template>
                </el-table-column>
                <el-table-column prop="content" label="内容" />
                <el-table-column prop="is_read" label="状态" width="100">
                  <template #default="scope">
                    <el-tag :type="scope.row.is_read ? 'success' : 'info'">
                      {{ scope.row.is_read ? '已读' : '未读' }}
                    </el-tag>
                  </template>
                </el-table-column>
                <el-table-column label="操作" width="100">
                  <template #default="scope">
                    <el-button
                      size="small"
                      :type="scope.row.is_read ? 'info' : 'primary'"
                      @click="markAsRead(scope.row.id)"
                      :disabled="scope.row.is_read"
                    >
                      标记已读
                    </el-button>
                  </template>
                </el-table-column>
              </el-table>
              <el-empty v-else description="暂无通知。"></el-empty>

              <div class="pagination-container" v-if="notificationStore.pagination.total > notificationStore.pagination.per_page">
                <el-pagination
                  background
                  layout="prev, pager, next"
                  :total="notificationStore.pagination.total"
                  :page-size="notificationStore.pagination.per_page"
                  v-model:current-page="notificationCurrentPage"
                  @current-change="handleNotificationPageChange"
                />
              </div>
            </el-card>
          </div>
        </el-tab-pane>
        <!-- Add other profile related tabs here later if needed -->
      </el-tabs>
    </el-card>
  </el-container>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue';
import { ElMessage, ElLoading, ElForm, ElFormItem, ElInput, ElSwitch, ElTag, ElButton, ElLink, ElCard, ElAlert, ElSkeleton, ElTabs, ElTabPane, ElBadge, ElTable, ElTableColumn, ElSelect, ElOption, ElPagination, ElEmpty } from 'element-plus';
import { Edit } from '@element-plus/icons-vue';
import type { FormInstance, FormRules } from 'element-plus';
import AuthService from '@/services/AuthService';
import { useAuthStore } from '@/stores/auth';
import { useNotificationStore } from '@/stores/notification';
import { useRouter } from 'vue-router';

const authStore = useAuthStore();
const notificationStore = useNotificationStore();
const router = useRouter();

// Active tab state
const activeTab = ref('profile');

// Form reference, for validation
const profileFormRef = ref<FormInstance>();

// User profile model
const userProfile = reactive({
  username: '',
  email: '',
  is_admin: false,
  email_verified: false,
});

// Initial user profile copy, for canceling edits
let originalUserProfile = { ...userProfile };

// Edit mode switch
const isEditMode = ref(false);
const loading = ref(false);
const errorMessage = ref('');

// Notification related state and methods
const notificationCurrentPage = ref(1);
const filterIsRead = ref<any>('all');

const fetchNotificationsByFilter = () => {
  notificationCurrentPage.value = 1;
  const statusFilter = filterIsRead.value === 'all' ? null : filterIsRead.value;
  notificationStore.fetchNotifications(notificationCurrentPage.value, notificationStore.pagination.per_page, statusFilter);
};

const handleNotificationPageChange = (page: number) => {
  notificationCurrentPage.value = page;
   const statusFilter = filterIsRead.value === 'all' ? null : filterIsRead.value;
  notificationStore.fetchNotifications(notificationCurrentPage.value, notificationStore.pagination.per_page, statusFilter);
};

const markAsRead = async (notificationId: number | string) => {
  await notificationStore.markNotificationAsRead(notificationId);
  // 在标记已读成功后重新获取未读数量
  notificationStore.fetchUnreadCount();
  // ... other optional refresh logic ...
};

// New method to handle Mark All as Read button click
const handleMarkAllAsRead = async () => {
  await notificationStore.markAllAsRead();
  // 在一键已读成功后重新获取未读数量
  notificationStore.fetchUnreadCount();
  // After marking all as read, refresh the current notification list to reflect changes
  // ... other refresh logic ...
   fetchNotificationsByFilter(); // Refetch with current filter
};

// Form validation rules
const profileRules: FormRules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 3, max: 20, message: '用户名长度在 3 到 20 个字符之间', trigger: 'blur' },
  ],
  // 邮箱字段禁用，无需验证规则
};

// Toggle edit mode
const toggleEditMode = () => {
  if (isEditMode.value) {
    cancelEdit();
  } else {
    isEditMode.value = true;
    originalUserProfile = { ...userProfile };
  }
};

// Save personal profile
const saveProfile = async () => {
  if (!profileFormRef.value) return;

  await profileFormRef.value.validate(async (valid) => {
    if (valid) {
      loading.value = true;
      errorMessage.value = '';
      const loadingInstance = ElLoading.service({ fullscreen: true, text: '保存中...' });
      try {
        const updateData = {
          username: userProfile.username,
          // 如果允许修改其他字段，也在这里添加
        };
        const response = await AuthService.updateProfile(updateData);
        ElMessage.success(response.message || '个人资料更新成功！');
        isEditMode.value = false;
        if (authStore.currentUser) {
          authStore.currentUser.username = userProfile.username;
          localStorage.setItem('username', userProfile.username);
        }
      } catch (error: any) {
        errorMessage.value = error.response?.data?.message || '更新失败，请重试。';
        ElMessage.error(errorMessage.value);
        console.error('Update profile failed:', error);
      } finally {
        loading.value = false;
        loadingInstance.close();
      }
    } else {
      ElMessage.warning('请检查您的输入。');
    }
  });
};

// Cancel editing, revert to original data
const cancelEdit = () => {
  Object.assign(userProfile, originalUserProfile);
  profileFormRef.value?.clearValidate();
  isEditMode.value = false;
};

// Get user profile data
const fetchUserProfile = async () => {
  loading.value = true;
  errorMessage.value = '';
  try {
    const data = await AuthService.getUserProfile();
    Object.assign(userProfile, data);
    originalUserProfile = { ...userProfile };
    if (authStore.currentUser) {
        authStore.currentUser.username = data.username;
        authStore.currentUser.email = data.email;
        authStore.currentUser.isAdmin = data.is_admin;
        authStore.currentUser.emailVerified = data.email_verified;
        localStorage.setItem('username', data.username || '');
        localStorage.setItem('email', data.email || '');
        localStorage.setItem('is_admin', data.is_admin.toString());
        localStorage.setItem('emailVerified', data.email_verified.toString());
    }
  } catch (error: any) {
    errorMessage.value = error.response?.data?.message || '无法加载个人资料。';
    ElMessage.error(errorMessage.value);
    console.error('Fetch user profile failed:', error);
  } finally {
    loading.value = false;
  }
};

// Resend verification email
const resendVerification = async () => {
  if (userProfile.email) {
    try {
      await AuthService.resendVerificationEmail(userProfile.email);
      ElMessage.success('新的验证邮件已发送，请检查您的收件箱。');
    } catch (error: any) {
      ElMessage.error(error.response?.data?.message || '重发验证邮件失败。');
    }
  } else {
    ElMessage.warning('无法获取用户邮箱，请尝试重新加载页面。');
  }
};

// Fetch notifications on tab switch or component mount (for initial load)
const fetchNotifications = () => {
  const statusFilter = filterIsRead.value === 'all' ? null : filterIsRead.value;
  notificationStore.fetchNotifications(notificationCurrentPage.value, notificationStore.pagination.per_page, statusFilter);
};

// Fetch initial data on component mount
onMounted(() => {
  if (authStore.isAuthenticated) {
    fetchUserProfile();
    // Only fetch notifications and unread count if the notifications tab is active initially
    // This optimization is commented out for now to ensure data is loaded even if profile tab is default
    // if (activeTab.value === 'notifications') {
      fetchNotifications();
    // }
  } else {
    router.push('/login');
    ElMessage.info('请先登录以查看个人资料。');
  }
});

// Optional: Watch activeTab to refetch notifications when switching to that tab
// import { watch } from 'vue';
// watch(activeTab, (newTab) => {
//   if (newTab === 'notifications') {
//     fetchNotifications();
//   }
// });

</script>

<style scoped>
.profile-tabs .el-tabs__content {
  padding: 0;
}

.profile-content {
  padding: 20px;
  position: relative; /* Add this for absolute positioning context */
  padding-top: 60px; /* Add padding to make space for the button */
}

.card-header-title {
  font-size: 20px;
  font-weight: bold;
}

.user-profile-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: calc(50vh - 60px);
  padding: 20px;
}

.box-card {
  width: 100%;
  max-width: 800px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.profile-input {
  width: 40%;
}

.save-buttons-item {
  display: flex;
  justify-content: center;
  align-items: center;
}

/* Styles copied from NotificationPage.vue */
.notification-card {
  width: 100%;
  max-height: 500px;
  overflow-y: auto;
  /* Adjust margin if needed, relative to its new container */
}
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 1.1em;
  font-weight: bold;
}
.pagination-container {
  margin-top: 20px;
  display: flex;
  justify-content: center;
}

.tab-label-content {
  display: inline-flex;
  align-items: center;
  font-size: 1.1em;
  font-weight: bold;
  gap: 5px;
}
</style>