<template>
  <el-card class="user-favorite-list-card" v-loading="loading">
    <template #header>
      <div class="card-header">
        <span>我收藏的团队</span>
      </div>
    </template>

    <el-table :data="userStore.favoriteTeams" style="width: 100%" v-if="userStore.favoriteTeams.length > 0">
      <el-table-column prop="name" label="团队名称" sortable width="210"/>
      <el-table-column prop="creator_username" label="创建者" width="100"/>
      <el-table-column prop="generation" label="游戏世代" width="85">
        <template #header>
          <el-select v-model="selectedGeneration" placeholder="世代" size="small" clearable @change="fetchFavoriteTeams">
            <el-option
              v-for="gen in generations"
              :key="gen.id"
              :label="'Gen ' + gen.id"
              :value="'Gen ' + gen.id"/>
          </el-select>
        </template>
      </el-table-column>
      <el-table-column prop="format" label="对战格式" width="85">
        <template #header>
          <el-select v-model="selectedFormat" placeholder="格式" size="small" clearable @change="fetchFavoriteTeams">
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
      <el-table-column prop="created_at" label="收藏时间" sortable width="120">
        <template #default="scope">
          {{ new Date(scope.row.created_at).toLocaleDateString() }}
        </template>
      </el-table-column>
      <el-table-column label="操作" width="200">
        <template #default="scope">
          <el-button size="small" @click="viewTeamDetails(scope.row)">查看</el-button>
          <el-button size="small" type="danger" @click="unfavoriteTeam(scope.row.id)">取消收藏</el-button>
        </template>
      </el-table-column>
    </el-table>
    <el-empty v-else description="您还没有收藏任何团队。"></el-empty>

    <div class="pagination-container" v-if="userStore.favoriteTeamsPagination.total > userStore.favoriteTeamsPagination.per_page">
      <el-pagination
        background
        layout="prev, pager, next"
        :total="userStore.favoriteTeamsPagination.total"
        :page-size="userStore.favoriteTeamsPagination.per_page"
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
import { formatZhMap } from '../../utils/constants';
import UserService from '../../services/UserService';

const userStore = useUserStore();
const router = useRouter();
const loading = ref(true);
const currentPage = ref(1);
const generations = ref([]);
const selectedGeneration = ref(null);
const selectedFormat = ref(null);

onMounted(async () => {
  await fetchFavoriteTeams();
  loading.value = false;
  try {
    generations.value = await UserService.getGenerationsWithVersionGroups();
  } catch (error) {
    console.error("Failed to fetch generations for filter:", error);
  }
});

const fetchFavoriteTeams = async () => {
  await userStore.fetchFavoriteTeams(
    currentPage.value,
    userStore.favoriteTeamsPagination.per_page,
    selectedGeneration.value,
    selectedFormat.value
  );
};

const handlePageChange = (page) => {
  currentPage.value = page;
  fetchFavoriteTeams();
};

const viewTeamDetails = (team) => {
  if (team && team.token) {
    window.open(`/team/share/${team.token}`, '_blank');
  } else {
    ElMessage.error('无法获取团队分享信息。');
  }
};

const unfavoriteTeam = async (teamId) => {
  ElMessageBox.confirm('此操作将取消收藏该团队，是否继续？', '提示', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning'
  }).then(async () => {
    try {
      await UserService.removeFavorite(teamId);
      await fetchFavoriteTeams();
      ElMessage.success('取消收藏成功！');
    } catch (error) {
      const msg = error?.response?.data?.message || '取消收藏失败。';
      ElMessage.error(msg);
      console.error('取消收藏失败:', error);
    }
  }).catch(() => {
    ElMessage.info('已取消操作。');
  });
};
</script>

<style scoped>
.user-favorite-list-card {
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
  gap: 4px;
  align-items: center;
}

.pokemon-team-sprite {
  width: 40px;
  height: 40px;
  object-fit: contain;
  background-color: #f0f0f0;
  border-radius: 4px;
  margin-right: 8px;
}

.pokemon-team-sprite-placeholder {
   width: 40px;
   height: 40px;
   background-color: #f2f0f0;
   border-radius: 4px;
   margin-right: 8px;
}
</style>