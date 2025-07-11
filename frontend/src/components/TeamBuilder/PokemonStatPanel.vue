<template>
  <div class="pokemon-stat-panel">
    <div class="panel-header">
      <h3>能力值分配</h3>
      <el-button type="primary" @click="$emit('close')" size="small" :disabled="totalEv > 508">完成</el-button>
    </div>
    <div v-if="pokemon && pokemon.base_stats">
      <el-form-item label="等级" style="margin-bottom: 12px;">
        <el-input-number v-model="level" :min="1" :max="100" @input="onLevelChange" @change="onLevelChange"  />
      </el-form-item>
      <!-- Header row for stats -->
      <div class="stat-header-row">
          <span class="stat-label-header"></span>
          <span class="base-stat-header">种族值</span>
          <span class="stat-bar-header"></span> <!-- Header for the visualization bar -->
          <span class="ev-input-header">努力值</span>
          <span class="ev-slider-header"></span>
          <span class="iv-input-header">个体值</span>
          <span class="final-stat-header">能力值</span>
          <span class="nature-symbol-header"></span> <!-- Header for nature symbol -->
      </div>
      <div v-for="stat in statKeys" :key="stat" class="stat-row">
        <div class="stat-label">
          <span>{{ statLabelZh[stat] }}</span>
        </div>
        <div class="base-stat-value">
            {{ pokemon.base_stats[stat] ?? 0 }}
        </div>
        <!-- Stat visualization bar -->
        <template v-if="pokemon.base_stats?.[stat]">
            <div class="stat-bar-container">
                <!-- Base Stat Contribution -->
                <div class="stat-bar-segment base" :style="{ width: statSegmentStyle(stat, 'base').width, backgroundColor: statColor(stat) }"></div>
                <!-- IV Contribution -->
                <div class="stat-bar-segment iv" :style="statSegmentStyle(stat, 'iv')"></div>
                <!-- EV Contribution -->
                <div class="stat-bar-segment ev" :style="statSegmentStyle(stat, 'ev')"></div>
            </div>
        </template>
        <template v-else>
            <div class="stat-bar-container" style="visibility: hidden;"></div>
        </template>

        <el-input-number
          v-model="evs[stat]"
          :min="0"
          :max="252"
          :step="4"
          :disabled="evs[stat] + (totalEv - evs[stat]) > 508"
          @change="onEvChange(stat, evs[stat])"
          @input="onEvChange(stat, evs[stat])"
          class="ev-input"
          size="small"
          style="width: 85%; text-align: left;"
        />
        <el-slider
          v-model="evs[stat]"
          :min="0"
          :max="252"
          :step="4"
          :disabled="evs[stat] + (totalEv - evs[stat]) > 508"
          @input="onEvChange(stat, evs[stat])"
          class="ev-slider"
        />

        <div class="iv-input-container">
            <el-input-number
              v-model="ivs[stat]"
              :min="0"
              :max="31"
              @input="onIvChange(stat, ivs[stat])"
              @change="onIvChange(stat, ivs[stat])"
              class="iv-input" size="small" :controls="false"
            />
        </div>
        <!-- Final Stat and Nature Symbol -->
        <span class="final-stat-value">{{ calcStat(stat) }}</span>
        <span class="nature-symbol" :class="natureClass(stat)">{{ natureSymbol(stat) }}</span>
      </div>
      <div class="ev-summary">
        <span>剩余: </span>
        <span :class="remainingEvClass">{{ remainingEv }}</span>
      </div>
    </div>
    <div v-else>请选择宝可梦以分配能力值</div>
  </div>
</template>

<script setup lang="ts">
import { computed, reactive, ref, watch } from 'vue';
const props = defineProps<{ pokemon: any }>();
const emit = defineEmits(['update', 'close']);

const statKeys = ['hp', 'atk', 'def', 'spa', 'spd', 'spe'];
const statLabelZh: Record<string, string> = {
  hp: 'HP', atk: '攻击', def: '防御', spa: '特攻', spd: '特防', spe: '速度'
};

const NATURE_EFFECTS: Record<string, { increased: string | null, decreased: string | null }> = {
  // Format: NatureName: { increased: 'stat_key', decreased: 'stat_key' }
  // HP is never affected by nature
  '固执': { increased: 'atk', decreased: 'spa' }, '怕寂寞': { increased: 'atk', decreased: 'def' },
  '顽皮': { increased: 'atk', decreased: 'spd' }, '勇敢': { increased: 'atk', decreased: 'spe' },
  '大胆': { increased: 'def', decreased: 'atk' }, '悠闲': { increased: 'def', decreased: 'spe' },
  '淘气': { increased: 'def', decreased: 'spa' }, '乐天': { increased: 'def', decreased: 'spd' },
  '内敛': { increased: 'spa', decreased: 'atk' }, '慢吞吞': { increased: 'spa', decreased: 'spe' },
  '马虎': { increased: 'spa', decreased: 'spd' }, '冷静': { increased: 'spa', decreased: 'def' },
  '温和': { increased: 'spd', decreased: 'atk' }, '温顺': { increased: 'spd', decreased: 'def' },
  '慎重': { increased: 'spd', decreased: 'spa' }, '自大': { increased: 'spd', decreased: 'spe' },
  '胆小': { increased: 'spe', decreased: 'atk' }, '急躁': { increased: 'spe', decreased: 'def' },
  '爽朗': { increased: 'spe', decreased: 'spa' }, '天真': { increased: 'spe', decreased: 'spd' },
  // Neutral Natures
  '勤奋': { increased: null, decreased: null }, '坦率': { increased: null, decreased: null },
  '害羞': { increased: null, decreased: null }, '浮躁': { increased: null, decreased: null },
  '认真': { increased: null, decreased: null },
};

// 初始化EV/IV
const evs = reactive<Record<string, number>>({ hp: 0, atk: 0, def: 0, spa: 0, spd: 0, spe: 0 });
const ivs = reactive<Record<string, number>>({ hp: 31, atk: 31, def: 31, spa: 31, spd: 31, spe: 31 });
const level = ref(props.pokemon.level ?? 50);

watch(() => props.pokemon, (val) => {
  if (val) {
    // Reset evs and ivs to default or from new pokemon data
    statKeys.forEach(k => {
        evs[k] = val.evs?.[k] ?? 0;
        ivs[k] = val.ivs?.[k] ?? 31;
    });
    level.value = val.level ?? 50;
  }
}, { immediate: true, deep: true }); // Use deep watch for nested properties

function onLevelChange() {
  emit('update', { level: level.value });
}

const totalEv = computed(() => statKeys.reduce((sum, k) => sum + (evs[k] || 0), 0));

// Computed property for remaining EVs
const remainingEv = computed(() => 508 - totalEv.value);

// Computed property for remaining EV text color class
const remainingEvClass = computed(() => {
  if (remainingEv.value < 0) return 'ev-over';
  if (remainingEv.value >= 0) return 'ev-valid';
  return ''; // Default
});

function onEvChange(stat: string, value: number) {
  // 限制总和≤508
  const currentStatEv = evs[stat] || 0;
  const otherStatsEv = totalEv.value - currentStatEv;

  if (otherStatsEv + value > 508) {
    // Calculate the maximum allowed value for this stat
    const maxAllowed = 508 - otherStatsEv;
    // Round down to the nearest multiple of 4
    evs[stat] = Math.floor(maxAllowed / 4) * 4;
  } else {
    evs[stat] = value;
  }

  emit('update', { evs: { ...evs } });
}

function onIvChange(stat: string, value: number) {
   // Ensure value is within min/max bounds
   ivs[stat] = Math.max(0, Math.min(31, value));
   emit('update', { ivs: { ...ivs } });
}

function getNatureEffect(stat: string) {
  const nature = props.pokemon.nature || '';
  const effect = NATURE_EFFECTS[nature];
  if (effect) {
    if (effect.increased === stat) return 1.1;
    if (effect.decreased === stat) return 0.9;
  }
  return 1.0;
}

function calcStat(stat: string) {
  const base = props.pokemon.base_stats?.[stat] ?? 0;
  const lv = level.value;
  const ev = evs[stat] ?? 0;
  const iv = ivs[stat] ?? 31;
  
  if (base === 0) return 0; // Stat is not present for this Pokemon

  if (stat === 'hp') {
    if (base === 1) return 1;
    return Math.floor(((base * 2 + iv + Math.floor(ev / 4)) * lv) / 100) + 10 + lv;
  } else {
    const nature = getNatureEffect(stat);
    return Math.floor((Math.floor(((base * 2 + iv + Math.floor(ev / 4)) * lv) / 100) + 5) * nature);
  }
}

// --- Stat Bar Visualization Logic ---
// Function to calculate segment widths based on rough proportion of components
function statSegmentStyle(stat: string, segmentType: 'base' | 'iv' | 'ev') {
  const base = props.pokemon.base_stats?.[stat] ?? 0;
  const iv = ivs[stat] ?? 31;
  const ev = evs[stat] ?? 0;
  const lv = level.value;

   if (base === 0) return { width: '0%' };

   // Calculate rough contribution components (simplified)
   // For HP, the formula structure is different, so simplify contribution logic
   let baseContribution = 0;
   let ivContribution = 0;
   let evContribution = 0;

   if (stat === 'hp') {
       // HP formula: ((base * 2 + iv + floor(ev / 4)) * lv / 100) + 10 + lv
       // Rough components proportional to base * 2, iv, floor(ev/4)
       baseContribution = base * 2;
       ivContribution = iv;
       evContribution = Math.floor(ev / 4);
   } else {
       // Non-HP formula: floor((floor((base * 2 + iv + floor(ev / 4)) * lv / 100) + 5) * nature)
       // Rough components proportional to base * 2, iv, floor(ev/4) before level/nature
       baseContribution = base * 2;
       ivContribution = iv;
       evContribution = Math.floor(ev / 4);
   }

   const totalComponents = baseContribution + ivContribution + evContribution;
   let percentage = 0;

   if (totalComponents > 0) {
       if (segmentType === 'base') {
           percentage = (baseContribution / totalComponents) * 100;
       } else if (segmentType === 'iv') {
           percentage = (ivContribution / totalComponents) * 100;
       } else if (segmentType === 'ev') {
           percentage = (evContribution / totalComponents) * 100;
       }
   }

   // Ensure percentage doesn't exceed 100% (shouldn't happen with correct calculation)
   percentage = Math.min(100, percentage);

   // The total width of all segments should scale with the calculated stat
   // relative to the max possible stat value at the current level.
   const totalCalculatedStat = calcStat(stat);
   let maxStatValue: number;
    if (lv <= 50) {
        maxStatValue = 200;
    } else if (lv <= 80) {
        maxStatValue = 325;
    } else {
        maxStatValue = 450;
    }
    const totalBarPercentage = Math.min(100, (totalCalculatedStat / maxStatValue) * 100);

    // Scale the segment percentage by the total bar percentage
    const scaledPercentage = (percentage / 100) * totalBarPercentage;

   return { width: scaledPercentage + '%' };
}

// Keep statColor function for segment colors
function statColor(stat: string) {
  const colors: Record<string, string> = { hp: '#78C850', atk: '#C03028', def: '#6890F0', spa: '#A040A0', spd: '#edbf08', spe: '#F85888' };
  return colors[stat] || '#ccc';
}

function natureClass(statKey: string): string {
  if (!props.pokemon.nature) return '';
  const effect = NATURE_EFFECTS[props.pokemon.nature];
  if (effect) {
    if (effect.increased === statKey) return 'nature-plus';
    if (effect.decreased === statKey) return 'nature-minus';
  }
  return '';
}
function natureSymbol(statKey: string): string {
  if (!props.pokemon.nature) return '';
  const effect = NATURE_EFFECTS[props.pokemon.nature];
  if (effect) {
    if (effect.increased === statKey) return '▲';
    if (effect.decreased === statKey) return '▼';
  }
  return '';
}

</script>

<style scoped>
.pokemon-stat-panel {
  width: 100%;
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.panel-header h3 {
  margin: 0;
  font-size: 1.1em;
}

.stat-header-row,
.stat-row {
  display: grid; /* Use grid layout */
  /* Define columns: Ability Name | Base Stat | Bar | EV Input | Slider | IV Input | Final Stat Value | Nature Symbol */
  grid-template-columns: 30px 45px 150px 120px 220px 45px 45px 10px; /* Explicit widths */
  gap: 12px; /* Space between columns */
  align-items: center; /* Vertically align items in the grid row */
  margin-bottom: 8px;
  font-size: 0.9em;
  width: 100%;
}

.stat-header-row {
    font-weight: bold;
    border-bottom: 1px solid #ebeef5;
    padding-bottom: 4px;
    margin-bottom: 10px;
    color: #606266;
}

/* Ensure headers and values span correctly in the grid */
.stat-label-header, .stat-label {
  grid-column: 1;
  text-align: right;
}

.base-stat-header, .base-stat-value {
    grid-column: 2;
    text-align: right;
}

.stat-bar-header {
    grid-column: 3;
    text-align: left;
    font-weight: bold;
}

.stat-bar-container {
    grid-column: 3; /* Both header and container in the same column */
    display: flex; /* Use flexbox for segments */
    height: 12px; /* Adjusted height */
    border-radius: 0; /* Removed border-radius */
    overflow: hidden;
    background-color: #ebeef5; /* Default background if no segments */
    width: 90%; /* Adjusted width */
    border: 1px solid #ebeef5; /* Added border */
    box-sizing: border-box; /* Include border in element's total width and height */
}

.stat-bar-segment {
    height: 100%;
    /* Width set by inline style */
    /* Background color set by dedicated classes or inline style */
}

/* Removed .stat-bar-segment.base background-color rule */

.stat-bar-segment.iv {
    background-color: #01d6d6; /* Color for IVs */
}

.stat-bar-segment.ev {
    background-color: #fdae25; /* Color for EVs */
}

.ev-input-header, .ev-input {
    grid-column: 4;
    text-align: left; /* Header left align */
}

.ev-slider-header, .ev-slider {
    grid-column: 5;
    text-align: left; /* Header left align */
    width: 95%; /* Adjusted width */
    margin-right: 10px; /* Adjusted margin */
}

.iv-input-header, .iv-input-container {
    grid-column: 6;
    display: flex;
    align-items: center;
}
.iv-input-header {
    justify-content: center; /* Center text */
}

.iv-input {
    width: 48px; /* Width for IV input number */
}

.final-stat-header {
  grid-column: 7; /* Header for the final stat value column */
  text-align: right;
}

.nature-symbol-header {
    grid-column: 8; /* Header for the nature symbol column */
    text-align: center; /* Center symbol header */
}

/* Updated styles for individual elements within the grid */
.stat-label {
    font-weight: bold;
}

.final-stat-value {
    grid-column: 7; /* Assign to the 7th column */
    font-weight: bold;
    text-align: right; /* Align value to the right */
}

.nature-symbol {
    grid-column: 8; /* Assign to the 8th column */
    font-weight: bold;
    text-align: center; /* Center the symbol */
}

.ev-summary {
  display: grid; /* Use grid to align with stat rows */
  grid-template-columns: 30px 45px 150px auto auto; /* Align with stat columns (label | base | bar | remaining text | remaining number) */
  gap: 12px; /* Match gap in stat rows */
  align-items: center; /* Vertically align items */
  margin-top: 12px;
  font-size: 0.9em;
}
.ev-summary span:first-child { /* "剩余:" text */
    grid-column: 3; /* Place the "剩余:" text in column 4 */
    text-align: right;
  font-weight: bold;
}
.warning {
  margin-left: 8px;
}

.nature-plus {
    color: #67C23A; /* Green color for increased stat */
}

.nature-minus {
    color: #F56C6C; /* Red color for decreased stat */
}

.ev-summary .ev-valid {
  color: #67C23A; /* Green color for valid remaining EVs */
  font-weight: bold;
  text-align: left;
  margin-left: 39px;
}
.ev-summary .ev-over {
  color: #F56C6C; /* Red color for negative remaining EVs */
  font-weight: bold;
  text-align: left;
  margin-left: 39px;
}
</style>
