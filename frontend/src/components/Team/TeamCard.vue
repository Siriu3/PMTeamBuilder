<template>
  <el-card class="team-card">
    <template #header>
      <div class="card-header">
        <span class="team-name">{{ team.name }}</span>
        <span class="creator-username">by {{ team.creator_username }}</span>
        <el-tag size="small">{{ team.generation }}</el-tag>
        <el-tag size="small">{{ formatZhMap[team.format] || team.format }}</el-tag>
      </div>
    </template>

    <div class="card-content">
      <!-- TODO: Add basic pokemon sprites display -->
       <div class="pokemon-sprites">
           <img
               v-for="(pokemon, index) in team.pokemons"
               :key="index"
               :src="pokemon.sprite_url"
               :alt="pokemon.name"
               class="pokemon-sprite-img"
           />
       </div>
       <div class="custom-tags" v-if="team.custom_tags && team.custom_tags.length > 0">
           <el-tag
               v-for="(tag, tagIndex) in team.custom_tags"
               :key="tagIndex"
               size="small"
               type="info"
               class="custom-tag"
           >{{ tag }}</el-tag>
       </div>
    </div>

    <div class="card-actions">
      <div class="card-actions-left">
        <el-button size="small" @click="handleLike(team.id)" :disabled="likeLoading" class="action-button no-background">
            <el-icon :color="team.is_liked ? '#e62829' : '#909399'"><Flag /></el-icon>
            {{ team.likes_count || 0 }}
        </el-button>
        <el-button size="small" @click="handleFavorite(team.id)" :disabled="favoriteLoading" class="action-button no-background">
             <el-icon :color="team.is_favorited ? '#fac000' : '#909399'"><Star v-if="!team.is_favorited" /><StarFilled v-else /></el-icon>
             {{ team.favorites_count || 0 }}
        </el-button>
      </div>
      <div class="card-actions-right">
        <el-button size="small" type="primary" @click="viewDetails(team)">查看详情</el-button>
         <el-button size="small" type="danger" @click="showReportDialog = true">举报</el-button>
      </div>
    </div>

    <!-- 举报弹窗 -->
    <el-dialog v-model="showReportDialog" title="举报团队" width="400px">
        <el-form :model="reportForm" :rules="reportRules" ref="reportFormRef">
            <el-form-item label="举报理由" prop="reason">
                <el-input
                    v-model="reportForm.reason"
                    type="textarea"
                    :rows="3"
                    placeholder="请详细描述举报理由"
                ></el-input>
            </el-form-item>
        </el-form>
        <template #footer>
            <span class="dialog-footer">
                <el-button @click="showReportDialog = false">取消</el-button>
                <el-button type="primary" @click="submitReport(team.id)" :loading="reportLoading">提交举报</el-button>
            </span>
        </template>
    </el-dialog>

  </el-card>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue';
import { useRouter } from 'vue-router';
import { useTeamSquareStore } from '@/stores/teamSquare';
import { ElMessage, ElMessageBox } from 'element-plus';
// import { Star, StarFilled, Heart, HeartFilled } from '@element-plus/icons-vue'; // 导入图标，暂时注释以避免Linter错误
import { Star, StarFilled, Flag } from '@element-plus/icons-vue'; // Ensure Star icons are imported if needed
import { formatZhMap } from '@/utils/constants'; // 导入格式汉化映射
// 移除不必要的导入，因为登录判断和 API 调用主要在 store 中处理
// import { useUserStore } from '@/stores/user';
// import { useAuthStore } from '@/stores/auth';

const router = useRouter();
const teamSquareStore = useTeamSquareStore();
// 移除不必要的 store 实例获取
// const userStore = useUserStore();
// const authStore = useAuthStore();

// 定义组件接收的 props
interface Props {
  team: {
    id: number | string;
    name: string;
    creator_username: string;
    generation: string;
    format: string;
    pokemon_count: number;
    created_at: string;
    favorites_count: number; // 收藏数
    likes_count: number;     // 点赞数
    is_liked?: boolean;      // 当前用户是否已点赞
    is_favorited?: boolean;  // 是否已收藏
    external_link?: string | null; // 添加 external_link 属性
    pokemons?: { // Assuming pokemons array is included with sprite_url
        name: string;
        sprite_url: string;
    }[];
    custom_tags?: string[]; // 添加 custom_tags 属性
    token?: string; // Added token property
    // 其他可能需要的字段
  };
}

const props = defineProps<Props>();

// 查看详情
const viewDetails = (team: Props['team']) => {
  if (team.token) { // Check if token exists
    const shareUrl = `/team/share/${team.token}`; // Construct the share URL
    window.open(shareUrl, '_blank'); // Open in a new tab
  } else if (team.external_link) {
    // If external_link exists, open it in a new tab
    window.open(team.external_link, '_blank');
  } else {
    // Otherwise, navigate to the existing TeamView route (optional, depends on requirement)
    // router.push({ name: 'TeamView', params: { teamId: team.id as string } });
    ElMessage.info('该团队暂无分享信息或外部链接。'); // Update message
  }
};

// 点赞相关
const likeLoading = ref(false); // 可以在 store 中统一管理，这里简化
const handleLike = async (teamId: number | string) => {
    // 委托给 store action，store 中已包含登录判断和逻辑
    await teamSquareStore.handleLike(teamId as string);
};

// 收藏相关
const favoriteLoading = ref(false); // 可以在 store 中统一管理，这里简化
const handleFavorite = async (teamId: number | string) => {
    // 移除多余的调试日志和判断逻辑，委托给 store action
    await teamSquareStore.handleFavorite(teamId as string);
};

// 举报相关
const showReportDialog = ref(false);
const reportFormRef = ref(null); // 用于表单验证
const reportForm = reactive({
    reason: ''
});

const reportRules = reactive({
    reason: [
        { required: true, message: '请输入举报理由', trigger: 'blur' }
    ]
});

const reportLoading = ref(false);
const submitReport = async (teamId: number | string) => {
    if (!reportFormRef.value) return;

    (reportFormRef.value as any).validate(async (valid: boolean) => {
        if (valid) {
            reportLoading.value = true;
            // 移除多余的调试日志和判断逻辑，委托给 store action
            const success = await teamSquareStore.handleReport(teamId as string, reportForm.reason);
            reportLoading.value = false;

            if (success) {
                 showReportDialog.value = false;
                 reportForm.reason = ''; // Reset form
            }
        } else {
            ElMessage.error('请填写举报理由。');
            return false;
        }
    });
};

</script>

<style scoped>
.team-card {
  margin-bottom: 20px;
  position: relative; /* Added for absolute positioning of card-actions */
  padding-bottom: 50px; /* Added padding to make space for absolute positioned actions */
}
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 1.1em;
  font-weight: bold;
}
.team-name {
    margin-right: 10px;
    flex-grow: 1; /* 让队伍名称占据更多空间 */
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
    max-width: 160px;
}
.creator-username {
    font-size: 0.7em; /* 标题字体的约 70% */
    font-weight: normal; /* 不加粗 */
    margin-right: 10px; /* 与后面的标签留出间距 */
    color: #606266; /* 可以根据需要调整颜色 */
}
.card-content p {
  margin: 5px 0;
  color: #606266;
}
.pokemon-sprites {
    display: flex;
    justify-content: center;
    margin-top: 10px;
}
.pokemon-sprite-img {
    width: 50px; /* Adjust size as needed */
    height: 50px; /* Adjust size as needed */
    margin: 0 2px;
}
.card-actions {
  margin-top: 15px;
  margin-left: 5px;
  display: flex; /* Use flexbox */
  justify-content: space-between; /* Space out left and right groups */
  align-items: center; /* Vertically center items */
  position: absolute; /* Fixed position relative to parent */
  bottom: 10px; /* Distance from the bottom */
  left: 10px; /* Distance from the left */
  right: 10px; /* Distance from the right */
  width: calc(100% - 20px); /* Adjust width to fill space minus padding */
  box-sizing: border-box; /* Include padding in width calculation */
  background-color: white; /* Ensure background covers content below */
  z-index: 10; /* Ensure buttons are clickable */
}
.card-actions-left,
.card-actions-right {
    display: flex;
    gap: 10px;
    align-items: center;
}

.card-actions-left .el-button,
.card-actions-right .el-button {
    margin-left: 0; /* Reset default margin */
    margin-right: 10px; /* Add spacing between buttons in a group */
    scale: 1.1;
}
.card-actions-right .el-button:last-child {
    margin-right: 16px; /* No right margin for the last button in the right group */
}
.action-button.no-background {
    background: transparent !important; /* Remove background */
    border: none !important; /* Remove border */
    padding: 0 5px; /* Adjust padding */
}
.action-button.no-background:hover {
    background: rgba(0, 0, 0, 0.05) !important; /* Add slight hover effect */
}
.action-button.no-background .el-icon {
    margin-right: 4px; /* Add space between icon and number */
}
.custom-tags {
    margin-top: 15px;
    text-align: center; /* 词条居中显示 */
}
.custom-tag {
    margin: 4px; /* 词条之间的间距 */
}
</style> 