<template>
  <el-card class="team-view-card" v-loading="loading">
    <template #header>
      <div class="card-header">
        <span v-if="!editingName">{{ team.name || "加载中..." }}</span>
        <el-input v-else v-model="editableTeamName" @keyup.enter="saveTeamName" @blur="saveTeamName" size="large" style="width: 240px;"></el-input>
        <el-button v-if="!editingName" :icon="Edit" @click="editTeamName" size="small" circle />
        <el-button v-else :icon="Check" @click="saveTeamName" size="small" circle />
        
        <div class="header-actions">
           <el-button type="primary" @click="copyTeam">复制</el-button>
           <el-button @click="goBack">返回</el-button>
        </div>
      </div>
    </template>
    <div class="team-view-card-content">
      <el-row :gutter="20">
        <el-col :span="12">
          <p><strong>世代:</strong> {{ team.generation }}</p>
          <p><strong>格式:</strong> {{ formatZhMap[team.format] || team.format }}</p>
          <p>
            <strong>隐私:</strong>
            <el-switch
              v-model="team.is_public"
              active-text="公开"
              inactive-text="私密"
              :loading="privacyUpdating"
              @change="handlePrivacyChange"
            />
          </p>
        </el-col>
        <el-col :span="12">
          <p><strong>审核状态:</strong> <el-tag :type="getTagType(team.review_status)">{{ getStatusText(team.review_status) }}</el-tag></p>
          <p><strong>创建日期:</strong> {{ new Date(team.created_at).toLocaleDateString() }}</p>
          <p><strong>更新日期:</strong> {{ new Date(team.updated_at).toLocaleDateString() }}</p>
        </el-col>
      </el-row>
    </div>

    <el-divider>宝可梦</el-divider>

    <div class="pokemon-sprite-list-view">
       <img v-for="poke in team.pokemons" :key="poke.id" :src="poke.sprite || '/ball_default.png'" :alt="poke.species_name_zh || 'sprite'" class="pokemon-team-sprite-view" />
    </div>

    <el-divider>自定义词条</el-divider>

     <div class="custom-tags-section">
        <el-input v-model="tagInput" placeholder="输入标签后回车添加" @keyup.enter="addTag" style="width: 200px; margin-right: 8px;" />
        <el-button type="primary" @click="addTag">添加标签</el-button>
        <div class="tag-list-view" style="margin-top: 8px;">
          <el-tag
            v-for="(tag, idx) in team.custom_tags"
            :key="tag + idx"
            closable
            @close="removeTag(idx)"
            type="info"
            style="margin-right: 4px;"
          >{{ tag }}</el-tag>
        </div>
    </div>

    <el-divider>社区数据与分享</el-divider>

    <div class="actions-placeholders">
         <!-- Display Token if available -->
         <p v-if="team.token"><strong>队伍 Token:</strong> <el-tag type="info">{{ team.token }}</el-tag> <el-button size="small" @click="copyToken"><el-icon><CopyDocument /></el-icon> 复制</el-button></p>
         <p v-else><strong>队伍 Token:</strong> (仅队伍创建者可见)</p>

         <!-- 修改为直接显示分享链接 -->
         <p v-if="team.token"><strong>分享链接:</strong>
            <a :href="shareUrl" target="_blank" rel="noopener noreferrer">{{ shareUrl }}</a>
            <el-button size="small" @click="copyShareLink"><el-icon><CopyDocument /></el-icon> 复制</el-button>
         </p>
         <p v-else><strong>分享链接:</strong> (仅队伍创建者可见)</p>

        <p><strong>点赞数:</strong> {{ team.likes_count || 0 }}</p>
        <p><strong>收藏数:</strong> {{ team.favorites_count || 0 }}</p>
    </div>

  </el-card>
</template>

<script setup>
import { ref, onMounted, reactive, computed } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { ElMessage, ElNotification, ElSwitch, ElMessageBox } from 'element-plus';
import { Edit, Check, CopyDocument } from '@element-plus/icons-vue';
import UserService from '@/services/UserService'; // Assuming UserService handles API calls
import { formatZhMap } from '@/utils/constants'; // Assuming formatZhMap is available

const route = useRoute();
const router = useRouter();
const teamId = route.params.teamId; // Get team ID from route parameters

const loading = ref(true);
const privacyUpdating = ref(false); // New ref for privacy switch loading state
const team = reactive({
  name: '',
  generation: '',
  format: '',
  is_public: false,
  review_status: '',
  custom_tags: [],
  pokemons: [],
  created_at: '',
  updated_at: '',
  token: null, // Add token field
  likes_count: 0, // Add placeholder for likes
  favorites_count: 0, // Add placeholder for favorites
});

const editingName = ref(false);
const editableTeamName = ref('');
const tagInput = ref('');

// === Computed property for share URL ===
const shareUrl = computed(() => {
  if (team.token) {
    return `${window.location.origin}/team/share/${team.token}`;
  }
  return '';
});
// =====================================

onMounted(async () => {
  if (!teamId) {
    ElMessage.error('未找到团队ID。');
    loading.value = false;
    return;
  }
  await fetchTeamDetails(teamId);
});

const fetchTeamDetails = async (id) => {
  loading.value = true;
  try {
    const data = await UserService.getTeamDetails(id);
    Object.assign(team, data);
    editableTeamName.value = team.name; // Initialize editable name
  } catch (error) {
    console.error('Failed to fetch team details:', error);
    const msg = error?.response?.data?.message || '加载团队详情失败。';
    ElMessage.error(msg);
  } finally {
    loading.value = false;
  }
};

const editTeamName = () => {
  editingName.value = true;
};

const saveTeamName = async () => {
  if (editableTeamName.value === team.name) {
    editingName.value = false; // No change, just exit editing
    return;
  }
   if (!editableTeamName.value.trim()) {
    ElMessage.warning('团队名称不能为空。');
    return;
  }
  loading.value = true; // Show loading indicator while saving
  try {
    await UserService.updateTeam(teamId.toString(), { name: editableTeamName.value }); // Use updateTeam and convert id to string
    team.name = editableTeamName.value; // Update local state
    ElMessage.success('团队名称更新成功。');
  } catch (error) {
     console.error('Failed to update team name:', error);
    const msg = error?.response?.data?.message || '更新团队名称失败。';
    ElMessage.error(msg);
    editableTeamName.value = team.name; // Revert to original name on error
  } finally {
    editingName.value = false;
     loading.value = false;
  }
};

const addTag = async () => {
  if (tagInput.value && !team.custom_tags.includes(tagInput.value.trim())) {
     const newTags = [...team.custom_tags, tagInput.value.trim()];
     loading.value = true; // Show loading while saving tags
     try {
        await UserService.updateTeam(teamId.toString(), { custom_tags: newTags }); // Use updateTeam
        team.custom_tags = newTags; // Update local state
        tagInput.value = ''; // Clear input
        ElMessage.success('标签添加成功。');
     } catch (error) {
        console.error('Failed to add tag:', error);
        const msg = error?.response?.data?.message || '添加标签失败。';
        ElMessage.error(msg);
     } finally {
         loading.value = false;
     }
  }
};

const removeTag = async (idx) => {
   const newTags = team.custom_tags.filter((_, i) => i !== idx);
    loading.value = true; // Show loading while saving tags
   try {
      await UserService.updateTeam(teamId.toString(), { custom_tags: newTags }); // Use updateTeam
      team.custom_tags = newTags; // Update local state
      ElMessage.success('标签移除成功。');
   } catch (error) {
      console.error('Failed to remove tag:', error);
      const msg = error?.response?.data?.message || '移除标签失败。';
      ElMessage.error(msg);
   } finally {
       loading.value = false;
   }
};

const copyTeam = async () => {
  loading.value = true; // Show loading
  try {
    const newTeam = await UserService.copyTeam(teamId.toString()); // Ensure id is string
    ElNotification({
      title: '复制成功',
      message: `团队 "${team.name}" 已成功复制。`, // Use original name
      type: 'success',
      duration: 3000,
    });
    // Redirect to the new team's edit page or view page
    router.push({ name: 'TeamBuilderEdit', params: { teamId: newTeam.id } }); // Redirect to edit

  } catch (error) {
     console.error('Failed to copy team:', error);
    const msg = error?.response?.data?.message || '复制团队失败。';
    ElMessage.error(msg);
  } finally {
     loading.value = false;
  }
};

const goBack = () => {
  router.go(-1);
};

// Helper functions for status display (copied from UserTeamList.vue)
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

const handlePrivacyChange = async (newValue) => {
  privacyUpdating.value = true; // Start loading
  try {
    await UserService.updateTeamPrivacy(teamId.toString(), newValue);
    ElMessage.success(`团队已设置为${newValue ? '公开' : '私密'}。`);
  } catch (error) {
    console.error('Failed to update privacy:', error);
    const msg = error?.response?.data?.message || '更新隐私设置失败。';
    ElMessage.error(msg);
    // Revert the switch state on error
    team.is_public = !newValue; // Assuming the change event already updated it
    ElMessage.info('隐私设置变更已取消。'); // Inform user
  } finally {
    privacyUpdating.value = false;
  }
};

// Function to copy team token
const copyToken = () => {
    if (team.token) {
        navigator.clipboard.writeText(team.token).then(() => {
            ElMessage.success('队伍 Token 已复制到剪贴板！');
        }).catch(err => {
            console.error('Failed to copy token:', err);
            ElMessage.error('复制 Token 失败。');
        });
    } else {
        ElMessage.warning('没有可用的队伍 Token。');
    }
};

// === 新增复制分享链接方法 ===
const copyShareLink = () => {
  if (shareUrl.value) {
    navigator.clipboard.writeText(shareUrl.value).then(() => {
      ElMessage.success('分享链接已复制到剪贴板！');
    }).catch(err => {
      console.error('Failed to copy share link:', err);
      ElMessage.error('复制分享链接失败。');
    });
  } else {
     ElMessage.warning('没有可用的分享链接。');
  }
};
// =========================

</script>

<style scoped>
.team-view-card {
  max-width: 900px;
  margin: 30px auto;
  padding: 24px;
}
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 1.2em;
  font-weight: bold;
}

/* Add styles for the new header-actions container */
.header-actions {
    display: flex; /* Use flexbox to align buttons in a row */
    align-items: center; /* Vertically center buttons */
    gap: 10px; /* Add space between the buttons */
}

.team-view-card-content {
  text-align: left;
}

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

.custom-tags-section {
    margin-top: 10px;
}

.tag-list-view {
    display: flex;
    flex-wrap: wrap;
    gap: 4px;
}

.actions-placeholders {
    margin-top: 20px;
}
.actions-placeholders h4 {
    margin-top: 15px;
    margin-bottom: 8px;
}
.actions-placeholders p {
    margin-bottom: 5px;
    color: #606266;
    /* Style for displaying link and button in line */
    display: flex;
    align-items: center;
    word-break: break-all; /* Prevent long links from overflowing */
}

.actions-placeholders strong {
    display: inline-block;
    width: 100px; /* Adjust as needed for alignment */
    flex-shrink: 0; /* Prevent shrinking */
}

.actions-placeholders .link-container {
    display: flex;
    align-items: center;
    flex-grow: 1; /* Allow link container to take available space */
}

.actions-placeholders .link-container a {
    margin-right: 10px; /* Space between link and copy button */
}

.actions-placeholders .el-button {
    /* Adjustments may be needed depending on desired alignment */
    margin-left: auto; /* Push the copy button to the right */
    flex-shrink: 0; /* Prevent the button from shrinking */
}

.el-divider {
  margin-top: 20px;
  margin-bottom: 20px;
}
</style> 