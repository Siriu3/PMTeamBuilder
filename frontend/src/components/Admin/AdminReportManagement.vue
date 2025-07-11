<template>
  <el-card class="admin-report-card" v-loading="loading">
    <template #header>
      <div class="card-header">
        <span>举报管理</span>
        <el-select v-model="reportStatusFilter" placeholder="筛选状态" style="width: 120px" @change="fetchReports">
          <el-option label="全部" value="" />
          <el-option label="待处理" value="pending" />
          <el-option label="已处理" value="handled" />
        </el-select>
      </div>
    </template>

    <el-table :data="adminStore.reports" style="width: 100%" v-if="adminStore.reports.length > 0">
      <el-table-column prop="reporter_username" label="举报者" width="160" />
      <el-table-column prop="team_name" label="被举报团队" width="250" />
      <el-table-column prop="status" label="状态" width="100">
        <template #default="scope">
          <el-tag :type="getTagType(scope.row.status)">{{ getStatusText(scope.row.status) }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="created_at" label="举报时间" sortable width="150">
        <template #default="scope">
          {{ new Date(scope.row.created_at).toLocaleDateString() }}
        </template>
      </el-table-column>
      <el-table-column prop="handler_username" label="处理者" width="160" />
      <el-table-column prop="action" label="处理动作" width="100">
        <template #default="scope">
          <el-tag v-if="scope.row.action" :type="getActionType(scope.row.action)">
            {{ getActionText(scope.row.action) }}
          </el-tag>
          <span v-else>未处理</span>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="180">
        <template #default="scope">
          <el-button
            size="small"
            :type="scope.row.status === 'resolved' || scope.row.status === 'rejected' ? 'info' : 'primary'"
            @click="handleReport(scope.row)"
            :disabled="scope.row.status === 'resolved' || scope.row.status === 'rejected'"
          >
            处理
          </el-button>
          <el-button
            size="small"
            type="info"
            @click="viewReportHistory(scope.row.id)"
            :disabled="scope.row.status === 'pending'"
          >
            历史
          </el-button>
        </template>
      </el-table-column>
    </el-table>
    <el-empty v-else description="暂无举报信息。"></el-empty>

    <div class="pagination-container" v-if="adminStore.reportsPagination.total > adminStore.reportsPagination.per_page">
      <el-pagination
        background
        layout="prev, pager, next"
        :total="adminStore.reportsPagination.total"
        :page-size="adminStore.reportsPagination.per_page"
        v-model:current-page="currentPage"
        @current-change="handlePageChange"
      />
    </div>

    <el-dialog v-model="dialogVisible" :title="isViewingHistory ? '举报处理历史' : '处理举报'" width="500">
      <el-form v-if="currentReport" :model="reportForm" ref="reportFormRef" :rules="reportRules">
        <el-form-item label="举报者:">
          {{ currentReport.reporter_username }}
        </el-form-item>
        <el-form-item label="被举报团队:">
          {{ currentReport.team_name }}
        </el-form-item>
        <el-form-item label="举报理由:">
          {{ currentReport.reason }}
        </el-form-item>

        <template v-if="!isViewingHistory">
          <el-form-item label="处理动作" prop="action">
            <el-radio-group v-model="reportForm.action">
              <el-radio label="ignore">忽略</el-radio>
              <el-radio label="reject_team">警告</el-radio>
              <el-radio label="delete_team">删除团队</el-radio>
            </el-radio-group>
          </el-form-item>
          <el-form-item label="处理评论" prop="comment">
            <el-input
              v-model="reportForm.comment"
              type="textarea"
              :rows="3"
              placeholder="请输入处理评论 (警告或删除时必填)"
            />
          </el-form-item>
        </template>

        <template v-else>
          <el-form-item label="处理动作:">
            {{ getActionText(reportForm.action) }}
          </el-form-item>
          <el-form-item label="处理评论:">
            {{ reportForm.comment || '无评论' }}
          </el-form-item>
        </template>

      </el-form>
      <template #footer>
        <span class="dialog-footer" v-if="!isViewingHistory">
          <el-button @click="dialogVisible = false">取消</el-button>
          <el-button type="primary" @click="submitReportHandling" :loading="submitLoading">
            提交处理
          </el-button>
        </span>
        <span class="dialog-footer" v-else>
           <el-button @click="dialogVisible = false">关闭</el-button>
        </span>
      </template>
    </el-dialog>
  </el-card>
</template>

<script setup>
import { ref, onMounted, reactive } from 'vue';
import { useAdminStore } from '../../stores/admin';
import { ElMessage, ElMessageBox } from 'element-plus';

const adminStore = useAdminStore();
const loading = ref(true);
const currentPage = ref(1);
const reportStatusFilter = ref(''); // 筛选状态

// 处理弹窗相关
const dialogVisible = ref(false);
const dialogTitle = ref('处理举报');
const currentReport = ref(null);
const reportFormRef = ref(null);
const submitLoading = ref(false);
const isViewingHistory = ref(false); // Add state variable for viewing history
const reportForm = reactive({
  action: 'ignore', // 默认忽略
  comment: ''
});

const reportRules = reactive({
  comment: [
    {
      required: true,
      message: '警告或删除时必须填写处理评论',
      trigger: 'blur',
      validator: (rule, value, callback) => {
        if ((reportForm.action === 'warn' || reportForm.action === 'delete') && !value.trim()) {
          callback(new Error('警告或删除时必须填写处理评论'));
        } else {
          callback();
        }
      }
    }
  ]
});

onMounted(async () => {
  await fetchReports();
  loading.value = false;
});

const fetchReports = async () => {
  await adminStore.fetchReports(currentPage.value, adminStore.reportsPagination.per_page, reportStatusFilter.value);
};

const handlePageChange = (page) => {
  currentPage.value = page;
  fetchReports();
};

const handleReport = (report) => {
  currentReport.value = report;
  reportForm.action = report.action || 'ignore'; // 初始化表单
  reportForm.comment = report.comment || '';
  isViewingHistory.value = false; // Set to false when handling
  dialogVisible.value = true;
};

const submitReportHandling = async () => {
  if (!reportFormRef.value) return;
  reportFormRef.value.validate(async (valid) => {
    if (valid) {
      submitLoading.value = true;
      const success = await adminStore.handleReport(
        currentReport.value.id,
        reportForm.action,
        reportForm.comment
      );
      submitLoading.value = false;
      if (success) {
        dialogVisible.value = false;
        await fetchReports(); // 刷新列表
      }
    } else {
      ElMessage.error('请填写完整的处理信息。');
      return false;
    }
  });
};

const viewReportHistory = (reportId) => {
  const report = adminStore.reports.find(r => r.id === reportId);
  if (report) {
    currentReport.value = report;
    reportForm.action = report.action || ''; // Populate form with history data
    reportForm.comment = report.comment || '';
    isViewingHistory.value = true; // Set to true when viewing history
    dialogVisible.value = true;
  } else {
    ElMessage.error('未找到该举报的历史记录。');
  }
};

const getTagType = (status) => {
  switch (status) {
    case 'pending': return 'warning';
    case 'handled': return 'success';
    default: return 'info';
  }
};

const getStatusText = (status) => {
  switch (status) {
    case 'pending': return '待处理';
    case 'handled':
    case 'rejected':
    case 'resolved':
      return '已处理';
    default: return '未知';
  }
};

const getActionType = (action) => {
  switch (action) {
    case 'ignore': return 'info';
    case 'reject_team': return 'warning';
    case 'delete_team': return 'danger';
    default: return '';
  }
};

const getActionText = (action) => {
  switch (action) {
    case 'ignore': return '忽略';
    case 'reject_team': return '警告';
    case 'delete_team': return '删除';
    default: return '';
  }
};
</script>

<style scoped>
.admin-report-card {
  width: 100%;
  margin-top: 20px;
}
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 1.2em;
  font-weight: bold;
}
.pagination-container {
  margin-top: 20px;
  display: flex;
  justify-content: center;
}
</style>