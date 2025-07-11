<template>
  <el-card class="admin-sensitive-words-card" v-loading="loading">
    <template #header>
      <div class="card-header">
        <span>敏感词管理</span>
        <div>
          <el-button type="success" :icon="Plus" @click="showAddDialog">添加敏感词</el-button>
          <el-button type="info" :icon="Refresh" @click="refreshCache" :loading="refreshLoading">刷新缓存</el-button>
        </div>
      </div>
    </template>

    <el-table :data="adminStore.sensitiveWords" style="width: 100%" v-if="adminStore.sensitiveWords.length > 0">
      <el-table-column prop="id" label="ID" width="80" />
      <el-table-column prop="content" label="敏感词内容" />
      <el-table-column prop="created_at" label="添加时间" sortable width="180">
        <template #default="scope">
          {{ new Date(scope.row.created_at).toLocaleDateString() }}
        </template>
      </el-table-column>
      <el-table-column label="操作" width="100">
        <template #default="scope">
          <el-button size="small" type="danger" @click="deleteSensitiveWord(scope.row.id)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>
    <el-empty v-else description="暂无敏感词。"></el-empty>

    <div class="pagination-container" v-if="adminStore.sensitiveWordsPagination.total > adminStore.sensitiveWordsPagination.per_page">
      <el-pagination
        background
        layout="prev, pager, next"
        :total="adminStore.sensitiveWordsPagination.total"
        :page-size="adminStore.sensitiveWordsPagination.per_page"
        v-model:current-page="currentPage"
        @current-change="handlePageChange"
      />
    </div>

    <el-dialog v-model="addDialogVisible" title="添加敏感词" width="400">
      <el-form :model="addForm" ref="addFormRef" :rules="addRules">
        <el-form-item label="敏感词" prop="content">
          <el-input v-model="addForm.word" placeholder="请输入敏感词"></el-input>
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="addDialogVisible = false">取消</el-button>
          <el-button type="primary" @click="submitAddSensitiveWord" :loading="addLoading">
            添加
          </el-button>
        </span>
      </template>
    </el-dialog>
  </el-card>
</template>

<script setup>
import { ref, onMounted, reactive } from 'vue';
import { useAdminStore } from '../../stores/admin';
import { ElMessage, ElMessageBox } from 'element-plus';
import { Plus, Refresh } from '@element-plus/icons-vue';

const adminStore = useAdminStore();
const loading = ref(true);
const currentPage = ref(1);
const refreshLoading = ref(false);

// 添加敏感词弹窗相关
const addDialogVisible = ref(false);
const addFormRef = ref(null);
const addLoading = ref(false);
const addForm = reactive({
  word: ''
});

const addRules = reactive({
  word: [
    { required: true, message: '请输入敏感词内容', trigger: 'blur' },
    { min: 1, max: 100, message: '长度在 1 到 100 个字符', trigger: 'blur' }
  ]
});

onMounted(async () => {
  await fetchSensitiveWords();
  loading.value = false;
});

const fetchSensitiveWords = async () => {
  await adminStore.fetchSensitiveWords(currentPage.value, adminStore.sensitiveWordsPagination.per_page);
};

const handlePageChange = (page) => {
  currentPage.value = page;
  fetchSensitiveWords();
};

const showAddDialog = () => {
  addForm.word = ''; // 重置表单
  addDialogVisible.value = true;
};

const submitAddSensitiveWord = async () => {
  if (!addFormRef.value) return;
  addFormRef.value.validate(async (valid) => {
    if (valid) {
      addLoading.value = true;
      const success = await adminStore.addSensitiveWord(addForm.word);
      addLoading.value = false;
      if (success) {
        addDialogVisible.value = false;
        await fetchSensitiveWords(); // 刷新列表
      }
    } else {
      ElMessage.error('请填写敏感词内容。');
      return false;
    }
  });
};

const deleteSensitiveWord = async (wordId) => {
  ElMessageBox.confirm('此操作将永久删除该敏感词，是否继续？', '提示', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning'
  }).then(async () => {
    const success = await adminStore.removeSensitiveWord(wordId);
    if (success) {
      await fetchSensitiveWords(); // 刷新列表
    }
  }).catch(() => {
    ElMessage.info('已取消删除。');
  });
};

const refreshCache = async () => {
  refreshLoading.value = true;
  await adminStore.refreshSensitiveWordCache(); // 刷新敏感词缓存
  refreshLoading.value = false;
};
</script>

<style scoped>
.admin-sensitive-words-card {
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