<template>
  <el-card class="team-builder-main-card" v-loading="loading">
    <template #header>
      <div class="card-header">
        <span>宝可梦团队构建器</span>
      </div>
    </template>

    <!-- Team Details Form -->
    <el-form :model="teamForm" label-width="100px" class="team-form">
      <el-row :gutter="20">
        <el-col :span="12">
          <el-form-item label="团队名称" required>
            <el-input v-model="teamForm.name" maxlength="20" placeholder="请输入团队名称" />
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="对战格式">
            <el-select v-model="teamForm.format" placeholder="请选择对战格式" style="width: 100%;">
              <el-option label="单打" value="Singles" />
              <el-option label="双打" value="Doubles" />
            </el-select>
          </el-form-item>
        </el-col>
      </el-row>
      <el-row :gutter="20">
        <el-col :span="12">
          <el-form-item label="游戏世代">
            <el-select v-model="teamForm.generation" placeholder="请选择世代" style="width: 100%;">
              <el-option label="第九世代" value="Gen 9" />
              <el-option label="第八世代" value="Gen 8" />
            </el-select>
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="自定义标签">
            <el-input v-model="tagInput" placeholder="输入标签后回车添加" @keyup.enter.native="addTag" />
            <div class="tag-list">
              <el-tag
                v-for="(tag, idx) in teamForm.custom_tags"
                :key="tag + idx"
                closable
                @close="removeTag(idx)"
                type="info"
                style="margin-right: 4px;"
              >{{ tag }}</el-tag>
            </div>
          </el-form-item>
        </el-col>
      </el-row>
    </el-form>

    <el-divider>团队概览</el-divider>
    
    <!-- Pokemon Slots -->
    <div class="pokemon-slots-container">
      <div
        v-for="(poke, index) in teamForm.pokemons"
        :key="poke.id"
        class="pokemon-slot"
        :class="{ active: currentPokemonIndex === index, dragging: draggedItemIndex === index }"
        @click="selectPokemon(index)"
        draggable="true" 
        @dragstart="dragStart(index, $event)"
        @dragover.prevent="dragOver($event, index)"
        @dragleave="dragLeave($event)"
        @drop.prevent="drop(index, $event)"
        @dragend="dragEnd($event)"
      >
        <img v-if="poke.sprite" :src="poke.sprite" :alt="poke.species_name_zh || 'sprite'" class="pokemon-slot-sprite" />
        <div v-else class="pokemon-icon-placeholder">{{ poke.species_name_zh ? poke.species_name_zh.substring(0,2) : '??' }}</div>
        <div class="pokemon-brief">
          <div class="pokemon-name">{{ poke.species_name_zh || '新宝可梦' }}</div>
          <div class="pokemon-item">{{ poke.item || '无道具' }}</div>
        </div>
      </div>
      <div
        v-if="teamForm.pokemons.length < 6"
        class="pokemon-slot empty"
        @click="addPokemonAndSelect"
      >
        <el-icon size="24"><Plus /></el-icon>
      </div>
    </div>

    <div class="team-actions" v-if="teamForm.pokemons.length > 0">
       <el-button type="primary" @click="handleSaveTeam">保存团队</el-button>
       <el-button @click="exportTeam">导出团队 (占位)</el-button>
    </div>
    <el-button v-else type="primary" @click="handleSaveTeam" style="margin-top: 10px;">保存空团队</el-button>


    <el-divider v-if="currentPokemonIndex !== null && teamForm.pokemons[currentPokemonIndex]">宝可梦配置</el-divider>
    
    <!-- Current Pokemon Configuration -->
    <div class="pokemon-config-area" v-if="currentPokemonIndex !== null && teamForm.pokemons[currentPokemonIndex]">
      <TeamPokemonConfig
        :pokemon="teamForm.pokemons[currentPokemonIndex]"
        :index="currentPokemonIndex"
        :generation="teamForm.generation"
        :version-group-id="selectedVersionGroupId"
        @remove="handleRemovePokemonFromConfig(currentPokemonIndex)"
        @update="updatePokemon(currentPokemonIndex, $event)"
      />
    </div>
    <div v-else-if="teamForm.pokemons.length > 0 && currentPokemonIndex === null" class="empty-config-prompt">
      <p>请从上方选择一个宝可梦进行配置。</p>
    </div>
     <div v-else-if="teamForm.pokemons.length === 0" class="empty-config-prompt">
      <p>队伍中还没有宝可梦，点击上方 "+" 添加一个吧！</p>
    </div>

  </el-card>
</template>

<script setup lang="ts">
import { ref, reactive, watch, computed, onMounted } from 'vue';
import { ElMessage, ElMessageBox, ElNotification } from 'element-plus';
import { Plus } from '@element-plus/icons-vue';
import TeamPokemonConfig from './TeamPokemonConfig.vue';
import UserService from '@/services/UserService';

const loading = ref(false);
const tagInput = ref('');
const currentPokemonIndex = ref<number | null>(null);
const generationsData = ref<any[]>([]); // To store generation and VG data
const selectedVersionGroupId = ref<number | null>(null);
const activePanelType = ref<string | null>(null);
const activeMoveSlotIndex = ref<number>(-1);

const teamForm = reactive({
  id: null as number | null,
  name: '',
  format: 'Singles',
  generation: 'Gen 9',
  custom_tags: [] as string[],
  pokemons: [] as any[],
});

// Initialize with one Pokemon for easier testing, can be removed
// if (teamForm.pokemons.length === 0) {
//   addPokemon();
//   currentPokemonIndex.value = 0;
// }


watch(() => teamForm.pokemons.length, (newLength) => {
  if (newLength === 0) {
    currentPokemonIndex.value = null;
  } else if (currentPokemonIndex.value === null || currentPokemonIndex.value >= newLength) {
    // If current index is invalid or null, and there are pokemons, select the last one or first one.
    // For now, let's default to selecting the first if one exists and nothing is selected.
    if (newLength > 0 && currentPokemonIndex.value === null) {
        // currentPokemonIndex.value = 0; // Optionally select first pokemon by default
    } else if (currentPokemonIndex.value !== null && currentPokemonIndex.value >= newLength) {
        currentPokemonIndex.value = newLength -1;
    }
  }
});

// Watch for changes in currentPokemonIndex to close panels
watch(currentPokemonIndex, (newIndex, oldIndex) => {
  // Only close if index actually changed and is not null
  if (newIndex !== oldIndex && newIndex !== null) {
    console.log(`Selected Pokemon index changed from ${oldIndex} to ${newIndex}. Closing active panel.`);
    activePanelType.value = null; // Close any active panel
    activeMoveSlotIndex.value = -1; // Reset move slot index
  }
});

// Fetch generations and version groups on mount
onMounted(async () => {
  try {
    generationsData.value = await UserService.getGenerationsWithVersionGroups();
    // Set a default version group based on the initial teamForm.generation
    updateSelectedVersionGroupId(teamForm.generation);
  } catch (error) {
    console.error("Failed to fetch generations data:", error);
    ElMessage.error("加载世代数据失败");
  }
});

// Watch for changes in teamForm.generation to update selectedVersionGroupId
watch(() => teamForm.generation, (newGenName) => {
  updateSelectedVersionGroupId(newGenName);
});

function updateSelectedVersionGroupId(generationName: string) {
  const currentGenData = generationsData.value.find(gen => gen.name === generationName.toLowerCase().replace('gen ', 'generation-'));
  if (currentGenData && currentGenData.version_groups.length > 0) {
    selectedVersionGroupId.value = currentGenData.version_groups[0].id; // Default to the first VG
    console.log(`Selected Version Group ID for ${generationName}: ${selectedVersionGroupId.value}`);
  } else {
    selectedVersionGroupId.value = null;
    console.warn(`No version group found for generation: ${generationName}`);
  }
}

function addTag() {
  if (tagInput.value && !teamForm.custom_tags.includes(tagInput.value)) {
    teamForm.custom_tags.push(tagInput.value);
    tagInput.value = '';
  }
}
function removeTag(idx: number) {
  teamForm.custom_tags.splice(idx, 1);
}

function addPokemon() {
  if (teamForm.pokemons.length < 6) {
    const newPokemon = {
      id: `local-${Date.now()}-${Math.random().toString(36).substring(2, 9)}`,
      localKey: Date.now() + Math.random(),
      species_id: '',
      species_name: '',
      species_name_zh: '', // Will be filled by TeamPokemonConfig or selection list
      level: 50,
      ability: '',
      item: '',
      nature: '',
      evs: { hp: 0, atk: 0, def: 0, spa: 0, spd: 0, spe: 0 },
      ivs: { hp: 31, atk: 31, def: 31, spa: 31, spd: 31, spe: 31 },
      moves: ['', '', '', ''], // Array of 4 move names or IDs
    };
    teamForm.pokemons.push(newPokemon);
    return teamForm.pokemons.length - 1; // Return index of new Pokemon
  }
  return null; // Indicate failure if team is full
}

function addPokemonAndSelect() {
  const newIndex = addPokemon();
  if (newIndex !== null) {
    currentPokemonIndex.value = newIndex;
  } else {
    ElMessage.warning('队伍已满，无法添加更多宝可梦！');
  }
}

function selectPokemon(idx: number) {
  currentPokemonIndex.value = idx;
}

function removePokemon(idx: number) {
  if (idx < 0 || idx >= teamForm.pokemons.length) return;
  const removedPokemonId = teamForm.pokemons[idx].id;
  teamForm.pokemons.splice(idx, 1);

  if (teamForm.pokemons.length === 0) {
    currentPokemonIndex.value = null;
  } else {
    if (currentPokemon.value?.id === removedPokemonId) {
        // If the removed Pokemon was the selected one, try to select the next, or previous, or null if none
        if (idx < teamForm.pokemons.length) {
            currentPokemonIndex.value = idx;
        } else if (teamForm.pokemons.length > 0) {
            currentPokemonIndex.value = teamForm.pokemons.length - 1;
        } else {
            currentPokemonIndex.value = null;
        }
    } else {
        // If a different Pokemon was selected, update its index if necessary
        const selectedId = currentPokemon.value?.id;
        if (selectedId) {
            const newIdx = teamForm.pokemons.findIndex(p => p.id === selectedId);
            currentPokemonIndex.value = newIdx !== -1 ? newIdx : null;
        } else {
            currentPokemonIndex.value = null; // Should not happen if a pokemon was selected
        }
    }
  }
}

function handleRemovePokemonFromConfig(idx: number) {
    ElMessageBox.confirm(
    `确定要从队伍中移除 ${teamForm.pokemons[idx]?.species_name_zh || '该宝可梦'} 吗?`,
    '确认移除',
    {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning',
    }
  ).then(() => {
    removePokemon(idx);
    ElMessage.success('宝可梦已移除');
  }).catch(() => {
    // User cancelled
  });
}


function updatePokemon(idx: number, data: any) {
  if (currentPokemonIndex.value !== null && teamForm.pokemons[idx]) {
    teamForm.pokemons[idx] = { ...teamForm.pokemons[idx], ...data };
  }
}

async function handleSaveTeam() {
  if (!teamForm.name) {
    ElMessage.error('请输入团队名称！');
    return;
  }
  // Basic validation for at least one Pokemon if not allowing empty save.
  // if (teamForm.pokemons.length === 0) {
  //   ElMessage.error('队伍中至少需要一只宝可梦！');
  //   return;
  // }

  loading.value = true;
  try {
    // Ensure localKey is not sent to backend if it's purely a frontend helper
    const pokemonsToSave = teamForm.pokemons.map(p => {
      const { localKey, ...rest } = p;
      // --- Start: Modified moves handling for backend --- 确保发送给后端的moves数据是字符串数组
      const movesToSend: string[] = []; // Explicitly define type as string array
      if (rest.moves && Array.isArray(rest.moves)) {
          rest.moves.forEach((move: any) => {
              let moveName = '';
              if (move && typeof move === 'object') {
                  // Prefer move_name_zh, fallback to name_zh if needed
                  moveName = move.move_name_zh || move.name_zh || '';
              } else if (typeof move === 'string') {
                  // If it's already a string, use it
                  moveName = move;
              }
              // Add non-empty string names to the array
              if (moveName) {
                  movesToSend.push(String(moveName)); // Ensure it's a string
              }
          });
      }
      // --- End: Modified moves handling for backend ---

      return { ...rest, moves: movesToSend }; // Replace the original moves array
    });

    let responseData;
    if (teamForm.id !== null) {
      // If teamForm has an id, it's an update
      responseData = await UserService.updateTeam(teamForm.id.toString(), {
        name: teamForm.name,
        format: teamForm.format,
        generation: teamForm.generation,
        custom_tags: teamForm.custom_tags,
        // --- Start: Ensure moves is a plain string array for backend --- 张大队，强制转换为普通数组
        pokemons: pokemonsToSave.map(p => ({
            ...p,
            moves: JSON.parse(JSON.stringify(p.moves))
        })),
        // --- End: Ensure moves is a plain string array for backend ---
        // Assuming updateTeam can also handle is_public if needed
      });
       ElMessage.success('团队更新成功！');
    } else {
      // Otherwise, it's a creation
      responseData = await UserService.createTeam({
        name: teamForm.name,
        format: teamForm.format,
        generation: teamForm.generation,
        custom_tags: teamForm.custom_tags,
        pokemons: pokemonsToSave,
        // is_public defaults to True in backend createTeam, no need to send here unless overriding
      });
       ElMessage.success('团队创建成功！');
       // If creation is successful, set the ID for future updates (if staying on the same page)
       if (responseData && responseData.id) {
            teamForm.id = responseData.id;
       }
    }

  } catch (e: any) {
    const msg = e?.response?.data?.message || '保存失败';
    ElMessage.error(msg);
  } finally {
    loading.value = false;
  }
}

function exportTeam() {
  // Placeholder for export functionality
  ElMessage.info('导出功能暂未实现。');
  console.log('Export team data:', JSON.stringify(teamForm));
}

// --- Drag and Drop Logic ---
let draggedItemIndex = -1;

function dragStart(index: number, event: DragEvent) {
  draggedItemIndex = index;
  if (event.dataTransfer) {
    event.dataTransfer.effectAllowed = 'move';
    event.dataTransfer.setData('text/plain', index.toString()); // Required for Firefox
    // Optional: add a class to the dragged item for visual feedback
    const el = event.target as HTMLElement;
    if(el) el.classList.add('dragging');
  }
}

function dragOver(event: DragEvent, targetIndex: number) {
  event.preventDefault();
  if (event.dataTransfer) {
    event.dataTransfer.dropEffect = 'move';
  }
  // Optional: visual feedback for drop target
  const el = event.currentTarget as HTMLElement;
  if(el && !el.classList.contains('drag-over-active')) {
    // Basic visual cue, can be more sophisticated with before/after indicators
    // el.classList.add('drag-over-active'); 
  }
}

function dragLeave(event: DragEvent) {
    const el = event.currentTarget as HTMLElement;
    // if(el) el.classList.remove('drag-over-active');
}

function drop(targetIndex: number, event: DragEvent) {
  event.preventDefault();
  // const el = event.currentTarget as HTMLElement;
  // if(el) el.classList.remove('drag-over-active');
  // if(event.target && (event.target as HTMLElement).classList.contains('dragging')){
  //   (event.target as HTMLElement).classList.remove('dragging');
  // }

  if (draggedItemIndex === -1 || draggedItemIndex === targetIndex) {
    draggedItemIndex = -1;
    return; // No change or dropping on itself
  }

  const selectedPokemonIdBeforeDrag = currentPokemon.value?.id;

  const itemToMove = teamForm.pokemons.splice(draggedItemIndex, 1)[0];
  teamForm.pokemons.splice(targetIndex, 0, itemToMove);

  // Update currentPokemonIndex to follow the moved item or stay correct
  if (selectedPokemonIdBeforeDrag) {
    const newIdxOfSelected = teamForm.pokemons.findIndex(p => p.id === selectedPokemonIdBeforeDrag);
    if (newIdxOfSelected !== -1) {
      currentPokemonIndex.value = newIdxOfSelected;
    } else {
      // This case should ideally not happen if the selected pokemon is part of the list
      currentPokemonIndex.value = null; 
    }
  } else {
    currentPokemonIndex.value = null; // No pokemon was selected, or it was removed
  }
  
  draggedItemIndex = -1; // Reset for next drag operation
  
  // Minimal visual feedback
  ElNotification({
    title: '排序成功',
    message: '宝可梦顺序已更新。',
    type: 'success',
    duration: 2000,
  });
}

function dragEnd(event: DragEvent) {
    // Clean up dragging class if it was added
    const el = event.target as HTMLElement;
    if(el) el.classList.remove('dragging');
    draggedItemIndex = -1; // Ensure reset
}

// Helper to get current selected Pokemon object reactively
const currentPokemon = computed(() => {
  if (currentPokemonIndex.value !== null && teamForm.pokemons[currentPokemonIndex.value]) {
    return teamForm.pokemons[currentPokemonIndex.value];
  }
  return null;
});

// Ensure currentPokemonIndex is valid on initial load or external changes
// This watch needs to be robust, especially with IDs
watch(() => teamForm.pokemons, (newPokemons, oldPokemons) => {
  if (currentPokemon.value) {
    const stillExists = newPokemons.find(p => p.id === currentPokemon.value!.id);
    if (!stillExists) {
      // Selected Pokemon was removed (e.g. by an external action not covered by removePokemon)
      currentPokemonIndex.value = newPokemons.length > 0 ? 0 : null; // Default to first or null
    } else {
      // Update index if it shifted but Pokemon still exists
      const newIdx = newPokemons.findIndex(p => p.id === currentPokemon.value!.id);
      if (newIdx !== -1 && newIdx !== currentPokemonIndex.value) {
        currentPokemonIndex.value = newIdx;
      }
    }
  } else if (newPokemons.length > 0 && currentPokemonIndex.value === null) {
    // If no Pokemon is selected and there are Pokemons, optionally select the first one.
    // currentPokemonIndex.value = 0; 
  }
}, { deep: true });

</script>

<style scoped>
.team-builder-main-card {
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

.team-form .el-row {
  margin-bottom: 0; /* Reduce default el-form-item margin */
}
.team-form .el-form-item {
  margin-bottom: 18px; /* Standard margin for form items */
}

.tag-list {
  margin-top: 8px;
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
}

.pokemon-slots-container {
  display: flex;
  flex-wrap: wrap; /* Allow wrapping if more than 6, though we limit to 6 */
  gap: 10px; /* Space between slots */
  margin-top: 20px;
  margin-bottom: 20px;
  padding: 10px;
  border: 1px solid #ebeef5;
  border-radius: 4px;
  background-color: #fcfcfc;
  justify-content: center; /* Center the pokemon slots horizontally */
}

.pokemon-slot {
  width: 120px; /* Adjust as needed */
  height: 100px; /* Adjust as needed */
  border: 2px solid #dcdfe6;
  border-radius: 8px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.2s ease-in-out;
  background-color: #fff;
  box-shadow: 0 2px 4px rgba(0,0,0,0.05);
}

.pokemon-slot:hover {
  border-color: #409EFF;
  box-shadow: 0 4px 12px rgba(0,0,0,0.1);
}

.pokemon-slot.active {
  border-color: #409EFF;
  box-shadow: 0 0 0 2px #409EFF, 0 4px 12px rgba(64,158,255,0.3);
  background-color: #ecf5ff;
}

.pokemon-slot.empty {
  border-style: dashed;
  color: #909399;
}
.pokemon-slot.empty:hover {
  color: #409EFF;
  border-color: #409EFF;
}

/* Drag and Drop Styles */
.pokemon-slot.dragging {
  opacity: 0.5;
  border-style: dashed;
  border-color: #ff69b4; /* Hot pink for visibility during drag */
}

.pokemon-slot.drag-over-active {
  /* background-color: #e6f7ff; Simple cue for drop target */
  /* More complex indicators might involve pseudo-elements for before/after lines */
  outline: 2px dashed #409EFF;
  outline-offset: 2px;
}

.pokemon-icon-placeholder {
  font-size: 2em;
  color: #c0c4cc;
  margin-bottom: 8px;
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: #f0f2f5;
  border-radius: 50%;
}
.pokemon-slot.active .pokemon-icon-placeholder {
    color: #409EFF;
    background-color: #d9ecff;
}

.pokemon-slot-sprite {
  width: 60px; /* Adjust size as needed */
  height: 60px; /* Adjust size as needed */
  object-fit: contain;
  margin-bottom: 8px;
}

.pokemon-brief {
  text-align: center;
  font-size: 0.85em;
}

.pokemon-name {
  font-weight: bold;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 100px;
}

.pokemon-item {
  font-size: 0.9em;
  color: #606266;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 100px;
}

.team-actions {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end; /* Align buttons to the right */
  gap: 10px;
}

.pokemon-config-area {
  margin-top: 20px;
  padding: 15px;
  border: 1px solid #e4e7ed;
  border-radius: 4px;
  background-color: #fdfdfd;
}
.empty-config-prompt {
  margin-top: 20px;
  padding: 20px;
  text-align: center;
  color: #909399;
  background-color: #f9f9f9;
  border-radius: 4px;
}

/* Style for the delete icon in pokemon slot */
.pokemon-slot .el-icon-delete {
  color: #f56c6c; /* A strong red color */
  margin-left: 8px; /* Add some space between pokemon brief and delete icon */
  cursor: pointer;
}

.pokemon-slot.active .pokemon-icon-placeholder {
    color: #409EFF;
    background-color: #d9ecff;
}

</style>
