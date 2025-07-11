<template>
  <div class="team-square-container">
    <!-- 页面标题 -->
    <h2>团队广场</h2>

    <!-- 搜索和筛选卡片区域 -->
    <el-card class="search-filter-card">
        <el-row :gutter="20">
            <!-- 搜索输入框 -->
            <el-col :span="12">
                <el-input
                    v-model="searchQuery"
                    placeholder="搜索团队名称、创建者或标签，也可搜索宝可梦的中/英文名称"
                    clearable
                    @change="handleSearch"
                >
                    <!-- 搜索图标前缀 -->
                    <template #prefix>
                         <el-icon><Search /></el-icon>
                    </template>
                </el-input>
            </el-col>
            <!-- 世代筛选下拉框 -->
            <el-col :span="6">
                <el-select v-model="generationFilter" placeholder="筛选世代" clearable @change="handleFilter">
                    <el-option label="全部世代" :value="''" />
                    <!-- TODO: Dynamically load generations from backend -->
                     <el-option
                          v-for="gen in generationOptions"
                          :key="gen.value"
                          :label="gen.label"
                          :value="gen.value"
                      />
                     <!-- Add more generations as needed -->
                </el-select>
            </el-col>
             <!-- 格式筛选下拉框 -->
             <el-col :span="6">
                <el-select v-model="formatFilter" placeholder="筛选格式" clearable @change="handleFilter">
                    <el-option label="全部格式" :value="''" />
                    <el-option :label="formatZhMap['Singles']" value="Singles" />
                    <el-option :label="formatZhMap['Doubles']" value="Doubles" />
                    <!-- Add more formats as needed -->
                </el-select>
            </el-col>
        </el-row>
    </el-card>

    <!-- 团队列表区域，加载状态显示 loading -->
    <div v-loading="teamSquareStore.isLoading" class="team-list-area">
      <!-- 团队卡片网格 -->
      <div v-if="teamSquareStore.publicTeams.length > 0" class="team-cards-grid">
        <!-- 遍历显示团队卡片 -->
        <TeamCard
          v-for="team in teamSquareStore.publicTeams"
          :key="team.id"
          :team="team"
        />
      </div>
      <!-- 没有团队时显示空状态 -->
      <el-empty v-else description="暂无公开团队信息。"></el-empty>
    </div>

    <!-- 分页组件，当总数大于每页数量时显示 -->
    <div class="pagination-container" v-if="teamSquareStore.pagination.total > teamSquareStore.pagination.per_page">
      <el-pagination
        background
        layout="prev, pager, next"
        :total="teamSquareStore.pagination.total"
        :page-size="teamSquareStore.pagination.per_page"
        v-model:current-page="teamSquareStore.pagination.page"
        @current-change="teamSquareStore.handlePageChange"
      />
    </div>

  </div>
</template>

<script setup lang="ts">
// 导入 Vue 相关函数
import { ref, onMounted, computed } from 'vue';
// 导入团队广场 store
import { useTeamSquareStore } from '@/stores/teamSquare';
// 导入 TeamCard 组件
import TeamCard from '@/components/Team/TeamCard.vue';
// 导入 Element Plus 的搜索图标
import { Search } from '@element-plus/icons-vue';
// 导入格式汉化映射常量
import { formatZhMap } from '@/utils/constants';

// 使用团队广场 store
const teamSquareStore = useTeamSquareStore();

// 使用 store 中的 ref 同步搜索框和筛选器的状态
const searchQuery = ref(teamSquareStore.searchQuery);
const generationFilter = ref(teamSquareStore.generationFilter);
const formatFilter = ref(teamSquareStore.formatFilter);

// 计算属性：将 store 中的 generations 状态转换为 el-select 的 options 格式
const generationOptions = computed(() => {
  // 格式转换：将 { id: 1, name: 'generation-i' } 转换为 { label: 'Gen 1', value: 'Gen 1' }
  return teamSquareStore.generations
    .map(gen => ({
      label: 'Gen ' + gen.id, // 假设后端使用 'Gen X' 格式进行过滤
      value: 'Gen ' + gen.id, // 匹配后端过滤值格式
    }))
    // 按世代 ID 降序排序
    .sort((a, b) => {
      const aId = parseInt(a.value.replace('Gen ', ''));
      const bId = parseInt(b.value.replace('Gen ', ''));
      return bId - aId;
    });
});

// 组件挂载后执行的操作
onMounted(() => {
  // 在组件挂载时获取公开团队列表和世代列表
  teamSquareStore.fetchPublicTeams();
  teamSquareStore.fetchGenerations(); // 挂载时获取世代数据
});

// 处理搜索输入变化事件，触发 store 中的搜索操作
const handleSearch = () => {
    teamSquareStore.handleSearch(searchQuery.value);
};

// 处理筛选条件变化事件，触发 store 中的筛选操作
const handleFilter = () => {
    teamSquareStore.handleFilter(generationFilter.value, formatFilter.value);
};

// TODO: Add methods to fetch formats dynamically for filters

</script>

<style scoped>
/* 团队广场容器样式 */
.team-square-container {
  padding: 20px;
  max-width: 1200px;
  margin: 0 auto;
}
/* 标题样式 */
h2 {
    text-align: center;
    margin-bottom: 20px;
}
/* 搜索筛选卡片样式 */
.search-filter-card {
    margin-bottom: 20px;
    padding: 20px;
}
/* 团队列表区域样式，设置最小高度并处理加载状态 */
.team-list-area {
    min-height: 300px; /* 在加载或无内容时确保一定高度 */
    position: relative;
}
/* 团队卡片网格布局 */
.team-cards-grid {
  columns: 300px auto; /* 列宽约 300px，自动计算列数 */
  column-gap: 20px; /* 列之间的间距 */
}
/* 分页容器样式，居中显示 */
.pagination-container {
  margin-top: 20px;
  display: flex;
  justify-content: center;
}
</style> 