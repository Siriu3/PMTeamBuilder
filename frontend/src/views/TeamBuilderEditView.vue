<template>
  <div class="team-builder-edit-view">
    <!-- 页面主标题 -->
    <h1 style="text-align: center;">编辑队伍宝可梦</h1>
    <!-- 队伍信息卡片，加载时显示 loading -->
    <el-card v-if="teamForm.name || teamId === 'new'" v-loading="loading">
      <!-- 是否公开开关容器 -->
      <div class="public-switch-container">
        <span>是否公开：<el-switch v-model="teamForm.is_public" active-text="公开" inactive-text="私有" @change="handlePrivacyChange"/></span>
      </div>
      <!-- 队伍基本信息（名称、格式、世代） -->
      <div class="team-info">
        <!-- 队伍名称显示和编辑 -->
        <span>队伍名称：<el-input v-if="editingName" v-model="editableTeamName" @keyup.enter="saveTeamName" @blur="saveTeamName" size="small" style="width: 150px; display: inline-block;"></el-input><span v-else>{{ teamForm.name }} <el-icon size="small" style="cursor: pointer;" @click="editTeamName"><Edit /></el-icon></span></span>
        <!-- 对战格式显示 -->
        <span>对战格式：{{ formatMap[teamForm.format] || teamForm.format }}</span>
        <!-- 游戏世代显示 -->
        <span>游戏世代：{{ teamForm.generation }}</span>
      </div>
      <!-- 顶部宝可梦 Tab 栏与操作按钮分行容器 -->
      <div class="pokemon-tab-bar-row">
        <!-- 宝可梦 Tab 栏（显示队伍中的宝可梦） -->
        <div class="pokemon-tab-bar">
          <!-- 遍历队伍中的宝可梦，显示为可拖拽的 Tab -->
          <div class="pokemon-slot" v-for="(poke, idx) in teamForm.pokemons" :key="poke.localKey || poke.id || idx"
            :class="{ active: idx === currentPokemonIndex, 'slot-placeholder': !poke.species_id }"
            @click="selectPokemon(idx)"
            draggable="true"
            @dragstart="dragStart(idx, $event)"
            @dragover.prevent="dragOver($event)"
            @dragleave="dragLeave($event)"
            @drop.prevent="drop(idx, $event)"
            @dragend="dragEnd($event)"
          >
            <!-- 宝可梦精灵图或占位符 -->
            <img v-if="poke.sprite" :src="poke.sprite" :alt="poke.species_name_zh || 'sprite'" class="poke-avatar" />
            <!-- 当没有精灵图时显示宝可梦名称的前两个字或 ?? -->
            <div v-else class="pokemon-icon-placeholder">{{ poke.species_name_zh ? poke.species_name_zh.substring(0,2) : '??' }}</div>
            <!-- 宝可梦简略信息（名称和道具） -->
            <div class="pokemon-brief">
              <div class="pokemon-name">{{ poke.species_name_zh || poke.species_name || '新宝可梦' }}</div>
              <div class="pokemon-item">{{ poke.item || '无道具' }}</div>
            </div>
            <!-- 移除宝可梦按钮（队伍中宝可梦数量大于1时显示） -->
            <el-icon v-if="teamForm.pokemons.length > 1" class="delete-icon" @click.stop="handleRemovePokemonFromConfig(idx)"><Delete /></el-icon>
          </div>
          <!-- 添加宝可梦槽位（队伍未满6只时显示） -->
          <div v-if="teamForm.pokemons.length < 6" class="pokemon-slot add-slot" @click="addPokemonAndSelect">
             <el-icon size="20"><Plus /></el-icon> 添加
          </div>
        </div>
      </div>
      <el-divider />
      <!-- 主体区域：单栏显示 TeamPokemonConfig 组件 -->
      <div class="main-content-single-column">
        <!-- 宝可梦配置组件，当前选中宝可梦时显示 -->
        <TeamPokemonConfig
          v-if="currentPokemonIndex !== null && teamForm.pokemons[currentPokemonIndex]"
          :pokemon="teamForm.pokemons[currentPokemonIndex]"
          :index="currentPokemonIndex"
          :generation="teamForm.generation"
          :version-group-id="selectedVersionGroupId"
          @remove="handleRemovePokemonFromConfig(currentPokemonIndex)"
          @update="updatePokemon(currentPokemonIndex, $event)"
        />
         <!-- 没有选中宝可梦但队伍中有宝可梦时的提示 -->
         <div v-else-if="teamForm.pokemons.length > 0" class="empty-config-prompt">
           <p>请从上方选择一个宝可梦进行配置。</p>
         </div>
          <!-- 队伍中没有宝可梦时的提示 -->
          <div v-else class="empty-config-prompt">
           <p>队伍中还没有宝可梦，点击上方 "+" 添加一个吧！</p>
         </div>
      </div>
      <el-divider />
      <!-- 底部按钮组 -->
      <div class="button-group">
        <!-- 返回列表按钮 -->
        <el-button @click="goBackToList">返回列表</el-button>
        <!-- 保存配置按钮 -->
        <el-button type="success" @click="handleSave">保存配置</el-button>
      </div>
    </el-card>
    <!-- 队伍数据加载中或不存在时的提示 -->
    <div v-else>
      <p>加载中或队伍不存在...</p>
    </div>
  </div>
</template>

<script setup lang="ts">
// 导入 Vue 相关函数
import { ref, onMounted, reactive, computed, watch } from 'vue';
// 导入 Vue Router 的 useRoute 和 useRouter 函数
import { useRoute, useRouter } from 'vue-router';
// 导入 Element Plus 相关组件和消息提示
import { ElMessage, ElMessageBox, ElNotification } from 'element-plus';
// 导入用户服务模块
import UserService from '@/services/UserService';
// 导入宝可梦配置组件
import TeamPokemonConfig from '@/components/TeamBuilder/TeamPokemonConfig.vue';
// 导入 Element Plus 图标
import { Plus, CopyDocument, Upload, Download, Sort, Delete, Edit, Check } from '@element-plus/icons-vue';
// 导入认证 store
import { useAuthStore } from '@/stores/auth';

// 获取路由和 router 实例
const route = useRoute();
const router = useRouter();
// 获取认证 store 实例
const authStore = useAuthStore();

// 从路由参数获取队伍 ID
const teamId = route.params.teamId as string;

// 控制页面加载状态
const loading = ref(false);
// 当前选中的宝可梦在队伍列表中的索引
const currentPokemonIndex = ref<number | null>(null);
// 默认的宝可梦图标路径
const defaultPokeIcon = '/ball_default.png';
// 存储获取到的世代数据
const generationsData = ref<any[]>([]);
// 当前选定世代对应的版本组 ID
const selectedVersionGroupId = ref<number | null>(null);

// 队伍表单响应式数据对象
const teamForm = reactive({
  id: null as number | null, // 队伍 ID，新建时为 null
  name: '', // 队伍名称
  format: 'Singles', // 对战格式
  generation: 'Gen 9', // 游戏世代
  custom_tags: [] as string[], // 自定义标签列表
  pokemons: [] as any[], // 队伍中的宝可梦列表
  is_public: true, // 是否公开
});

// 控制队伍名称编辑状态
const editingName = ref(false);
// 队伍名称编辑框的值
const editableTeamName = ref('');

// 对战格式映射，用于显示中文格式名称
const formatMap: { [key: string]: string } = {
  'Singles': '单打',
  'Doubles': '双打',
};

// 计算属性：判断当前用户是否为队伍创建者（这里简单判断用户是否已登录）
const isTeamOwner = computed(() => {
    return authStore.currentUser?.id !== undefined;
});

// 组件挂载后执行的操作
onMounted(async () => {
  try {
    // 异步获取世代数据和版本组信息
    generationsData.value = await UserService.getGenerationsWithVersionGroups();
    // 加载队伍数据或处理导入数据
    await loadTeamDataOrImport();
  } catch (error) {
    console.error("Failed to fetch generations data:", error);
    ElMessage.error("加载世代数据失败");
    loading.value = false;
  }
});

// 监听 teamForm.generation 变化，更新选定的版本组 ID
watch(() => teamForm.generation, (newGenName) => {
  updateSelectedVersionGroupId(newGenName);
});

// 函数：根据世代名称更新选定的版本组 ID
function updateSelectedVersionGroupId(generationName: string) {
  // 检查世代数据是否已加载
  if (!generationsData.value || generationsData.value.length === 0) {
      selectedVersionGroupId.value = null;
      console.warn(`Generations data not loaded yet or empty.`);
      return;
  }
  // 格式化世代名称以匹配后端数据
  const formattedGenName = generationName?.toLowerCase().replace('gen ', 'generation-');
  // 查找当前世代的数据
  const currentGenData = generationsData.value.find(gen => gen.name === formattedGenName);

  // 如果找到世代数据且有版本组，则设置选定的版本组 ID 为第一个版本组的 ID
  if (currentGenData && currentGenData.version_groups.length > 0) {
    selectedVersionGroupId.value = currentGenData.version_groups[0].id;
    console.log(`Selected Version Group ID for ${generationName}: ${selectedVersionGroupId.value}`);
  } else {
    // 如果没有找到版本组，则将选定的版本组 ID 设为 null
    selectedVersionGroupId.value = null;
    console.warn(`No version group found for generation: ${generationName}`);
  }
}

// 异步函数：加载队伍数据或处理导入数据
async function loadTeamDataOrImport() {
   loading.value = true; // 设置加载状态为 true

   // 从 history state 中获取导入的数据和名称
   const importedData = history.state?.importedData;
   const importedName = history.state?.importedName;

   console.log('Checking for imported data:', importedData, importedName);

   // 如果存在导入数据且路由参数 teamId 为 'new'，则使用导入数据初始化新队伍
   if (importedData && teamId === 'new') {
       console.log('Found imported data. Initializing new team with imported data.');
       // 将导入数据合并到 teamForm 中
       Object.assign(teamForm, {
           id: null,
           name: importedName || '导入的队伍', // 使用导入的名称或默认名称
           format: importedData.format || 'Singles', // 使用导入的格式或默认格式
           generation: importedData.generation || 'Gen 9', // 使用导入的世代或默认世代
           custom_tags: importedData.custom_tags || [], // 使用导入的标签或空数组
           pokemons: importedData.pokemons || [], // 使用导入的宝可梦列表或空数组
           is_public: false, // 导入的队伍默认设置为私有
       });
       // 设置可编辑的队伍名称
       editableTeamName.value = teamForm.name;

       // 更新选定的版本组 ID
       updateSelectedVersionGroupId(teamForm.generation);

       // 如果导入的宝可梦列表不为空，则选中第一个宝可梦，否则添加一个空白宝可梦
       if (teamForm.pokemons.length > 0) {
           currentPokemonIndex.value = 0;
       } else {
           addPokemon();
       }

       loading.value = false; // 设置加载状态为 false
       return;
   }

   // 如果路由参数 teamId 存在且不为 'new'，则根据 ID 加载已有队伍数据
   if (teamId && teamId !== 'new') {
       console.log(`Loading team details for ID: ${teamId}`);
       try {
         // 调用服务方法获取队伍详情
         const res = await UserService.getTeamDetails(teamId);
         // 将获取到的数据合并到 teamForm 中
         Object.assign(teamForm, {
             id: res.id,
             name: res.name,
             format: res.format,
             generation: res.generation,
             custom_tags: res.custom_tags || [],
             // 映射宝可梦数据，确保有 localKey
             pokemons: res.pokemons?.map((p: any) => ({
                  ...p,
                 localKey: p.localKey || `${Date.now()}-${Math.random().toString(36).substring(2,9)}-${p.id}`
             })) || [],
             is_public: res.is_public ?? true, // 使用获取到的公开状态或默认公开
         });

         // 设置可编辑的队伍名称
         editableTeamName.value = teamForm.name;

         // 更新选定的版本组 ID
         updateSelectedVersionGroupId(teamForm.generation);

         // --- Start: Debug Print ---
         console.log('TeamBuilderEditView: After loading team data, checking pokemon moves:');
         teamForm.pokemons.forEach((poke, index) => {
             console.log(`  Pokemon ${index + 1} (ID: ${poke.id}, LocalKey: ${poke.localKey}, Species ID: ${poke.species_id}):`);
             console.log('    Moves:', poke.moves);
         });
         // --- End: Debug Print ---

         // 如果队伍中没有宝可梦，则添加一个空白宝可梦并选中，否则选中第一个宝可梦
         if (teamForm.pokemons.length === 0) {
             addPokemon();
         } else {
             currentPokemonIndex.value = 0;
         }

       } catch (error) {
         console.error('Failed to load team details:', error);
         // 显示加载失败的错误信息
         const msg = (error as any)?.response?.data?.message || '加载队伍信息失败';
         ElMessage.error(msg);
          // 加载失败后重定向到队伍构建入口页
          router.push({ name: 'TeamBuilder' });
       } finally {
         loading.value = false; // 设置加载状态为 false
       }
   } else if (teamId === 'new') {
        console.log('Creating a new blank team.');
        // 初始化一个空白的新队伍数据
       Object.assign(teamForm, {
            id: null,
            name: '新队伍',
            format: 'Singles',
            // 设置默认世代为最新世代，如果世代数据未加载则默认为 Gen 9
            generation: generationsData.value.length > 0 ? 'Gen ' + generationsData.value.reduce((latest, gen) => gen.id > latest.id ? gen : latest, { id: 0 }).id : 'Gen 9',
            custom_tags: [],
            pokemons: [],
            is_public: true,
       });
        // 设置可编辑的队伍名称
        editableTeamName.value = teamForm.name;

       // 更新选定的版本组 ID
       updateSelectedVersionGroupId(teamForm.generation);

       // 添加一个空白宝可梦并选中
       addPokemon();
       loading.value = false; // 设置加载状态为 false
   } else {
       console.error("Unexpected route state in TeamBuilderEditView.");
       loading.value = false; // 设置加载状态为 false
   }
}

// 函数：切换到队伍名称编辑状态
function editTeamName() {
    editableTeamName.value = teamForm.name; // 将当前队伍名称赋值给编辑框
    editingName.value = true; // 设置编辑状态为 true
}

// 异步函数：保存队伍名称
async function saveTeamName() {
    // 如果名称没有改变，则退出编辑状态
    if (editableTeamName.value === teamForm.name) {
         editingName.value = false;
         return;
    }
    // 如果编辑后的名称为空，则提示并恢复原名称
    if (!editableTeamName.value.trim()) {
         ElMessage.warning('团队名称不能为空！');
         editableTeamName.value = teamForm.name;
         return;
    }
    // 如果是新建队伍 (id 为 null)，则只更新本地名称
     if (teamForm.id === null) {
          teamForm.name = editableTeamName.value;
          editingName.value = false;
          return;
     }
    loading.value = true; // 设置加载状态为 true
    try {
        // 调用服务方法更新队伍名称
        await UserService.updateTeam(teamForm.id.toString(), { name: editableTeamName.value });
        teamForm.name = editableTeamName.value; // 更新本地队伍名称
        ElMessage.success('团队名称已更新。'); // 显示成功消息
         editingName.value = false; // 退出编辑状态

    } catch (error: any) {
         console.error("Failed to update team name:", error);
         // 显示更新失败的错误信息
         const msg = error?.response?.data?.message || '更新名称失败';
         ElMessage.error(msg);
         editableTeamName.value = teamForm.name; // 恢复原名称
    } finally {
         loading.value = false; // 设置加载状态为 false
    }
}

// 函数：添加一个空白宝可梦槽位
function addPokemon() {
  // 检查队伍是否已满
  if (teamForm.pokemons.length < 6) {
    // 创建一个新的空白宝可梦对象
    const newPokemon = {
      // 生成一个唯一的本地 key
      id: `local-${Date.now()}-${Math.random().toString(36).substring(2, 9)}`,
      localKey: `${Date.now()}-${Math.random().toString(36).substring(2,9)}-new`,
      species_id: null,
      species_name: '',
      species_name_zh: '新宝可梦',
      level: 50,
      ability: '',
      item: '',
      nature: '',
      // 默认努力值和个体值
      evs: { hp: 0, atk: 0, def: 0, spa: 0, spd: 0, spe: 0 },
      ivs: { hp: 31, atk: 31, def: 31, spa: 31, spd: 31, spe: 31 },
      moves: ['', '', '', ''], // 默认四个空白招式槽位
      sprite: defaultPokeIcon, // 默认精灵图
      types: [],
      generation: teamForm.generation, // 继承队伍的世代
      tera_type: null, // 默认太晶属性为 null
    };
    // 将新宝可梦添加到队伍列表并转为响应式对象
    teamForm.pokemons.push(reactive(newPokemon));
    // 返回新添加宝可梦的索引
    return teamForm.pokemons.length - 1;
  }
  // 如果队伍已满，返回 null
  return null;
}

// 函数：添加一个宝可梦并选中它
function addPokemonAndSelect() {
  const newIndex = addPokemon(); // 添加宝可梦
  // 如果成功添加，则选中新添加的宝可梦
  if (newIndex !== null) {
    currentPokemonIndex.value = newIndex;
  } else {
    ElMessage.warning('队伍已满，无法添加更多宝可梦！'); // 队伍已满提示
  }
}

// 函数：选中指定索引的宝可梦
function selectPokemon(idx: number) {
  currentPokemonIndex.value = idx; // 设置当前选中宝可梦的索引
}

// 函数：移除指定索引的宝可梦
function removePokemon(idx: number) {
  // 检查索引是否有效
  if (idx < 0 || idx >= teamForm.pokemons.length) return;
  // 记录当前选中宝可梦的 key，以便移除后重新选中
  const selectedPokemonKey = currentPokemonIndex.value !== null && teamForm.pokemons[currentPokemonIndex.value]
                                ? (teamForm.pokemons[currentPokemonIndex.value].localKey || teamForm.pokemons[currentPokemonIndex.value].id)
                                : null;

  // 从队伍列表中移除宝可梦
  teamForm.pokemons.splice(idx, 1);

  // 如果队伍列表变空，则取消选中
  if (teamForm.pokemons.length === 0) {
    currentPokemonIndex.value = null;
  } else {
     // 查找之前选中宝可梦的新索引
     const newIdxOfSelected = selectedPokemonKey !== null
                               ? teamForm.pokemons.findIndex(p => (p.localKey || p.id) === selectedPokemonKey)
                               : -1;

     // 如果找到新索引，则选中该宝可梦
     if (newIdxOfSelected !== -1) {
        currentPokemonIndex.value = newIdxOfSelected;
     } else {
         // 如果没找到（可能被移除的是选中的宝可梦），则根据情况重新选中
         if (idx < teamForm.pokemons.length) {
             // 如果移除位置后面还有宝可梦，则选中移除位置的宝可梦
             currentPokemonIndex.value = idx;
         } else if (teamForm.pokemons.length > 0) {
             // 如果移除位置是最后一个，则选中新的最后一个宝可梦
             currentPokemonIndex.value = teamForm.pokemons.length - 1;
         } else {
             // 如果队伍已空，则取消选中
             currentPokemonIndex.value = null;
         }
     }
  }
}

// 函数：处理从 TeamPokemonConfig 组件触发的移除事件
function handleRemovePokemonFromConfig(idx: number) {
    // 显示确认移除的对话框
    ElMessageBox.confirm(
    `确定要从队伍中移除 ${teamForm.pokemons[idx]?.species_name_zh || '该宝可梦'} 吗?`,
    '确认移除',
    {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning',
    }
  ).then(() => {
    // 用户确认移除，调用 removePokemon 函数
    removePokemon(idx);
    ElMessage.success('宝可梦已移除'); // 显示移除成功消息
  }).catch(() => {
    // 用户取消移除，不做任何操作
  });
}

// 函数：更新指定索引宝可梦的数据
function updatePokemon(idx: number, data: any) {
  // 确保当前有选中的宝可梦且索引有效
  if (currentPokemonIndex.value !== null && teamForm.pokemons[idx]) {
    // 将更新的数据合并到对应的宝可梦对象中
    Object.assign(teamForm.pokemons[idx], data);
  }
}

// 拖拽相关状态：被拖拽宝可梦的索引
let draggedItemIndex = -1;

// 函数：处理拖拽开始事件
function dragStart(index: number, event: DragEvent) {
  draggedItemIndex = index; // 记录被拖拽宝可梦的索引
  if (event.dataTransfer) {
    event.dataTransfer.effectAllowed = 'move'; // 设置拖拽效果为移动
    event.dataTransfer.setData('text/plain', index.toString()); // 存储被拖拽宝可梦的索引
    const el = event.target as HTMLElement;
    if(el) el.classList.add('dragging'); // 添加拖拽样式
  }
}

// 函数：处理拖拽经过目标元素事件
function dragOver(event: DragEvent) {
  event.preventDefault(); // 阻止默认行为（阻止放置）
  if (event.dataTransfer) {
    event.dataTransfer.dropEffect = 'move'; // 设置放置效果为移动
  }
   const el = event.currentTarget as HTMLElement;
   // 如果目标元素不存在 drag-over-active 类，则添加
   if (el && !el.classList.contains('drag-over-active')) {
        el.classList.add('drag-over-active');
   }
}

// 函数：处理拖拽离开目标元素事件
function dragLeave(event: DragEvent) {
    const el = event.currentTarget as HTMLElement;
    if(el) el.classList.remove('drag-over-active'); // 移除 drag-over-active 样式
}

// 函数：处理放置事件
function drop(targetIndex: number, event: DragEvent) {
  event.preventDefault(); // 阻止默认行为
   const el = event.currentTarget as HTMLElement;
   if(el) el.classList.remove('drag-over-active'); // 移除 drag-over-active 样式

  // 如果没有被拖拽的宝可梦或目标索引是被拖拽的宝可梦本身，则不做任何操作
  if (draggedItemIndex === -1 || draggedItemIndex === targetIndex) {
    draggedItemIndex = -1;
    return;
  }

  // 记录拖拽前选中宝可梦的 key
  const selectedPokemonKeyBeforeDrag = currentPokemonIndex.value !== null && teamForm.pokemons[currentPokemonIndex.value]
                                     ? (teamForm.pokemons[currentPokemonIndex.value].localKey || teamForm.pokemons[currentPokemonIndex.value].id)
                                     : null;

  // 移除被拖拽的宝可梦
  const [itemToMove] = teamForm.pokemons.splice(draggedItemIndex, 1);
  // 将宝可梦插入到目标位置
  teamForm.pokemons.splice(targetIndex, 0, itemToMove);

  // 如果之前有选中的宝可梦，则重新查找其在新列表中的索引并选中
  if (selectedPokemonKeyBeforeDrag) {
    const newIdxOfSelected = teamForm.pokemons.findIndex(p => (p.localKey || p.id) === selectedPokemonKeyBeforeDrag);
    if (newIdxOfSelected !== -1) {
      currentPokemonIndex.value = newIdxOfSelected;
    } else {
       // 如果没找到（不应该发生），则取消选中
       currentPokemonIndex.value = null;
    }
  } else {
    // 如果之前没有选中宝可梦，则取消选中
    currentPokemonIndex.value = null;
  }

  draggedItemIndex = -1; // 重置拖拽状态
}

// 函数：处理拖拽结束事件
function dragEnd(event: DragEvent) {
    const el = event.target as HTMLElement;
    if(el) el.classList.remove('dragging'); // 移除拖拽样式
    draggedItemIndex = -1; // 重置拖拽状态
}

// 监听 teamForm.pokemons 变化
watch(() => teamForm.pokemons, (newPokemons, oldPokemons) => {
  // 如果列表变空，则取消选中
  if (newPokemons.length === 0) {
    currentPokemonIndex.value = null;
  } else if (currentPokemonIndex.value !== null) {
    // 如果之前有选中，尝试保持索引
    if (currentPokemonIndex.value >= newPokemons.length) {
      // 如果旧索引超出新列表范围，则选中最后一个宝可梦
      currentPokemonIndex.value = newPokemons.length - 1;
    }
    // 如果旧索引仍然有效，则保持不变
  } else if (newPokemons.length > 0 && currentPokemonIndex.value === null) {
     // 如果列表不为空但之前没有选中，则不做任何操作（取消自动选中第一个宝可梦）
  }
}, { deep: true }); // 深度监听 pokemons 数组的变化

// 异步函数：处理保存配置操作
async function handleSave() {
  // 检查团队名称是否为空
  if (!teamForm.name.trim()) {
    ElMessage.error('请输入团队名称！');
    return;
  }
   // 检查队伍中是否有宝可梦
   if (teamForm.pokemons.length === 0) {
     ElMessage.error('队伍中至少需要一只宝可梦！');
     return;
   }

  // 检查宝可梦努力值总和是否超出上限
  const pokemonWithInvalidEvs = teamForm.pokemons.find(p => {
      const totalEv = Object.values(p.evs || {}).reduce((sum: number, ev: any) => sum + (ev || 0), 0);
      return totalEv > 508;
  });
  if (pokemonWithInvalidEvs) {
      // 显示努力值超出的警告消息
      ElMessage.warning(`宝可梦 ${pokemonWithInvalidEvs.species_name_zh || '未知宝可梦'} 的努力值总和超出上限 (508)，请调整。`);
      return;
  }

  loading.value = true; // 设置加载状态为 true
  try {
    // 准备要发送到后端的宝可梦数据（过滤掉 species_id 为 null 的宝可梦，处理招式格式）
    const pokemonsToSave = teamForm.pokemons
        .filter(p => p.species_id !== null)
        .map(p => {
            const { localKey, ...rest } = p; // 移除 localKey
            // 提取招式名称，确保格式正确且过滤掉空招式
            const movesToSend = (rest.moves || []).map((move: any) => {
                if (move && typeof move === 'object') {
                    return move.move_name_zh || move.name_zh || '';
                }
                return typeof move === 'string' ? move : '';
            }).filter((moveName: string) => moveName);

            return {
                ...rest,
                // 如果是本地新建或导入的宝可梦，将 id 设为 null
                id: (typeof rest.id === 'string' && (rest.id.startsWith('local-') || rest.id.startsWith('import-'))) ? null : rest.id,
                moves: movesToSend, // 使用处理后的招式列表
            };
    });

    // 构建要发送到后端的队伍数据对象
    const teamDataToSave = {
      name: teamForm.name.trim(), // 移除名称首尾空格
      format: teamForm.format,
      generation: teamForm.generation,
      custom_tags: teamForm.custom_tags, // 标签在添加时已处理
      pokemons: pokemonsToSave, // 使用处理后的宝可梦列表
      is_public: teamForm.is_public,
    };

    let responseData; // 用于存储后端响应数据
    // 根据 teamForm.id 判断是更新还是创建队伍
    if (teamForm.id !== null) {
      console.log('Updating team:', teamForm.id, teamDataToSave);
      // 调用服务方法更新队伍
      responseData = await UserService.updateTeam(teamForm.id.toString(), teamDataToSave);
       ElMessage.success('团队更新成功！'); // 显示更新成功消息
    } else {
       console.log('Creating new team:', teamDataToSave);
       // 调用服务方法创建队伍
      responseData = await UserService.createTeam(teamDataToSave);
       ElMessage.success('团队创建成功！'); // 显示创建成功消息
       // 如果创建成功且返回了 id，则更新本地 teamForm 的 id 并替换当前路由
       if (responseData && responseData.id) {
            teamForm.id = responseData.id;
            router.replace({ name: 'TeamBuilderEdit', params: { teamId: responseData.id } });
       }
    }

    // 保存成功后，重定向到队伍详情页面
     router.push({ name: 'TeamView', params: { teamId: teamForm.id ? teamForm.id.toString() : responseData.id.toString() } });

  } catch (e: any) {
    console.error('Save failed:', e);
    // 显示保存失败的错误信息
    const msg = e?.response?.data?.message || '保存失败';
    ElMessage.error(msg);
  } finally {
    loading.value = false; // 设置加载状态为 false
  }
}

// 函数：返回队伍列表页
const goBackToList = () => {
    router.push({ name: 'TeamBuilder' }); // 导航到队伍构建入口页
};

// 异步函数：处理队伍公开状态变更
const handlePrivacyChange = async (newValue: boolean) => {
    // 如果是新建队伍，则不立即更新，状态会在创建时保存
     if (teamForm.id === null) {
         console.log("Privacy changed for new team. Will be saved on creation.");
         return;
     }
    loading.value = true; // 设置加载状态为 true
    try {
        // 调用服务方法更新队伍隐私设置
        await UserService.updateTeamPrivacy(teamForm.id.toString(), newValue);
        ElMessage.success(`团队已设置为${newValue ? '公开' : '私密'}。`); // 显示成功消息
    } catch (error: any) {
        console.error('Failed to update privacy:', error);
        // 显示更新失败的错误信息
        const msg = error?.response?.data?.message || '更新隐私设置失败。';
        ElMessage.error(msg);
        teamForm.is_public = !newValue; // 更新失败，恢复原来的公开状态
        ElMessage.info('隐私设置变更已取消。'); // 提示用户变更已取消
    } finally {
        loading.value = false; // 设置加载状态为 false
    }
};
</script>

<style scoped>
/* 队伍编辑视图容器样式 */
.team-builder-edit-view {
  max-width: 900px;
  margin: 30px auto;
  padding: 24px;
}
/* 队伍信息区域样式 */
.team-info {
  display: flex;
  gap: 24px;
  margin-bottom: 12px;
  font-size: 0.9em;
  color: #555;
}
/* 宝可梦 Tab 栏所在行容器样式 */
.pokemon-tab-bar-row {
  display: flex;
  flex-direction: row;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
  flex-wrap: wrap; /* 允许换行 */
}
/* 宝可梦 Tab 栏样式 */
.pokemon-tab-bar {
  display: flex;
  align-items: center;
  gap: 6px; /* Tab 之间的间距 */
  flex-wrap: nowrap; /* 不换行 */
  overflow-x: auto; /* 允许横向滚动 */
  padding-bottom: 5px;
  flex-grow: 1; /* 占据剩余空间 */
}
/* Tab 操作按钮容器样式 */
.tab-actions {
  margin-left: 16px;
  flex-shrink: 0; /* 不缩小 */
}
/* 宝可梦槽位（Tab）样式 */
.pokemon-slot {
  display: flex;
  align-items: center;
  border: 1px solid #dcdfe6;
  border-radius: 6px; /* 圆角 */
  padding: 8px 8px;
  background: #f5f7fa; /* 背景色 */
  cursor: pointer; /* 鼠标样式 */
  position: relative; /* 相对定位 */
  min-width: 100px;
  transition: all 0.2s ease-in-out; /* 过渡效果 */
  justify-content: center;
}
/* 宝可梦槽位鼠标悬停样式 */
.pokemon-slot:hover {
  border-color: #c0c4cc;
  box-shadow: 0 2px 8px rgba(0,0,0,0.05); /* 阴影效果 */
}
/* 选中状态的宝可梦槽位样式 */
.pokemon-slot.active {
  border-color: #409EFF;
  box-shadow: 0 0 0 2px rgba(64, 158, 255, 0.5); /* 蓝色外发光 */
  background: #e9f3ff; /* 浅蓝色背景 */
  color: #303133;
}
/* 宝可梦头像（精灵图）样式 */
.poke-avatar {
  width: 35px;
  height: 35px;
  margin-right: 8px;
  border-radius: 4px; /* 圆角 */
}
/* 宝可梦简略信息容器样式 */
.pokemon-brief {
  display: flex;
  flex-direction: column; /* 垂直排列 */
  font-size: 12px;
  line-height: 1.3;
  overflow: hidden; /* 隐藏溢出内容 */
}
/* 宝可梦名称样式 */
.pokemon-name {
  font-weight: 600;
  white-space: nowrap; /* 不换行 */
  text-overflow: ellipsis; /* 文本溢出显示省略号 */
  overflow: hidden;
  max-width: 80px; /* 最大宽度 */
}
/* 宝可梦道具名称样式 */
.pokemon-item {
  color: #606266;
  font-size: 11px;
  white-space: nowrap;
  text-overflow: ellipsis;
  overflow: hidden;
  max-width: 60px;
}
/* 移除宝可梦图标样式 */
.delete-icon {
  position: absolute; /* 绝对定位 */
  top: 4px;
  right: 4px;
  font-size: 14px;
  color: #909399;
  cursor: pointer;
  padding: 2px;
  border-radius: 50%; /* 圆形 */
  background-color: rgba(255, 255, 255, 0.6); /* 半透明白色背景 */
  visibility: hidden; /* 默认隐藏 */
  opacity: 0;
  transition: visibility 0.2s, opacity 0.2s; /* 过渡效果 */
}
/* 宝可梦槽位鼠标悬停时显示移除图标 */
.pokemon-slot:hover .delete-icon {
  visibility: visible;
  opacity: 1;
  color: #F56C6C; /* 红色 */
  background-color: rgba(253, 245, 245, 0.8);
}
/* 选中状态的宝可梦槽位悬停时显示移除图标 */
.pokemon-slot.active .delete-icon {
    visibility: visible;
    opacity: 1;
    color: #F56C6C;
    background-color: rgba(253, 245, 245, 0.8);
}
/* 添加宝可梦槽位样式 */
.add-slot {
}

/* 主要内容区域（宝可梦配置组件）样式 */
.main-content-single-column {
  border: 1px solid #ebeef5;
  border-radius: 4px;
  padding: 16px;
  background-color: #fdfdfd;
}

/* 拖拽经过时的宝可梦槽位样式 */
.pokemon-slot.drag-over-active {
/* 简单的拖放目标提示 */
/* 更复杂的提示可能涉及伪元素来实现前后指示线 */
outline: 2px dashed #409EFF; /* 蓝色虚线边框 */
outline-offset: 2px; /* 边框偏移 */
}

/* Style for the delete icon in pokemon slot */
/* 宝可梦槽位中移除图标的样式 (重复定义，保留第一个有效的) */
/* .pokemon-slot .delete-icon {
  position: absolute;
  top: 4px;
  right: 4px;
  font-size: 14px;
  color: #909399;
  cursor: pointer;
  padding: 2px;
  border-radius: 50%;
  background-color: rgba(255, 255, 255, 0.6);
  visibility: hidden;
  opacity: 0;
  transition: visibility 0.2s, opacity 0.2s;
} */
/* 宝可梦槽位鼠标悬停时显示移除图标 (重复定义，保留第一个有效的) */
/* .pokemon-slot:hover .delete-icon {
  visibility: visible;
  opacity: 1;
  color: #F56C6C;
  background-color: rgba(253, 245, 245, 0.8);
} */
/* 选中状态的宝可梦槽位中的占位符样式 */
.pokemon-slot.active .pokemon-icon-placeholder {
    color: #409EFF;
    background-color: #d9ecff;
}

/* 新增的公开状态开关容器样式 */
.el-card {
  position: relative; /* 使卡片成为绝对定位子元素的定位上下文 */
}

.public-switch-container {
  position: absolute; /* 绝对定位 */
  top: 20px; /* 根据卡片内边距调整顶部位置 */
  right: 20px; /* 根据卡片内边距调整右侧位置 */
  z-index: 10; /* 确保在其他内容之上 */
  font-size: 0.9em; /* 与其他信息文本大小一致 */
  color: #555; /* 与其他信息文本颜色一致 */
}

/* 底部按钮组样式 */
.button-group {
  display: flex;
  justify-content: center; /* 按钮居中 */
  margin-top: 20px; /* 可选：在按钮上方添加一些空间 */
  gap: 10px; /* 按钮之间的间距 */
}
</style>
