<template>
  <el-container class="admin-panel-container">
    <el-card class="box-card">
      <template #header>
        <div class="card-header">
          <span>管理员面板</span>
        </div>
      </template>

      <div v-if="loading">
        <el-skeleton :rows="3" animated />
      </div>
      <div v-else>
        <el-alert v-if="adminOverallMessage" :title="adminOverallMessage" type="info" show-icon closable />
        <el-alert v-if="errorMessage" :title="errorMessage" type="error" show-icon closable />
      </div>

      <el-tabs v-model="activeAdminTab" type="card" class="admin-tabs">
        <el-tab-pane label="团队审核" name="team-review">
          <AdminTeamReview />
        </el-tab-pane>
        <el-tab-pane label="举报管理" name="report-management">
          <AdminReportManagement />
        </el-tab-pane>
        <el-tab-pane label="敏感词管理" name="sensitive-words">
          <AdminSensitiveWords />
        </el-tab-pane>
      </el-tabs>

    </el-card>
  </el-container>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { ElMessage, ElLoading, ElCard, ElAlert, ElSkeleton, ElTabs, ElTabPane } from 'element-plus';
import AuthService from '@/services/AuthService'; // 导入 AuthService

// 导入子组件
import AdminTeamReview from '@/components/Admin/AdminTeamReview.vue';
import AdminReportManagement from '@/components/Admin/AdminReportManagement.vue';
import AdminSensitiveWords from '@/components/Admin/AdminSensitiveWords.vue';

const activeAdminTab = ref('team-review'); // 默认选中团队审核

// 用于显示整体加载状态和消息
const loading = ref(false);
const adminOverallMessage = ref('Welcome!');
const errorMessage = ref('');

// 可以在这里添加一个方法来获取管理员面板的整体信息（如果需要）
const fetchOverallAdminStatus = async () => {
  loading.value = true;
  errorMessage.value = '';
  adminOverallMessage.value = 'Welcome!';
  try {
    // 假设有一个通用的管理员概览接口
    const data = await AuthService.getAdminData(); // 复用之前创建的getAdminData
    adminOverallMessage.value = "管理员面板概览数据已成功加载，请谨慎处理相关数据。" || data.message;
  } catch (error: any) {
    errorMessage.value = error.response?.data?.message || '无法加载管理员面板概览数据。';
    console.error('Fetch overall admin status failed:', error);
  } finally {
    loading.value = false;
  }
};

onMounted(() => {
  fetchOverallAdminStatus(); // 在组件挂载时获取概览数据
});
</script>

<style scoped>
.admin-panel-container {
  display: flex;
  justify-content: center;
  /* align-items: center; */ /* 移除或调整此项，否则内容过长时会被挤压 */
  min-height: calc(100vh - 60px);
  padding: 20px;
  background-color: #f5f7fa;
}

.box-card {
  width: 100%;
  max-width: 1200px; /* 增加最大宽度以容纳多标签页内容 */
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.admin-tabs {
  margin-top: 20px;
}
</style>