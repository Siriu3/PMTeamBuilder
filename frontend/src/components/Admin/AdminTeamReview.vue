<template>
  <el-card class="admin-review-card" v-loading="loading">
    <template #header>
      <div class="card-header">
        <span>待审核团队列表</span>
      </div>
    </template>

    <el-table :data="adminStore.teamsForReview" style="width: 100%" v-if="adminStore.teamsForReview.length > 0">
      <el-table-column prop="name" label="团队名称" sortable />
      <el-table-column prop="creator_username" label="提交者" />
      <el-table-column prop="generation" label="游戏世代" />
      <el-table-column prop="format" label="对战格式">
        <template #default="scope">
          {{ formatZhMap[scope.row.format] || scope.row.format }}
        </template>
      </el-table-column>
      <el-table-column prop="pokemon_count" label="宝可梦数量" width="120" />
      <el-table-column prop="created_at" label="提交时间" sortable>
        <template #default="scope">
          {{ new Date(scope.row.created_at).toLocaleString() }}
        </template>
      </el-table-column>
      <el-table-column label="操作" width="220">
        <template #default="scope">
          <el-button size="small" @click="previewTeam(scope.row)">预览</el-button>
          <el-button size="small" type="success" @click="handleReview(scope.row.id, 'approve')">通过</el-button>
          <el-button size="small" type="danger" @click="handleReview(scope.row.id, 'reject')">拒绝</el-button>
        </template>
      </el-table-column>
    </el-table>
    <el-empty v-else description="暂无待审核团队。"></el-empty>

    <div class="pagination-container" v-if="adminStore.teamsForReviewPagination.total > adminStore.teamsForReviewPagination.per_page">
      <el-pagination
        background
        layout="prev, pager, next"
        :total="adminStore.teamsForReviewPagination.total"
        :page-size="adminStore.teamsForReviewPagination.per_page"
        v-model:current-page="currentPage"
        @current-change="handlePageChange"
      />
    </div>

    <el-dialog v-model="dialogVisible" :title="dialogTitle" width="500">
      <el-form v-if="currentTeam" :model="reviewForm" ref="reviewFormRef" :rules="reviewRules">
        <el-form-item label="团队名称:">
          {{ currentTeam.name }}
        </el-form-item>
        <el-form-item label="提交者:">
          {{ currentTeam.creator_username }}
        </el-form-item>
        <el-form-item label="审核决定:">
          <el-radio-group v-model="reviewForm.decision">
            <el-radio label="approve">通过</el-radio>
            <el-radio label="reject">拒绝</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item v-if="reviewForm.decision === 'reject'" label="拒绝理由" prop="comment">
          <el-input
            v-model="reviewForm.comment"
            type="textarea"
            :rows="3"
            placeholder="请输入拒绝理由 (必填)"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="dialogVisible = false">取消</el-button>
          <el-button type="primary" @click="submitReview" :loading="submitLoading">
            提交审核
          </el-button>
        </span>
      </template>
    </el-dialog>

    <el-dialog v-model="previewDialogVisible" title="团队预览" width="800">
      <div v-if="previewTeamData">
        <h3>团队名称: {{ previewTeamData.name }}</h3>

        <div class="team-details-grid">
          <p><strong>提交者:</strong> {{ previewTeamData.creator_username }}</p>
          <p><strong>游戏世代:</strong> {{ previewTeamData.generation }}</p>
          <p><strong>对战格式:</strong> {{ formatZhMap[previewTeamData.format] || previewTeamData.format }}</p>
          <p><strong>创建时间:</strong> {{ new Date(previewTeamData.created_at).toLocaleString() }}</p>
        </div>

        <h4>宝可梦列表 (示例)</h4>
        <div class="pokemon-sprite-list-view" v-if="previewTeamData.pokemons && previewTeamData.pokemons.length > 0">
          <img v-for="(poke, index) in previewTeamData.pokemons" :key="poke.id || index" :src="poke.sprite || '/ball_default.png'" :alt="poke.species_name_zh || 'sprite'" class="pokemon-team-sprite-view" />
        </div>
        <p v-else>该团队暂无宝可梦信息或具体信息待接口提供。</p>

        <!-- Display review_comment if available -->
        <div class="review-comment-container" v-if="previewTeamData.review_comment">
           <el-divider content-position="center">审核评论</el-divider>
           <p style="text-align: center; margin-top: 10px; color: #f56c6c;">{{ previewTeamData.review_comment }}</p>
        </div>

        <el-divider>自定义词条</el-divider>
        <div class="tag-list-view" v-if="previewTeamData.custom_tags && previewTeamData.custom_tags.length > 0">
          <el-tag
            v-for="(tag, idx) in previewTeamData.custom_tags"
            :key="tag + idx"
            type="info"
            style="margin-right: 4px;"
          >{{ tag }}</el-tag>
        </div>
        <p v-else>该团队暂无自定义词条。</p>
      </div>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="handleRemoveSensitiveTags" :loading="tagsUpdating">一键删除敏感词条</el-button>
          <el-button @click="handleResetTeamName" :loading="nameUpdating">重置队伍名称</el-button>
          <el-button @click="previewDialogVisible = false">关闭</el-button>
        </span>
      </template>
    </el-dialog>
  </el-card>
</template>

<script setup>
import { ref, onMounted, reactive } from 'vue';
import { useAdminStore } from '../../stores/admin';
import { ElMessage, ElMessageBox } from 'element-plus';
import { formatZhMap } from '@/utils/constants';
import UserService from '@/services/UserService';

const adminStore = useAdminStore();
const loading = ref(true);
const currentPage = ref(1);

// 审核弹窗相关
const dialogVisible = ref(false);
const dialogTitle = ref('审核团队');
const currentTeam = ref(null);
const reviewFormRef = ref(null);
const submitLoading = ref(false);
const reviewForm = reactive({
  decision: 'approve', // 默认通过
  comment: ''
});

// 团队预览弹窗相关
const previewDialogVisible = ref(false);
const previewTeamData = ref(null); // 用于存储预览的团队详情

// 新增状态变量，用于按钮的加载状态
const tagsUpdating = ref(false);
const nameUpdating = ref(false);

const reviewRules = reactive({
  comment: [
    {
      required: true,
      message: '拒绝时必须填写拒绝理由',
      trigger: 'blur',
      validator: (rule, value, callback) => {
        if (reviewForm.decision === 'reject' && !value.trim()) {
          callback(new Error('拒绝时必须填写拒绝理由'));
        } else {
          callback();
        }
      }
    }
  ]
});

onMounted(async () => {
  await fetchTeamsForReview();
  loading.value = false;
});

const fetchTeamsForReview = async () => {
  await adminStore.fetchTeamsForReview(currentPage.value, adminStore.teamsForReviewPagination.per_page);
};

const handlePageChange = (page) => {
  currentPage.value = page;
  fetchTeamsForReview();
};

const previewTeam = async (team) => {
  previewDialogVisible.value = true;
   // 调用 API 获取完整的团队详情
  try {
     loading.value = true; // Optional: show loading for preview data fetch
     const teamDetails = await UserService.getTeamDetails(team.id.toString()); // 确保ID是字符串
     previewTeamData.value = teamDetails;
  } catch (error) {
     console.error('Failed to fetch team details for preview:', error);
     const msg = error?.response?.data?.message || '加载团队预览详情失败。';
     ElMessage.error(msg);
     previewDialogVisible.value = false; // Close dialog on error
  } finally {
      loading.value = false;
  }
};

const handleReview = (teamId, decision) => {
  currentTeam.value = adminStore.teamsForReview.find(team => team.id === teamId);
  if (!currentTeam.value) {
    ElMessage.error('未找到该团队。');
    return;
  }
  reviewForm.decision = decision;
  reviewForm.comment = ''; // 重置评论
  dialogTitle.value = `审核团队: ${currentTeam.value.name}`;
  dialogVisible.value = true;
};

const submitReview = async () => {
  if (!reviewFormRef.value) return;
  reviewFormRef.value.validate(async (valid) => {
    if (valid) {
      submitLoading.value = true;
      const success = await adminStore.reviewTeam(
        currentTeam.value.id,
        reviewForm.decision,
        reviewForm.comment
      );
      submitLoading.value = false;
      if (success) {
        dialogVisible.value = false;

        // 如果是拒绝，更新预览数据中的敏感信息显示
        if (reviewForm.decision === 'reject' && previewTeamData.value) {
          previewTeamData.value.name = `[已拒绝] ${previewTeamData.value.name}`; // 或者替换为其他提示
          previewTeamData.value.custom_tags = ['(敏感词条已处理)']; // 或者清空数组
        }

        await fetchTeamsForReview(); // 刷新列表
      }
    } else {
      ElMessage.error('请填写完整的审核信息。');
      return false;
    }
  });
};

// 新增方法：处理一键删除敏感词条
const handleRemoveSensitiveTags = async () => {
  if (!previewTeamData.value || !previewTeamData.value.id) return;
  tagsUpdating.value = true; // 开始加载
  try {
    // 调用 API 将自定义词条设置为空数组
    // 确保 teamId 是字符串类型，后端需要字符串或整数，这里用 toString() 确保兼容性
    await UserService.updateTeam(previewTeamData.value.id.toString(), { custom_tags: [] });
    previewTeamData.value.custom_tags = []; // 更新本地数据
    ElMessage.success('敏感词条已全部删除。');
     // 刷新待审核列表，因为词条改变可能影响审核状态（后端逻辑已添加）
    await fetchTeamsForReview();
  } catch (error) {
    console.error('Failed to remove sensitive tags:', error);
    const msg = error?.response?.data?.message || '删除敏感词条失败。';
    ElMessage.error(msg);
  } finally {
    tagsUpdating.value = false; // 结束加载
  }
};

// 新增方法：处理重置队伍名称
const handleResetTeamName = async () => {
  if (!previewTeamData.value || !previewTeamData.value.id) return;

  // 假设重置为包含ID的默认名称，您可以根据需要修改逻辑
  const defaultName = `队伍 ${previewTeamData.value.id}`;

  nameUpdating.value = true; // 开始加载
  try {
    // 调用 API 更新队伍名称
    // 确保 teamId 是字符串类型
    await UserService.updateTeam(previewTeamData.value.id.toString(), { name: defaultName });
    previewTeamData.value.name = defaultName; // 更新本地数据
    ElMessage.success('队伍名称已重置。');
     // 刷新待审核列表，因为名称改变可能影响审核状态（后端逻辑已添加）
    await fetchTeamsForReview();
  } catch (error) {
    console.error('Failed to reset team name:', error);
    const msg = error?.response?.data?.message || '重置队伍名称失败。';
    ElMessage.error(msg);
  } finally {
    nameUpdating.value = false; // 结束加载
  }
};
</script>

<style scoped>
.admin-review-card {
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

/* 添加 TeamView.vue 中的样式 */
.pokemon-sprite-list-view {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin-top: 10px;
  justify-content: center;
}

.pokemon-team-sprite-view {
  width: 60px; /* Adjust size as needed */
  height: 60px; /* Adjust size as needed */
  object-fit: contain;
  background-color: #f0f0f0; /* Placeholder background */
  border-radius: 4px;
}

/* 新增团队详情网格样式 */
.team-details-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); /* 自动适配列宽，至少250px */
  gap: 10px; /* 网格间距 */
  text-align: left; /* 文本左对齐 */
  margin-bottom: 10px; /* 与下方宝可梦列表的间距 */
  margin-left: 140px;
}

.review-comment-container {
  
}

</style>