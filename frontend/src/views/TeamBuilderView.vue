<template>
  <div class="team-builder-view">
    <!-- 页面标题 -->
    <h1>团队构建入口</h1>
    <!-- 团队构建卡片区域 -->
    <el-card class="team-builder-card">
      <!-- 新建和加载队伍按钮行 -->
      <el-row :gutter="20" style="gap: 100px; margin-bottom: 20px;" justify="center">
        <!-- 新建空白队伍按钮 -->
        <el-col :span="8" style="text-align: center; margin-top: 30px;">
          <el-button type="primary" @click="showCreateDialog = true">新建空白队伍</el-button>
        </el-col>
        <!-- 从队伍/收藏加载按钮 -->
        <el-col :span="8" style="text-align: center;  margin-top: 30px;">
          <el-button type="info" @click="showLoadDialog = true; fetchInitialTeams();">从队伍/收藏加载</el-button>
        </el-col>
      </el-row>

    <!-- 通过 Token 导入队伍区域 -->
    <el-divider class="token-import-divider">通过Token导入队伍</el-divider>
         <el-form :model="importForm" class="token-import-form" label-width="100px">
              <!-- 导入队伍名称输入项 -->
              <el-form-item label="队伍名称">
                  <el-input v-model="importForm.name" placeholder="请输入队伍名称" />
              </el-form-item>
              <!-- 导入队伍 Token 输入项 -->
              <el-form-item label="队伍Token">
                  <el-input v-model="importForm.token" placeholder="请输入队伍Token" />
              </el-form-item>
              <!-- 导入操作按钮组 -->
              <div class="import-buttons-item">
                  <!-- 清空按钮 -->
                  <el-button type="default" @click="clearImportToken">清空</el-button>
                  <!-- 导入按钮 -->
                  <el-button type="success" @click="importByToken" style="margin-left: 50px;">导入</el-button>             
              </div>
         </el-form>
    </el-card>

    <!-- 加载队伍弹窗 -->
    <el-dialog v-model="showLoadDialog" title="选择已有队伍" width="1200px">
      <!-- 队伍/收藏 Tab 切换 -->
      <el-tabs v-model="loadTab" @tab-change="handleTabChange">
        <!-- 我的队伍 Tab -->
        <el-tab-pane label="我的队伍" name="my">
          <!-- 我的队伍表格 -->
          <el-table :data="myTeams" @row-dblclick="editTeam">
            <el-table-column prop="name" label="队伍名称" />
             <el-table-column prop="generation" label="世代" width="80" />
            <el-table-column prop="format" label="格式" width="80">
               <!-- 格式显示 -->
               <template #default="scope">
                   {{ formatMap[scope.row.format] || scope.row.format }}
               </template>
            </el-table-column>
             <el-table-column label="宝可梦" width="350" >
                <!-- 宝可梦精灵图列表 -->
                <template #default="scope">
                   <div class="pokemon-sprite-list">
                      <img v-for="poke in scope.row.pokemons || []" :key="poke.id" :src="poke.sprite || '/ball_default.png'" :alt="poke.species_name_zh || 'sprite'" class="pokemon-team-sprite" />
                      <!-- 宝可梦占位符 -->
                      <div v-for="index in (6 - (scope.row.pokemons || []).length)" :key="'placeholder-' + index" class="pokemon-team-sprite-placeholder"></div>
                   </div>
                </template>
             </el-table-column>
             <el-table-column prop="is_public" label="隐私" width="80">
                 <!-- 隐私状态标签 -->
                 <template #default="scope">
                     <el-tag :type="scope.row.is_public ? 'success' : 'info'">{{ scope.row.is_public ? '公开' : '私有' }}</el-tag>
                 </template>
             </el-table-column>
            <el-table-column prop="updated_at" label="更新时间">
               <!-- 更新时间格式化 -->
               <template #default="scope">
                 {{ formatDateTime(scope.row.updated_at) }}
               </template>
            </el-table-column>
            <!-- 操作列 -->
            <el-table-column label="操作" width="150">
              <template #default="scope">
                <!-- 编辑按钮 -->
                <el-button size="small" @click="editTeam(scope.row)">编辑</el-button>
                <!-- 复制按钮 -->
                <el-button size="small" @click="handleCopyTeam(scope.row.id)">复制</el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-tab-pane>
        <!-- 我的收藏 Tab -->
        <el-tab-pane label="我的收藏" name="favorite">
          <!-- 我的收藏表格 -->
          <el-table :data="favoriteTeams" @row-dblclick="viewTeamDetails">
            <el-table-column prop="name" label="团队名称" />
            <el-table-column prop="creator_username" label="创建者" width="100"/>
             <el-table-column prop="generation" label="世代" width="80" />
            <el-table-column prop="format" label="格式" width="80">
                <!-- 格式显示 -->
                <template #default="scope">
                   {{ formatMap[scope.row.format] || scope.row.format }}
               </template>
            </el-table-column>
            <el-table-column label="宝可梦" width="350">
               <!-- 宝可梦精灵图列表 -->
               <template #default="scope">
                   <div class="pokemon-sprite-list">
                      <img v-for="poke in scope.row.pokemons || []" :key="poke.id" :src="poke.sprite || '/ball_default.png'" :alt="poke.species_name_zh || 'sprite'" class="pokemon-team-sprite" />
                      <!-- 宝可梦占位符 -->
                      <div v-for="index in (6 - (scope.row.pokemons || []).length)" :key="'placeholder-' + index" class="pokemon-team-sprite-placeholder"></div>
                   </div>
               </template>
            </el-table-column>
            <el-table-column prop="is_public" label="隐私" width="80">
                <!-- 隐私状态标签 -->
                <template #default="scope">
                     <el-tag :type="scope.row.is_public ? 'success' : 'info'">{{ scope.row.is_public ? '公开' : '私有' }}</el-tag>
                 </template>
            </el-table-column>
            <el-table-column prop="updated_at" label="更新时间">
               <!-- 更新时间格式化 -->
               <template #default="scope">
                 {{ formatDateTime(scope.row.updated_at) }}
               </template>
            </el-table-column>
            <!-- 操作列 -->
            <el-table-column label="操作" width="150">
               <template #default="scope">
                 <!-- 复制按钮 -->
                 <el-button size="small" @click="handleCopyTeam(scope.row.id)">复制</el-button>
               </template>
            </el-table-column>
          </el-table>
        </el-tab-pane>
      </el-tabs>
      <!-- 加载队伍弹窗底部按钮 -->
      <template #footer>
        <el-button @click="showLoadDialog = false">关闭</el-button>
      </template>
    </el-dialog>

    <!-- 新建队伍弹窗 -->
     <el-dialog v-model="showCreateDialog" title="创建新队伍" width="500px">
       <!-- 新建队伍表单 -->
       <el-form :model="newTeamForm" label-width="100px">
         <!-- 团队名称输入项 -->
         <el-form-item label="团队名称" required>
           <el-input v-model="newTeamForm.name" maxlength="20" placeholder="请输入团队名称" />
         </el-form-item>
         <!-- 对战格式选择项 -->
         <el-form-item label="对战格式">
            <el-select v-model="newTeamForm.format" placeholder="请选择对战格式" style="width: 100%;">
               <el-option label="单打" value="Singles" />
               <el-option label="双打" value="Doubles" />
             </el-select>
         </el-form-item>
         <!-- 游戏世代选择项 -->
         <el-form-item label="游戏世代">
           <el-select v-model="newTeamForm.generation" placeholder="请选择世代" style="width: 100%;">
             <!-- 遍历获取到的世代数据 -->
             <el-option
               v-for="gen in generations"
               :key="gen.id"
               :label="'Gen ' + gen.id"
               :value="'Gen ' + gen.id"
             ></el-option>
           </el-select>
         </el-form-item>
         <!-- 是否公开选择项 -->
         <el-form-item label="是否公开">
            <el-switch v-model="newTeamForm.is_public" active-text="公开" inactive-text="私有" />
         </el-form-item>
         <!-- 自定义标签输入和列表 -->
         <el-form-item label="自定义标签">
           <!-- 标签输入框 -->
           <el-input v-model="newTagInput" placeholder="输入标签后回车添加" @keyup.enter="addNewTag" />
           <!-- 标签列表 -->
           <div class="tag-list" style="margin-top: 8px;">
             <el-tag
               v-for="(tag, idx) in newTeamForm.custom_tags"
               :key="tag + idx"
               closable
               @close="removeNewTag(idx)"
               type="info"
               style="margin-right: 4px;"
             >{{ tag }}</el-tag>
           </div>
         </el-form-item>
       </el-form>
       <!-- 新建队伍弹窗底部按钮 -->
       <template #footer>
         <el-button @click="showCreateDialog = false">取消</el-button>
         <el-button type="primary" @click="confirmCreateTeam">创建</el-button>
       </template>
     </el-dialog>
  </div>
</template>

<script setup lang="ts">
// 导入 Vue 相关函数
import { ref, onMounted, reactive, computed, watch } from 'vue';
// 导入 Vue Router 的 useRouter 函数
import { useRouter } from 'vue-router';
// 导入 Element Plus 的 ElMessage 消息提示组件
import { ElMessage } from 'element-plus';
// 导入用户服务模块
import UserService from '@/services/UserService';

// 获取路由实例
const router = useRouter();
// 控制加载队伍弹窗的显示状态
const showLoadDialog = ref(false);
// 控制新建队伍弹窗的显示状态
const showCreateDialog = ref(false);
// 加载队伍弹窗中当前选中的 Tab (my 或 favorite)
const loadTab = ref('my');
// 存储我的队伍列表数据
const myTeams = ref<any[]>([]);
// 存储我的收藏队伍列表数据
const favoriteTeams = ref<any[]>([]);
// 新建队伍表单数据对象
const newTeamForm = reactive({
  name: '',
  format: 'Singles',
  generation: 'Gen 9',
  custom_tags: [] as string[],
  pokemons: [] as any[],
  is_public: true,
});
// 新建队伍时输入的标签内容
const newTagInput = ref('');
// 存储获取到的世代数据
const generations = ref<any[]>([]);

// 对战格式映射，用于显示中文格式名称
const formatMap: { [key: string]: string } = {
  'Singles': '单打',
  'Doubles': '双打',
};

// 用于 Token 导入区域的表单数据对象
const importForm = reactive({
    name: '',
    token: '',
});

// 函数：生成一个随机的 6 位 Base62 字符串作为队伍名称后缀
const generateRandomCode = () => {
    const characters = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789';
    let result = '';
    const charactersLength = characters.length;
    for (let i = 0; i < 6; i++) {
        result += characters.charAt(Math.floor(Math.random() * charactersLength));
    }
    return result;
};

// 监听 showCreateDialog 变化，在弹窗显示时预填充队伍名称
watch(showCreateDialog, (newValue) => {
  if (newValue) {
    newTeamForm.name = `队伍-${generateRandomCode()}`;
  }
});

// 计算属性：默认的导入队伍名称，包含随机码
const defaultImportTeamName = computed(() => {
    // 如果 importForm.name 当前为空，则设置一个带随机码的默认名称
    if (!importForm.name) {
         importForm.name = `队伍-${generateRandomCode()}`;
    }
    // 返回 importForm.name 的值
    return importForm.name;
});

// 时间格式化函数，将 ISO 字符串格式化为 'YYYY-MM-DD HH:mm'
function formatDateTime(isoString: string | null | undefined): string {
  if (!isoString) return '';
  const date = new Date(isoString);
  const year = date.getFullYear();
  const month = ('0' + (date.getMonth() + 1)).slice(-2);
  const day = ('0' + date.getDate()).slice(-2);
  const hours = ('0' + date.getHours()).slice(-2);
  const minutes = ('0' + date.getMinutes()).slice(-2);
  return `${year}-${month}-${day} ${hours}:${minutes}`;
}

// 异步函数：获取我的队伍和收藏队伍的数据
const fetchInitialTeams = async () => {
   try {
     // 同时发起请求获取我的队伍和收藏队伍列表 (这里限制了100条)
     myTeams.value = (await UserService.getUserTeams(1, 100)).items || [];
     favoriteTeams.value = (await UserService.getFavoriteTeams(1, 100)).items || [];
  } catch (e) {
      console.error("Failed to fetch user teams or favorites:", e);
      ElMessage.error("加载队伍列表失败");
  }
};

// 组件挂载后执行的操作
onMounted(async () => {
  // 异步获取世代数据
  try {
     generations.value = await UserService.getGenerationsWithVersionGroups();
     // 设置 newTeamForm 的默认世代为最新世代 (Gen 9)
     const latestGen = generations.value.reduce((latest, gen) => gen.id > latest.id ? gen : latest, { id: 0 });
     if (latestGen.id > 0) {
         newTeamForm.generation = 'Gen ' + latestGen.id;
     }
  } catch (e) {
      console.error("Failed to fetch generations data:", e);
      ElMessage.error("加载世代数据失败");
  }
  // 访问 computed 属性以初始化默认导入队伍名称（虽然这里也可以直接设置，但访问 computed 触发其计算）
  console.log('TeamBuilderView mounted. Default import team name:', defaultImportTeamName.value);
});

// 处理加载队伍弹窗的 Tab 切换事件
const handleTabChange = (tabName: string) => {
    // 切换到我的队伍或我的收藏时，重新获取数据
    if (tabName === 'my' || tabName === 'favorite') { // 应该是 'favorite' 而不是 'fav'
        fetchInitialTeams(); // 每次 Tab 切换都刷新数据
    }
};

// 异步函数：通过 Token 导入队伍
async function importByToken() {
  // 检查队伍名称是否为空
  if (!importForm.name.trim()) { // 使用 trim() 移除首尾空格
      ElMessage.warning('请输入导入后队伍的名称！');
      return;
  }
  // 检查队伍 Token 是否为空
  if (!importForm.token.trim()) { // 使用 trim() 移除首尾空格
      ElMessage.warning('请输入队伍Token！');
      return;
  }
  try {
    // 调用服务方法根据 Token 获取队伍数据
    const importedTeamData = await UserService.getTeamByToken(importForm.token.trim()); // 使用 trim()

    // 准备导入的数据并导航到编辑页面
    // 后端服务 getTeamByToken 已经将数据格式化为导入所需格式 (移除 id, user_id, token 等，确保 pokemons 有本地 key 和正确的招式格式)

    // 导航到新的队伍编辑页面，通过 state 传递导入的数据
    // 这将跳转到 /team-builder/new，编辑页面会接收到 state 中的数据
    router.push({
      name: 'TeamBuilderEdit', // 编辑页面的路由名称
      params: { teamId: 'new' }, // 标记为创建新队伍
      state: {
        importedData: importedTeamData,
        importedName: importForm.name.trim(), // 传递用户输入的队伍名称 (已移除首尾空格)
      },
    });

    ElMessage.success('Token验证成功，正在导入队伍...');
    // 导入尝试成功后清空表单
    importForm.name = `队伍-${generateRandomCode()}`; // 重置为新的默认名称
    importForm.token = '';

  } catch (e: any) {
    console.error("Import by token failed:", e);
    // 显示导入失败的错误信息
    const msg = e?.response?.data?.message || '导入失败';
    ElMessage.error(msg);
  }
}

// 函数：编辑已有队伍，导航到编辑页面
function editTeam(team: any) {
  router.push({ name: 'TeamBuilderEdit', params: { teamId: team.id } }); // 导航到编辑页面，并传递队伍 ID
  showLoadDialog.value = false; // 关闭加载队伍弹窗
}

// 函数：查看收藏队伍详情，导航到队伍详情页面
function viewTeamDetails(team: any) {
   router.push({ name: 'TeamView', params: { teamId: team.id } }); // 导航到队伍详情页面，并传递队伍 ID
   showLoadDialog.value = false; // 关闭加载队伍弹窗
}

// 异步函数：处理"我的队伍"和"我的收藏"中的复制按钮点击事件
async function handleCopyTeam(teamId: number | string) {
    try {
        // 调用后端复制队伍 API
        const newTeam = await UserService.copyTeam(teamId.toString()); // 确保 teamId 是字符串类型
        console.log("团队复制成功:", newTeam);
        ElMessage.success(`团队 "${newTeam.name}" 复制成功！`); // 显示新队伍的名称

        // 可选：刷新弹窗中显示的队伍列表
        fetchInitialTeams();

        // 重定向到新复制队伍的编辑页面
        router.push({ name: 'TeamBuilderEdit', params: { teamId: newTeam.id } });
        showLoadDialog.value = false; // 关闭加载队伍弹窗
    } catch (error: any) {
        console.error("复制团队失败:", error);
        // 显示复制失败的错误信息
        const msg = error?.response?.data?.message || '复制团队失败';
        ElMessage.error(msg);
    }
}

// 函数：添加新的自定义标签
function addNewTag() {
  // 检查输入是否非空且标签不存在于列表中
  if (newTagInput.value.trim() && !newTeamForm.custom_tags.includes(newTagInput.value.trim())) { // 使用 trim()
    newTeamForm.custom_tags.push(newTagInput.value.trim()); // 添加标签并移除首尾空格
    newTagInput.value = ''; // 清空输入框
  }
}

// 函数：移除指定的自定义标签
function removeNewTag(idx: number) {
  newTeamForm.custom_tags.splice(idx, 1);
}

// 异步函数：确认创建新队伍
async function confirmCreateTeam() {
  // 检查团队名称是否为空
  if (!newTeamForm.name.trim()) { // 使用 trim()
    ElMessage.error('团队名称不能为空！');
    return;
  }

  // 构建要发送到后端的数据对象
  const teamDataToCreate = {
    name: newTeamForm.name.trim(), // 使用 trim() 移除首尾空格
    format: newTeamForm.format,
    generation: newTeamForm.generation,
    custom_tags: newTeamForm.custom_tags, // 标签在添加时已经移除首尾空格
    pokemons: [], // 新队伍初始时宝可梦列表为空
    is_public: newTeamForm.is_public,
  };

  try {
    // 调用 UserService 的 createTeam 方法创建队伍
    const newTeamResponse = await UserService.createTeam(teamDataToCreate);
    ElMessage.success('新队伍创建成功！');
    showCreateDialog.value = false; // 关闭新建队伍弹窗

    // 重定向到新创建队伍的编辑界面
    // 不需要通过 state 传递初始的空白宝可梦数据，EditView 会默认添加第一个宝可梦
     router.push({
       name: 'TeamBuilderEdit',
       params: { teamId: newTeamResponse.id },
       // blank creation does not need state
     });

  } catch (e: any) {
    console.error('Create team failed:', e);
    // 显示创建失败的错误信息
    const msg = e?.response?.data?.message || '创建队伍失败';
    ElMessage.error(msg);
  }
}

// 函数：清空导入 Token 输入框内容
const clearImportToken = () => {
    importForm.token = '';
};

</script>

<style scoped>
/* 团队构建视图容器样式 */
.team-builder-view {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  max-width: 700px;
  margin: 30px auto;
  padding: 24px;
}
/* Token 导入表单项样式 */
.token-import-form .el-form-item {
     margin-bottom: 15px; /* 调整堆叠表单项的底部外边距 */
     margin-right: 20px; /* 移除堆叠表单项的右侧外边距 */
}
/* Token 导入表单样式 */
.token-import-form {
     width: 450px; /* 根据需要调整宽度 */
     text-align: left; /* 文本左对齐 */
}
/* 调整输入框宽度 */
.token-import-form .el-input {
     width: 100%; /* 使输入框占据其父容器的全部宽度 */
}

/* 团队构建卡片样式 */
.team-builder-card {
  margin-top: 100px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 20px;
  width: 100%;
}

/* Token 导入分隔线样式 */
.token-import-divider {
  margin-top: 50px;
  margin-bottom: 20px;
}

/* 导入按钮组容器样式 */
.import-buttons-item {
  text-align: center;
}

/* 宝可梦精灵图列表容器样式 */
.pokemon-sprite-list {
  display: flex;
  gap: 4px; /* 精灵图之间的间距 */
  align-items: center;
}

/* 宝可梦团队精灵图样式 */
.pokemon-team-sprite {
  width: 40px; /* 根据需要调整大小 */
  height: 40px; /* 根据需要调整大小 */
  object-fit: contain; /* 保持图片比例 */
  background-color: #f0f0f0; /* 占位符背景色 */
  border-radius: 4px; /* 圆角 */
  margin-right: 8px; /* 右侧外边距 */
}

/* 宝可梦团队精灵图占位符样式 */
.pokemon-team-sprite-placeholder {
   width: 40px; /* 匹配精灵图宽度 */
   height: 40px; /* 匹配精灵图高度 */
   background-color: #f2f0f0; /* 较浅的占位符背景色 */
   border-radius: 4px; /* 圆角 */
   margin-right: 8px; /* 右侧外边距 */
}
</style>
