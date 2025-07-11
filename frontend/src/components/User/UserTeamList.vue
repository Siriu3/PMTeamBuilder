<template>
  <el-card class="user-team-list-card" v-loading="loading">
    <template #header>
      <div class="card-header">
        <span>我创建的团队</span>
        <el-button type="primary" :icon="Plus" @click="createTeam">创建新团队</el-button>
      </div>
    </template>

    <el-table :data="userStore.userTeams" style="width: 100%" >
      <el-table-column prop="name" label="团队名称" sortable width="200"/>
      <el-table-column prop="generation" label="世代" width="95">
        <template #header>
          <el-select v-model="selectedGeneration" placeholder="世代" size="small" clearable @change="fetchTeams">
            <el-option
              v-for="gen in generations"
              :key="gen.id"
              :label="'Gen ' + gen.id"
              :value="'Gen ' + gen.id"/>
          </el-select>
        </template>
      </el-table-column>
      <el-table-column prop="format" label="格式" width="85">
        <template #header>
          <el-select v-model="selectedFormat" placeholder="格式" size="small" clearable @change="fetchTeams">
             <el-option label="单打" value="Singles"/>
             <el-option label="双打" value="Doubles"/>
          </el-select>
        </template>
        <template #default="scope">
          {{ formatZhMap[scope.row.format] || scope.row.format }}
        </template>
      </el-table-column>
      <el-table-column label="宝可梦" width="350">
        <template #default="scope">
          <div class="pokemon-sprite-list">
            <img v-for="poke in scope.row.pokemons || []" :key="poke.id" :src="poke.sprite || '/ball_default.png'" :alt="poke.species_name_zh || 'sprite'" class="pokemon-team-sprite" />
            <div v-for="index in (6 - (scope.row.pokemons || []).length)" :key="'placeholder-' + index" class="pokemon-team-sprite-placeholder"></div>
          </div>
        </template>
      </el-table-column>
      <el-table-column label="审核状态" width="95">
        <template #header>
           <el-select v-model="selectedReviewStatus" placeholder="状态" size="small" clearable @change="fetchTeams">
            <el-option label="已通过" value="approved"/>
            <el-option label="待审核" value="pending"/>
            <el-option label="已拒绝" value="rejected"/>
          </el-select>
        </template>
        <template #default="scope">
          <el-tag :type="getTagType(scope.row.review_status)">{{ getStatusText(scope.row.review_status) }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="隐私设置" width="85">
         <template #header>
            <el-select v-model="selectedPrivacy" placeholder="隐私" size="small" clearable @change="(value) => fetchTeams(value)">
               <el-option label="公开" :value="true"/>
               <el-option label="私密" :value="false"/>
            </el-select>
         </template>
         <template #default="scope">
            {{ scope.row.is_public ? '公开' : '私密' }}
         </template>
      </el-table-column>
      <el-table-column label="操作" width="250">
        <template #default="scope">
          <el-button size="small" @click="viewTeamDetails(scope.row.id)">查看</el-button>
          <el-button size="small" @click="editTeam(scope.row.id)">编辑</el-button>
          <el-button size="small" type="danger" @click="deleteTeam(scope.row.id)">删除</el-button>
        </template>
      </el-table-column>

      <template #empty>
          <el-empty description="没有找到符合筛选条件的团队或您还没有创建团队"></el-empty>
      </template>

    </el-table>

    <div class="pagination-container" v-if="userStore.userTeamsPagination.total > userStore.userTeamsPagination.per_page">
      <el-pagination
        background
        layout="prev, pager, next"
        :total="userStore.userTeamsPagination.total"
        :page-size="userStore.userTeamsPagination.per_page"
        v-model:current-page="currentPage"
        @current-change="handlePageChange"
      />
    </div>
  </el-card>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { useUserStore } from '../../stores/user';
import { useRouter } from 'vue-router';
import { ElMessage, ElMessageBox } from 'element-plus';
import { Plus } from '@element-plus/icons-vue';
import UserService from '../../services/UserService';
import { formatZhMap } from '../../utils/constants';

const userStore = useUserStore();
const router = useRouter();
const loading = ref(true);
const currentPage = ref(1);
const generations = ref([]); // To store generations for filter
const selectedGeneration = ref(null); // Filter by generation
const selectedReviewStatus = ref(null); // Filter by review status
const selectedFormat = ref(null); // Filter by format
const selectedPrivacy = ref(null); // Filter by privacy

onMounted(async () => {
  await fetchTeams();
  loading.value = false;
  // Fetch generations for the filter
  try {
    generations.value = await UserService.getGenerationsWithVersionGroups();
  } catch (error) {
    console.error("Failed to fetch generations for filter:", error);
  }
});

const fetchTeams = async (privacyValue = selectedPrivacy.value) => {
  // Log the value of selectedPrivacy before fetching
  console.log('Fetching teams with privacy filter:', privacyValue);
  // Pass selected filters to the fetchUserTeams action
  await userStore.fetchUserTeams(
    currentPage.value,
    userStore.userTeamsPagination.per_page,
    selectedGeneration.value, // Pass selected generation
    selectedReviewStatus.value, // Pass selected review status
    selectedFormat.value, // Pass selected format
    privacyValue // Use the passed privacy value
  );
};

const handlePageChange = (page) => {
  currentPage.value = page;
  fetchTeams(); // 分页处理：支持大量团队数据的分页显示
};

const createTeam = () => {
  // ElMessage.info('跳转到创建团队页面...');
  // 实际：router.push({ name: 'CreateTeam' });
  router.push('/team-builder');
};

const viewTeamDetails = (teamId) => {
  // ElMessage.info(`查看团队 ID: ${teamId} 的详情`);
  router.push({ name: 'TeamView', params: { teamId: teamId } }); // Navigate to the new TeamView route
};

const editTeam = (teamId) => {
  router.push({ name: 'TeamBuilderEdit', params: { teamId } });
};

const deleteTeam = async (teamId) => {
  ElMessageBox.confirm('此操作将永久删除该团队，是否继续？', '提示', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning'
  }).then(async () => {
    try {
      await UserService.deleteTeam(teamId);
      await fetchTeams(); // 删除后刷新列表
      ElMessage.success('团队删除成功！');
    } catch (error) {
      // 处理无权限等后端返回的错误
      const msg = error?.response?.data?.message || '团队删除失败。';
      ElMessage.error(msg);
    }
  }).catch(() => {
    ElMessage.info('已取消删除。');
  });
};

const getTagType = (status) => {
  switch (status) {
    case 'approved': return 'success';
    case 'pending': return 'warning';
    case 'rejected': return 'danger';
    default: return 'info';
  }
};

const getStatusText = (status) => {
  switch (status) {
    case 'approved': return '已通过';
    case 'pending': return '待审核';
    case 'rejected': return '已拒绝';
    default: return '未知';
  };
};
</script>

<style scoped>
.user-team-list-card {
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
.pokemon-sprite-list {
  display: flex;
  gap: 4px; /* Space between sprites */
  align-items: center;
}

.pokemon-team-sprite {
  width: 40px; /* Adjust size as needed */
  height: 40px; /* Adjust size as needed */
  object-fit: contain;
  background-color: #f0f0f0; /* Placeholder background */
  border-radius: 4px;
  margin-right: 8px;
}

.pokemon-team-sprite-placeholder {
   width: 40px; /* Match sprite width */
   height: 40px; /* Match sprite height */
   background-color: #f2f0f0; /* Lighter placeholder background */
   border-radius: 4px;
   margin-right: 8px;
}
</style>