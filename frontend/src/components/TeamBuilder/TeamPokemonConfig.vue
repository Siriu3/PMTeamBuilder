<template>
  <el-card class="pokemon-config-card" shadow="hover">
    <div class="config-content-wrapper">
      <!-- Main Layout: Image, Info, Moves/Stats -->
      <div class="pokemon-main-layout">
        <!-- Left: Image & Types -->
        <div class="poke-img-col">
          <img v-if="editablePokemon.sprite" :src="editablePokemon.sprite" :alt="editablePokemon.species_name_zh" class="poke-img" />
          <div v-else class="poke-img-placeholder">?</div>
          <div class="poke-types">
            <AttributeIcon 
              v-for="t in editablePokemon.types" 
              :key="t" 
              :type="t" 
              class="config-type-icon scaled-attribute-icon-config"
              style="margin-bottom: 5px;"
            />
          </div>
        </div>

        <!-- Middle: Name, Item, Ability, Nature, Tera -->
        <div class="poke-info-col">
          <el-form-item label="宝可梦">
            <el-input 
              :value="editablePokemon.species_name_zh || '请选择'" 
              readonly 
              placeholder="点击选择宝可梦"
              @click="openPanel('pokemon', -1)" 
              class="config-input-selector"
            />
          </el-form-item>
          <el-form-item label="道具">
            <div class="config-input-with-icon">
              <img v-if="editablePokemon.item_sprite" :src="editablePokemon.item_sprite" :alt="editablePokemon.item" class="config-item-icon" />
              <el-input 
                :value="editablePokemon.item || '请选择'" 
                readonly 
                placeholder="点击选择道具"
                @click="openPanel('item', -1)" 
                class="config-input-selector"
                :disabled="!editablePokemon.species_id"
              />
            </div>
          </el-form-item>
          <el-form-item label="特性">
            <el-input 
              :value="editablePokemon.ability || '请选择'" 
              readonly 
              placeholder="点击选择特性"
              @click="openPanel('ability', -1)" 
              class="config-input-selector"
              :disabled="!editablePokemon.species_id"
            />
          </el-form-item>
           <el-form-item label="性格">
            <el-input 
              :value="editablePokemon.nature || '请选择'" 
              readonly 
              placeholder="点击选择性格"
              @click="openPanel('nature', -1)" 
              class="config-input-selector"
              :disabled="!editablePokemon.species_id"
            />
          </el-form-item>
          <el-form-item label="太晶属性" v-if="showTeraType">
            <el-input 
              :value="teraTypeZh[editablePokemon.tera_type] || editablePokemon.tera_type || '请选择'" 
              readonly 
              placeholder="点击选择太晶属性"
              @click="openPanel('tera', -1)" 
              class="config-input-selector"
              :disabled="!editablePokemon.species_id"
            />
          </el-form-item>
        </div>

        <!-- Right: Moves & Stats Overview -->
        <div class="poke-moves-stats-col">
          <div class="moves-section">
            <div class="moves-label">招式</div>
            <div class="poke-moves-inputs">
              <el-input 
                v-for="(mv, i) in editablePokemon.moves" 
                :key="i" 
                :value="editablePokemon.moves[i]?.move_name_zh || editablePokemon.moves[i]?.name_zh || editablePokemon.moves[i] || `选择招式 ${i+1}`" 
                readonly 
                placeholder="点击选择招式"
                @click="openPanel('move', i)" 
                class="config-input-selector poke-move-input"
                :disabled="!editablePokemon.species_id"
              />
            </div>
          </div>
          <!-- Stats section -->
          <div class="stats-section-content">
            <div class="stats-label">能力值</div>
            <div 
              class="poke-stats-overview"
              @click="openPanel('stats', -1)"
              :class="{'disabled-stats-overview': !editablePokemon.species_id}"
              :style="{'cursor': !editablePokemon.species_id ? 'not-allowed' : 'pointer'}"
            >
              <div class="stat-bar-row" v-for="sKey in statKeys" :key="sKey">
                <span class="stat-label">{{ statLabelZh[sKey] }}</span>
                <!-- Hide bar and value if base stat is 0 or missing -->
                <template v-if="editablePokemon.base_stats?.[sKey]">
                  <div class="stat-bar-bg">
                    <div class="stat-bar" :style="statBarStyle(sKey)"></div>
                  </div>
                  <span class="stat-value">{{ calculatedStats[sKey]?.value || 0 }}</span>
                </template>
                <!-- Show placeholder or nothing if base stat is 0 or missing -->
                <template v-else>
                    <div class="stat-bar-bg" style="visibility: hidden; flex-grow: 1;"></div> <!-- Keep space -->
                    <span class="stat-value" style="visibility: hidden; width: 22px;"></span> <!-- Keep space -->
                </template>
                <!-- Show EV if EV is > 0, otherwise show a hidden placeholder -->
                <span class="stat-ev" v-if="(editablePokemon.evs?.[sKey] || 0) > 0">{{ editablePokemon.evs?.[sKey] }}</span>
                <span class="stat-ev" v-else style="visibility: hidden;">000</span> <!-- Hidden placeholder for width -->
                <span class="stat-nature" :class="natureClass(sKey)">{{ natureSymbol(sKey) }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
      
      <!-- Action Button for Removal -->
    </div>

    <!-- Inline Panel Area -->
    <div v-if="activePanelType" class="inline-panel-area">
      <el-card shadow="inner" class="inline-panel-card">
        <template #header v-if="activePanelType !== 'stats'">
          <div class="inline-panel-header">
            <span class="panel-header-title">{{ panelTitle }}</span>
            <el-button circle type="danger" :icon="CloseBold" @click="closeActivePanel" size="small"></el-button>
          </div>
        </template>
        <PokemonStatPanel 
          v-if="activePanelType === 'stats'" 
          :pokemon="editablePokemon" 
          @update="handleStatUpdate" 
          @close="closeActivePanel"
        />
        <SelectionPanel 
          v-else-if="activePanelType" 
          :type="activePanelType" 
          :current-pokemon-data="editablePokemon" 
          :generation="props.generation" 
          :version-group-id="props.versionGroupId"
          :selected-moves="activePanelType === 'move' ? editablePokemon.moves : undefined"
          @select="handlePanelSelection"
          @close="closeActivePanel" 
        />
      </el-card>
    </div>

    <!-- Moved Action Button for Removal to top right -->
    <div class="remove-button-container">
      <el-button type="danger" plain @click="$emit('remove')" size="small">从队伍移除</el-button>
    </div>
  </el-card>
</template>

<script setup lang="ts">
import { ref, computed, watch, reactive } from 'vue';
import { CloseBold } from '@element-plus/icons-vue';
import PokemonStatPanel from './PokemonStatPanel.vue';
import SelectionPanel from './SelectionPanel.vue';
import AttributeIcon from './AttributeIcon.vue'; // Import the AttributeIcon component
import { ElMessage } from 'element-plus';
import { typeZhMap } from '@/utils/constants';

const props = defineProps<{
  pokemon: any;
  index: number;
  generation?: string;
  versionGroupId?: number | null;
}>();

const emit = defineEmits(['remove', 'update']);

const NATURE_EFFECTS: Record<string, { increased: string | null, decreased: string | null }> = {
  // Format: NatureName: { increased: 'stat_key', decreased: 'stat_key' }
  // HP is never affected by nature
  '固执': { increased: 'atk', decreased: 'spa' }, '怕寂寞': { increased: 'atk', decreased: 'def' },
  '顽皮': { increased: 'atk', decreased: 'spd' }, '勇敢': { increased: 'atk', decreased: 'spe' },
  '大胆': { increased: 'def', decreased: 'atk' }, '悠闲': { increased: 'def', decreased: 'spe' },
  '淘气': { increased: 'def', decreased: 'spa' }, '乐天': { increased: 'def', decreased: 'spd' }, //淘气 Impish, 乐天 Lax
  '内敛': { increased: 'spa', decreased: 'atk' }, '慢吞吞': { increased: 'spa', decreased: 'spe' },
  '马虎': { increased: 'spa', decreased: 'spd' }, '冷静': { increased: 'spa', decreased: 'def' }, //冷静 Quiet, not 马虎 Rash (马虎 is +SpA, -SpD)
  // Corrected 马虎 (Rash) based on common knowledge if image is ambiguous for it, typically +SpA, -SpD
  // Image: 马虎 -> 特攻 / 特防. If 特防 is decreased, then it is Rash.
  // Image: 冷静 -> 特攻 / 速度. This is Quiet.
  '温和': { increased: 'spd', decreased: 'atk' }, '温顺': { increased: 'spd', decreased: 'def' }, //温顺 Gentle
  '慎重': { increased: 'spd', decreased: 'spa' }, '自大': { increased: 'spd', decreased: 'spe' }, //自大 Sassy
  '胆小': { increased: 'spe', decreased: 'atk' }, '急躁': { increased: 'spe', decreased: 'def' }, //急躁 Hasty
  '爽朗': { increased: 'spe', decreased: 'spa' }, '天真': { increased: 'spe', decreased: 'spd' }, //天真 Naive
  // Neutral Natures
  '勤奋': { increased: null, decreased: null }, '坦率': { increased: null, decreased: null },
  '害羞': { increased: null, decreased: null }, '浮躁': { increased: null, decreased: null },
  '认真': { increased: null, decreased: null },
};

// Use a reactive copy for local edits to avoid directly mutating props
// This is crucial if prop is an object/array from parent's reactive state
const editablePokemon = reactive<any>({ ...props.pokemon });

watch(() => props.pokemon, (val) => {
  if (val) {
    // Reset evs and ivs to default or from new pokemon data
    // Object.assign(editablePokemon, val);
    // To ensure full reset of old properties like item_sprite, replace the reactive object
    // Or use Object.assign after clearing old properties if necessary. Replacing is cleaner.
    // Alternatively, explicitly set properties to default/null if not present in new data.

    // Clear the existing reactive object properties
    for (const key in editablePokemon) {
        if (editablePokemon.hasOwnProperty(key)) {
            delete editablePokemon[key];
        }
    }
    // Assign new properties from the updated prop value
    Object.assign(editablePokemon, val);

    // === 汉化属性（types）字段 ===
    if (editablePokemon.types && Array.isArray(editablePokemon.types)) {
        editablePokemon.types = editablePokemon.types.map((type: string) => typeZhMap[type.toLowerCase()] || type);
    }
    // ===========================

    // Ensure default structure if needed (e.g., for new empty pokemon slots)
    if (!editablePokemon.evs) editablePokemon.evs = {hp:0,atk:0,def:0,spa:0,spd:0,spe:0};
    if (!editablePokemon.ivs) editablePokemon.ivs = {hp:31,atk:31,def:31,spa:31,spd:31,spe:31};
    if (!editablePokemon.moves) editablePokemon.moves = Array(4).fill(null); // Ensure moves is an array
    // Ensure abilities is an array, even if empty
    if (!editablePokemon.abilities) editablePokemon.abilities = [];

    // === Fetch item sprite if item exists but sprite is missing ===
    if (editablePokemon.item && !editablePokemon.item_sprite && editablePokemon.item !== '请选择') {
       console.log('Fetching item details for item:', editablePokemon.item);
       // Assuming UserService has a method to get item details by name or ID
       // Let's add a new method to UserService to get item details by name
       // For now, let's add a placeholder comment about needing this service method
       // TODO: Implement UserService.getItemDetailsByName in frontend/src/services/UserService.ts
       // Call the service method and update item_sprite
       // Example (requires UserService modification):
       /*
       try {
           const itemDetails = await UserService.getItemDetailsByName(editablePokemon.item);
           if (itemDetails && itemDetails.sprite) {
               editablePokemon.item_sprite = itemDetails.sprite; // Update the sprite
               console.log('Fetched item sprite:', itemDetails.sprite);
           }
       } catch (error) {
           console.error('Failed to fetch item details:', error);
       }
       */
       // As a temporary workaround for demonstration/testing without the service call:
       // You would need a mapping from item name to sprite URL here on the frontend
       // Or preferably, implement the backend/frontend service call.
       // For now, we just log the attempt.
    }
    // ================================================================

    // --- Start: Debug Print ---
    console.log('TeamPokemonConfig: props.pokemon updated. Checking editablePokemon moves:');
    console.log('  Moves:', editablePokemon.moves);
    console.log('  Item Sprite:', editablePokemon.item_sprite);
    console.log('  Base Stats:', editablePokemon.base_stats);
    // --- End: Debug Print ---
  }
}, { immediate: true, deep: true });

const statKeys = ['hp', 'atk', 'def', 'spa', 'spd', 'spe'];
const statLabelZh: Record<string, string> = { hp: 'HP', atk: '攻击', def: '防御', spa: '特攻', spd: '特防', spe: '速度' };

const activePanelType = ref<string | null>(null);
const activeMoveSlotIndex = ref<number>(-1); // To know which move slot is being edited

const showTeraType = computed(() => {
  // Ensure generation is treated as a string for comparison, handle potential null/undefined
  // Use the generation prop directly
  const gen = props.generation?.toString().toLowerCase();
  return gen === 'gen 9' || gen === '9'; // Compare with both 'gen 9' and '9' as string
});

const panelTitle = computed(() => {
  if (!activePanelType.value) return '';
  switch (activePanelType.value) {
    case 'pokemon': return '请选择宝可梦';
    case 'item': return '选择道具';
    case 'ability': return '选择特性';
    case 'nature': return '选择性格';
    case 'move': return `选择招式 ${activeMoveSlotIndex.value + 1}`;
    case 'tera': return '选择太晶属性';
    case 'stats': return '编辑能力值'; // Though StatPanel has its own title
    default: return '选择';
  }
});

function openPanel(type: string, moveIndex: number = -1) {
  // Prevent opening other panels if total EVs exceed 508
  if (type !== 'pokemon' && type !== 'stats') {
      const currentTotalEv = statKeys.reduce((sum, k) => sum + (editablePokemon.evs?.[k] || 0), 0);
      if (currentTotalEv > 508) {
          ElMessage.warning("努力值总和超出上限 (508)，请先调整。");
          return; // Prevent opening the panel
      }
  }
  // Only allow opening panels if a Pokemon is selected, or if the panel type is 'pokemon'
  if (!editablePokemon.species_id && type !== 'pokemon') {
    // Optionally, provide visual feedback to the user, e.g., a toast message
    // ElMessage.warning("请先选择宝可梦");
    console.log("Attempted to open panel without selected Pokemon:", type);
    return; // Prevent opening the panel
  }

  // === Check abilities before opening ability panel ===
  // We expect abilities to be in editablePokemon after backend change for imported teams.
  // Adding a log to verify if abilities data is present.
  if (type === 'ability' && editablePokemon.species_id) {
    console.log('Abilities in editablePokemon before opening panel:', editablePokemon.abilities);
    // If the above log shows empty/undefined, the issue is how imported data gets into editablePokemon,
    // or how the watch effect updates it.
    // If the above log shows data, the issue is in SelectionPanel component logic.
  }
  // ====================================================

  activePanelType.value = type;
  if (type === 'move') {
    activeMoveSlotIndex.value = moveIndex;
  }
}

function closeActivePanel() {
  activePanelType.value = null;
  activeMoveSlotIndex.value = -1;
}

function handlePanelSelection(selectedData: any) {
  let updatedData: Partial<any> = {};

  switch (activePanelType.value) {
    case 'pokemon':
      updatedData = {
        species_id: selectedData.id, // Assuming backend ID for species
        species_name: selectedData.name, // English name from selection
        species_name_zh: selectedData.name_zh, // Chinese name
        sprite: selectedData.sprite,
        types: selectedData.types,
        base_stats: selectedData.base_stats, // Make sure this structure matches
        abilities: selectedData.abilities, // This might be an array of possible abilities
        // Reset other fields that depend on species if necessary
        ability: '', item: '', nature: '', tera_type: '', moves: Array(4).fill(null), evs: {hp:0,atk:0,def:0,spa:0,spd:0,spe:0}, ivs: {hp:31,atk:31,def:31,spa:31,spd:31,spe:31}
      };
      break;
    case 'item':
      // Ensure item sprite URL is encoded to prevent URI malformed errors
      const encodedItemSprite = selectedData.sprite ? encodeURI(selectedData.sprite) : null;
      updatedData = { item: selectedData.name_zh, item_sprite: encodedItemSprite }; // Store name or full object?
      break;
    case 'ability':
      // Ensure selectedData is the expected ability name string
      if (typeof selectedData === 'string') {
          updatedData = { ability: selectedData }; 
      } else {
          // If received data is not a string, log a warning or try to extract from object
          console.warn('Received unexpected data format for ability selection:', selectedData);
          // Attempt to extract Chinese name from object if selectedData is an object with name_zh
          if (selectedData && typeof selectedData === 'object' && selectedData.name_zh) {
               updatedData = { ability: selectedData.name_zh };
          } else {
               // Cannot process data format, do not update ability
               console.error('Failed to extract ability name from selected data.');
               return; // Do not continue updating
          }
      }
      break;
    case 'nature':
      updatedData = { nature: selectedData }; // Assuming selectedData is the nature string
      break;
    case 'move':
      if (activeMoveSlotIndex.value !== -1) {
        const newMoves = [...editablePokemon.moves];
        // Store the full move object returned from SelectionPanel
        // SelectionPanel returns move objects with name_zh or move_name_zh
        const chineseName = selectedData?.name_zh || selectedData?.move_name_zh; // Prioritize name_zh from SelectionPanel result, fallback to move_name_zh
        const moveId = selectedData?.id; // Get move ID if available

        if (chineseName) {
             // Store only the necessary data: Chinese name and ID
             newMoves[activeMoveSlotIndex.value] = reactive({ move_name_zh: chineseName, move_id: moveId }); // Store as object with chinese name and id
        } else {
             // If selection is cleared or invalid, set to null
             newMoves[activeMoveSlotIndex.value] = null;
        }
        updatedData = { moves: newMoves };
      }
      break;
    case 'tera':
      updatedData = { tera_type: selectedData }; // Assuming selectedData is the type string
      break;
  }
  
  Object.assign(editablePokemon, updatedData);
  emit('update', { ...editablePokemon }); // Emit the whole updated pokemon object
  closeActivePanel();
}

function handleStatUpdate(statData: { evs?: any, ivs?: any, level?: number }) {
  console.log('Received stat update in config:', statData);
  Object.assign(editablePokemon, statData);
  console.log('editablePokemon after update:', editablePokemon);
  emit('update', { ...editablePokemon });
  // Stat panel might have its own close, or we can close it here if needed
  // closeActivePanel(); 
}

// --- Stat Display Calculation (Simplified, real calc in PokemonStatPanel) ---
const calculatedStats = computed(() => {
  console.log('Recalculating stats for:', editablePokemon.species_name_zh, 'EVs:', editablePokemon.evs, 'IVs:', editablePokemon.ivs, 'Level:', editablePokemon.level);
  const stats: Record<string, {value: number}> = {};
  statKeys.forEach(key => {
    const base = editablePokemon.base_stats?.[key] || 0;
    const ev = editablePokemon.evs?.[key] || 0;
    const iv = editablePokemon.ivs?.[key] ?? 31;
    const level = editablePokemon.level || 50;
    let finalVal = 0;

    const natureEffect = NATURE_EFFECTS[editablePokemon.nature || ''] || { increased: null, decreased: null };
    let natureMultiplier = 1.0;
    if (natureEffect.increased === key) {
      natureMultiplier = 1.1;
    } else if (natureEffect.decreased === key) {
      natureMultiplier = 0.9;
    }

    if (key === 'hp') {
        finalVal = base === 1 ? 1 : Math.floor(((base * 2 + iv + Math.floor(ev / 4)) * level) / 100) + 10 + level;
    } else {
        finalVal = Math.floor(((Math.floor((base * 2 + iv + Math.floor(ev / 4)) * level / 100) + 5) * natureMultiplier));
    }
    stats[key] = { value: finalVal };
  });
   console.log('Calculated stats result:', stats);
  return stats;
});

const totalEVs = computed(() => {
  if (!editablePokemon.evs) return 0;
  return statKeys.reduce((sum, key) => sum + (editablePokemon.evs[key] || 0), 0);
});

function statBarStyle(stat: string) {
  const val = calculatedStats.value[stat]?.value || 0;
  const level = editablePokemon.level || 50; // 获取等级，默认为 50

  let maxStatValue: number;
  if (level <= 50) {
    maxStatValue = 200;
  } else if (level <= 80) { // 包含 51-80 级
    maxStatValue = 325;
  } else { // 包含 81-100+ 级
    maxStatValue = 450;
  }

  const percentage = Math.min(100, (val / maxStatValue) * 100);
  return { width: percentage + '%', backgroundColor: statColor(stat) };
}

function statColor(stat: string) {
  const colors: Record<string, string> = { hp: '#78C850', atk: '#C03028', def: '#6890F0', spa: '#A040A0', spd: '#edbf08', spe: '#F85888' };
  return colors[stat] || '#ccc';
}

function natureClass(statKey: string): string {
  if (!editablePokemon.nature) return '';
  const effect = NATURE_EFFECTS[editablePokemon.nature];
  if (effect) {
    if (effect.increased === statKey) return 'nature-plus';
    if (effect.decreased === statKey) return 'nature-minus';
  }
  return '';
}

function natureSymbol(statKey: string): string {
  if (!editablePokemon.nature) return '';
  const effect = NATURE_EFFECTS[editablePokemon.nature];
  if (effect) {
    if (effect.increased === statKey) return '+';
    if (effect.decreased === statKey) return '-';
  }
  return '';
}

/* Add Tera Type Chinese Mapping */
const teraTypeZh: Record<string, string> = {
    'Normal': '一般', 'Fire': '火', 'Water': '水', 'Grass': '草', 'Electric': '电', 'Ice': '冰',
    'Fighting': '格斗', 'Poison': '毒', 'Ground': '地面', 'Flying': '飞行', 'Psychic': '超能力', 'Bug': '虫',
    'Rock': '岩石', 'Ghost': '幽灵', 'Dragon': '龙', 'Dark': '恶', 'Steel': '钢', 'Fairy': '妖精',
    'Stellar': '星晶'
};

</script>

<style scoped>
.poke-info-col .el-form-item {
  margin-bottom: 6px; /* Tighter form items */
}
.poke-info-col {
  margin-left: 0px;
}

/* Style for form item labels */
:deep(.el-form-item__label) {
  font-weight: bold;
}

.config-input-with-icon {
  display: flex;
  align-items: center;
  width: 100%;
}

.config-item-icon {
  width: 24px; /* Adjust size as needed */
  height: 24px; /* Adjust size as needed */
  object-fit: contain;
  margin-right: 8px; /* Space between icon and input */
  background-color: #f0f2f5; /* Light background for icon */
  border-radius: 4px;
  padding: 2px;
}

.config-input-selector {
  cursor: pointer;
  width: 100%; /* Make input take full width of its container */
}
.config-input-selector .el-input__inner {
  cursor: pointer !important;
}

.pokemon-config-card {
  position: relative; /* For potential absolute positioning of panels if needed later */
}

.config-content-wrapper {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.pokemon-main-layout {
  display: flex;
  flex-direction: row; /* Ensure items are in a row */
  gap: 16px; /* Space between main columns */
  align-items: flex-start;
  width: 100%; /* Ensure it takes full width */
}

.poke-img-col {
  width: 140px; /* Keep image column fixed or adjust as needed */
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  flex-shrink: 0; /* Prevent shrinking */
}

.poke-info-col {
  flex-grow: 1; /* Allow info column to grow */
  flex-basis: 0; /* Allow shrinking */
  min-width: 180px; /* Set a minimum width to prevent it from becoming too small */
  max-width: 250px; /* Set a maximum width to constrain the input size */
}

.poke-moves-stats-col {
  flex-grow: 3; /* Allow moves/stats column to grow more */
  flex-basis: 0; /* Allow shrinking */
  min-width: 400px; /* Adjusted minimum width for the whole section */
  display: flex; /* Add flex display */
  flex-direction: row; /* Arrange children (moves and stats sections) in a row */
  gap: 16px; /* Space between moves and stats sections */
  align-items: flex-start; /* Align items to the top */
}

.moves-section {
    display: flex;
    flex-direction: column; /* Stack label and inputs vertically */
    margin-left: 15px;
    gap: 6px; /* Space between label and inputs, and between inputs */
    /* Adjust width or flex-basis as needed */
    flex-grow: 1; /* Allow moves section to grow */
    max-width: 150px;
}

.moves-label {
  max-width: 28px;
  font-size: 14px; /* Adjust font size to match label */
  color: #606266; /* Match label color */
  margin-bottom: 6px; /* Space below label */
  margin-left: 0; /* Align left */
  margin-top: 6px; /* No top margin */
}

.poke-moves-inputs {
    display: flex;
    flex-direction: column; /* Stack move inputs vertically */
    gap: 6px; /* Space between move inputs */
    width: 100%; /* Take full width of parent */
    align-items: flex-start; /* Align items to the start (left) */
    margin-top: 0px; /* No top margin */
}

.poke-move-input {
  width: 100%; /* Make input take full width of its container */
  max-width: 200px; /* Set a max-width for individual move inputs */
}

.stats-section-content {
    display: flex;
    margin-left: 15px;
    flex-direction: column; /* Stack label and overview vertically */
    gap: 6px; /* Space between label and overview */
    /* Adjust width or flex-basis as needed */
    flex-shrink: 0; /* Prevent shrinking */
    width: 150px; /* Set a fixed width for the stats section */
}

.stats-label {
    font-size: 14px; /* Match label font size */
    max-width: 45px;
    color: #606266; /* Match label color */
    margin-bottom: 6px; /* Space below label */
    margin-left: 0; /* Align left */
    margin-top: 6px; /* No top margin */
}

.poke-stats-overview {
    cursor: pointer;
    padding: 10px;
    border: 1px solid #dcdfe6;
    border-radius: 4px;
    background-color: #f5f7fa;
    width: 120%;
}

.stat-bar-row {
    display: flex;
    align-items: center;
    margin-bottom: 4px;
    font-size: 0.65em;
    margin-right: 5px;
}

.stat-label {
    width: 40px;
    flex-shrink: 0;
    margin-right: 8px;
    font-weight: bold;
    text-align: right;
}

.stat-bar-bg {
    flex-grow: 1;
    height: 8px;
    max-width: 80px;
    background-color: #ebeef5;
    border-radius: 0; /* Removed border-radius */
    margin-right: 8px;
    overflow: hidden;
}

.stat-bar {
    height: 100%;
    border-radius: 0; /* Removed border-radius */
    transition: width 0.5s ease-in-out;
}

.stat-value {
    width: 22px;
    text-align: right;
    flex-shrink: 0;
    font-weight: bold;
    margin-right: 4px;
}

.stat-ev {
     width: 18px;
     text-align: right;
     flex-shrink: 0;
     font-size: 0.8em;
     color: #606266;
     margin-right: 4px;
}

.stat-nature {
    width: 12px;
    flex-shrink: 0;
    font-weight: bold;
    text-align: center;
}

.nature-plus {
    color: #67C23A; /* Green color for increased stat */
}

.nature-minus {
    color: #F56C6C; /* Red color for decreased stat */
}

.ev-summary-inline {
    font-size: 0.8em;
    color: #606266;
    text-align: right;
    margin-top: 8px;
}

.remove-button-container {
  position: absolute;
  top: 16px;
  right: 16px;
  z-index: 10;
}

.inline-panel-area {
    margin-top: 16px;
}

.inline-panel-card {
    width: 100%;
}

.inline-panel-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.panel-header-title {
  font-weight: bold;
}

.poke-types{
  transform: scale(0.85); 
  transform-origin: center; 
  display: grid;
  margin-bottom: 5px;
}

.disabled-stats-overview {
  cursor: not-allowed;
  background-color: #f0f0f0;
}

/* Add styles to vertically center table headers and content */
:deep(.el-table__header-wrapper th .cell) {
  display: flex;
  align-items: center;
  /* You might also want justify-content: center; if you want horizontal centering */
  justify-content: center; 
}

:deep(.el-table__body-wrapper td .cell) {
  display: flex;
  align-items: flex-start; /* Align cell content to top to prevent misalignment when content wraps */
  /* Note: Horizontal alignment in data cells might be handled by their specific templates (like base stats) */
  /* If you need general horizontal centering for all data cells, add justify-content: center; here */
}

</style>
