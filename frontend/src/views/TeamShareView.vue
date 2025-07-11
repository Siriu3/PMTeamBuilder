<template>
  <div class="team-share-view">
    <el-card class="box-card" v-loading="loading" v-if="loading || teamData || error">
      <template #header v-if="teamData">
        <div class="card-header">
          <div class="team-name-creator">
            <span>{{ teamData.name }}</span>
            <span class="creator-info"> by {{ teamData.creator_username || '未知' }}</span>
          </div>
          <div class="gen-format-info">
            | {{ teamData.generation }} - {{ formatZhMap[teamData.format] || teamData.format }}
          </div>
        </div>
      </template>

      <div v-if="loading" class="loading-container">
        <el-empty description="加载中..."></el-empty>
      </div>

      <div v-else-if="error" class="error-container">
        <el-empty description="团队未找到或无法访问。"></el-empty>
      </div>

      <div v-else-if="teamData">
        <div class="share-layout-container">

          <!-- Pokemon List (Left Side) -->
          <div class="pokemon-list-container">
            <div class="pokemon-list">
              <el-card class="pokemon-card" v-for="(poke, index) in teamData.pokemons" :key="index">
                 <template #header>
                   <div class="pokemon-card-header">
                      <img :src="poke.sprite || '/ball_default.png'" :alt="poke.species_name_zh" class="pokemon-sprite" />
                      <div class="name-item-stack">
                        <span style="font-size: 1.15em; font-weight: 700;">{{ poke.species_name_zh || poke.species_name || '未知宝可梦' }}</span>
                        <div class="item-display">
                            <span v-if="poke.item" class="item-at">@ </span>
                            <img v-if="poke.item_sprite" :src="poke.item_sprite" :alt="poke.item" class="item-sprite" />
                            <span style="font-weight: 700;">{{ poke.item || '无' }}</span>
                        </div>
                      </div>
                      <div class="pokemon-types-tera" v-if="poke.types.filter(t => t).length > 0 || teamData.generation === 'Gen 9'">
                        <div class="pokemon-types">
                          <AttributeIcon
                            v-for="(type, typeIndex) in poke.types.filter(t => t)"
                            :key="typeIndex"
                            :type="typeZhMap[type?.toLowerCase()] || type"
                            class="scaled-attribute-icon"
                            :style="{ margin: poke.types.filter(t => t).length === 1 ? 'auto' : '0' }"
                          />
                        </div>
                        <div class="pokemon-tera" v-if="teamData.generation === 'Gen 9'">
                          <div class="tera-label">太晶属性</div>
                          <AttributeIcon
                            v-if="poke.tera_type"
                            :type="typeZhMap[poke.tera_type?.toLowerCase()] || poke.tera_type"
                            class="scaled-attribute-icon"
                          />
                        </div>
                      </div>
                      <div class="pokemon-types-tera" v-else>
                        <div class="pokemon-types">
                          
                        </div>
                         <div class="pokemon-tera" v-if="teamData.generation === 'Gen 9'">
                           <div class="tera-label">太晶属性</div>
                           <AttributeIcon v-if="poke.tera_type" :type="typeZhMap[poke.tera_type?.toLowerCase()] || poke.tera_type" class="scaled-attribute-icon" />
                           <span v-else>-</span>
                         </div>
                         <div class="pokemon-tera" v-else>
                           <span>-</span>
                         </div>
                      </div>
                   </div>
                 </template>
                <el-descriptions class="pokemon-card-descriptions" :column="1" border size="small">
                  <el-descriptions-item class="pokemon-card-descriptions-item" label="特性"><span style="font-size: 1.1em;">{{ poke.ability || '未知' }}</span></el-descriptions-item>
                  <el-descriptions-item class="pokemon-card-descriptions-item" label="性格"><span style="font-size: 1.1em;">{{ poke.nature || '未知' }}</span></el-descriptions-item>
                  <el-descriptions-item class="pokemon-card-descriptions-item" label="招式">
                    <div class="moves-grid">
                      <div v-for="(move, moveIndex) in poke.moves" :key="moveIndex" class="move-item">
                        {{ move || '-' }}
                      </div>
                    </div>
                  </el-descriptions-item>
                  <el-descriptions-item class="pokemon-card-descriptions-item" label="努力值">
                    <div class="stats-grid">
                      <el-tag
                        v-for="stat in getDisplayedEvs(poke.evs)"
                        :key="stat.label"
                        size="small"
                        :style="{ 'background-color': stat.color, color: 'white', marginRight: '5px' }"
                        class="stat-tag"
                      >
                        <div class="stat-tag-content">
                          <span class="stat-tag-label">{{ stat.label }}</span>
                          <span class="stat-tag-value">{{ stat.value }}</span>
                        </div>
                      </el-tag>
                      <span v-if="getDisplayedEvs(poke.evs).length === 0">无</span>
                    </div>
                  </el-descriptions-item>
                  <el-descriptions-item class="pokemon-card-descriptions-item" label="个体值">
                    <div class="stats-grid">
                      <el-tag
                        v-for="stat in getDisplayedIvs(poke.ivs)"
                        :key="stat.label"
                        size="small"
                        :style="{ 'background-color': stat.color, color: 'white', marginRight: '5px' }"
                        class="stat-tag"
                      >
                        <div class="stat-tag-content">
                          <span class="stat-tag-label">{{ stat.label }}</span>
                          <span class="stat-tag-value">{{ stat.value }}</span>
                        </div>
                      </el-tag>
                      <span v-if="getDisplayedIvs(poke.ivs).length === 0">全31</span>
                    </div>
                  </el-descriptions-item>
                </el-descriptions>
              </el-card>
            </div>
          </div>

          <!-- Basic Info (Right Side) -->
          <div class="basic-info-container">
            <!-- Wrapper for descriptions and custom tags -->
            <div class="basic-info-content">
               <el-descriptions :column="1" border size="small">
                <el-descriptions-item label="收藏数">{{ teamData.favorites_count || 0 }}</el-descriptions-item>
                <el-descriptions-item label="点赞数">{{ teamData.likes_count || 0 }}</el-descriptions-item>
                <el-descriptions-item label="创建时间">{{ new Date(teamData.created_at).toLocaleString() }}</el-descriptions-item>
              </el-descriptions>

              <!-- Custom Tags section remains here -->
              <div class="custom-tags-section">
                 <div class="custom-tags-content">
                   <div v-if="teamData.custom_tags && teamData.custom_tags.length > 0" style="display: flex; flex-wrap: wrap; gap: 5px;">
                     <el-tag v-for="(tag, index) in teamData.custom_tags" :key="index" size="small">
                       {{ tag }}
                     </el-tag>
                   </div>
                   <span v-else>无</span>
                 </div>
              </div>
            </div>

            <!-- New section for Copyright at the bottom -->
            <div class="copyright-section">
                <div class="about">© 2025 <a :href="mainUrl">宝可梦队伍构建系统</a> by 3irius</div>
                <div class="about">Pokémon © 2002-2025 Pokémon.</div>
                <div class="about">© 1995-2025 Nintendo/Creatures Inc./GAME FREAK inc.</div>
                <div class="about">"精灵宝可梦"、"宝可梦"、"Pokémon"是任天堂的商标</div>
            </div>

          </div>

        </div>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue';
import { useRoute } from 'vue-router';
import UserService from '@/services/UserService';
import { ElCard, ElDescriptions, ElDescriptionsItem, ElTag, ElDivider, ElEmpty, ElMessage, ElLoading } from 'element-plus';
import { typeZhMap, formatZhMap } from '@/utils/constants';
import AttributeIcon from '@/components/TeamBuilder/AttributeIcon.vue';

const route = useRoute();
const teamData = ref(null);
const loading = ref(true);
const error = ref(false);
// 主站链接
const mainUrl = computed(() => {
  return `${window.location.origin}`;
});

// Stat display data (labels and colors)
const statKeys = ['hp', 'atk', 'def', 'spa', 'spd', 'spe'];
const statLabelZh = { hp: 'HP', atk: '攻击', def: '防御', spa: '特攻', spd: '特防', spe: '速度' };
const statColor = { hp: '#78C850', atk: '#C03028', def: '#6890F0', spa: '#A040A0', spd: '#edbf08', spe: '#F85888' };

// Helper function to get displayed EVs
const getDisplayedEvs = (evs) => {
  if (!evs) return [];
  const displayed = [];
  statKeys.forEach(key => {
    if (evs[key] && evs[key] > 0) {
      displayed.push({
        label: statLabelZh[key],
        value: evs[key],
        color: statColor[key]
      });
    }
  });
  return displayed;
};

// Helper function to get displayed IVs
const getDisplayedIvs = (ivs) => {
  // Default IVs are 31 if not specified by backend
  const defaultIVs = { hp: 31, atk: 31, def: 31, spa: 31, spd: 31, spe: 31 };
  const currentIvs = ivs || {};

  const displayed = [];
  statKeys.forEach(key => {
    const ivValue = currentIvs[key] ?? defaultIVs[key]; // Use ?? to handle null/undefined from backend
    if (ivValue !== 31) {
      displayed.push({
        label: statLabelZh[key],
        value: ivValue,
        color: statColor[key]
      });
    }
  });
  return displayed;
};

// Helper function to get tag type based on Pokemon type
const getTypeTagType = (type) => {
  switch (type?.toLowerCase()) {
    case 'normal': return 'info';
    case 'fighting': return '';
    case 'flying': return ''; // You might need specific colors for each type
    case 'poison': return 'success';
    case 'ground': return '';
    case 'rock': return '';
    case 'bug': return 'success';
    case 'ghost': return 'info';
    case 'steel': return '';
    case 'fire': return 'danger';
    case 'water': return '';
    case 'grass': return 'success';
    case 'electric': return 'warning';
    case 'psychic': return '';
    case 'ice': return '';
    case 'dragon': return '';
    case 'dark': return '';
    case 'fairy': return 'danger';
    default: return '';
  }
};

onMounted(async () => {
  const token = route.params.token;
  if (!token) {
    error.value = true;
    loading.value = false;
    ElMessage.error('分享链接无效。');
    return;
  }

  try {
    // Use the getTeamByToken service method
    const data = await UserService.getTeamByToken(token);
    teamData.value = data;
    loading.value = false;
  } catch (err) {
    console.error('Failed to fetch team data by token:', err);
    error.value = true;
    loading.value = false;
    // Display a user-friendly error message
    const errorMessage = err.response?.data?.message || '加载团队数据失败。';
    ElMessage.error(errorMessage);
  }
});
</script>

<style scoped>
.team-share-view {
  overflow-y: hidden; /* Disable vertical scrolling */
}

.card-header {
  font-size: 1.2em;
  font-weight: bold;
  display: flex;
  align-items: center;
  gap: 15px;
  flex-wrap: wrap;
}

.team-name-creator {
  display: flex;
  align-items: baseline;
  gap: 5px;
}

.creator-info {
  font-size: 0.7em;
  font-weight: normal;
  color: #606266;
}

.gen-format-info {
  font-size: 0.75em;
  font-weight: normal;
  color: #606266;
  margin-left: 20px;
}

.loading-container,
.error-container {
  min-height: 300px;
  display: flex;
  justify-content: center;
  align-items: center;
}

.share-layout-container {
  display: flex;
  gap: 20px;
  flex-wrap: wrap;
  align-items: stretch; /* Allow children to stretch to equal height */
}

.pokemon-list-container {
    flex: 3.9;
    min-width: 580px;
}

.basic-info-container {
    flex: 1.1;
    display: flex;
    flex-direction: column;
    justify-content: space-between; /* Push content and copyright apart */
}

.basic-info-content {
    flex-grow: 1; /* Allow content to take up available space */
     margin-bottom: 10px;
}

.basic-info-container .el-descriptions {
    width: 100%;
    margin-bottom: 10px; /* Add space between descriptions and custom tags */
}

.pokemon-list {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(350px, 0.33fr)); /* Adjust to auto-fit columns */
  gap: 10px;
  /* Remove max-width and margin: auto */
}

.pokemon-card-header {
   display: flex;
   align-items: center;
   width: 100%;
}

.pokemon-sprite {
  width: 65px;
  height: 65px;
  object-fit: contain;
}

.name-item-stack {
  display: flex;
  flex-direction: column; /* Stack name and item vertically */
  align-items: flex-start; /* Align items to the start (left) */
  margin-right: auto; /* Push this block to the right of the sprite, and push types/tera to the far right */
  margin-left: 10px; /* Add some space between sprite and name/item stack */
}

.item-display {
   display: flex;
   align-items: center;
   font-size: 0.8em;
   margin-right: 1px;
}

.item-sprite {
   width: 30px;
   height: 30px;
   object-fit: contain;
   margin-right: 1px;
}

.moves-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr); /* 2 columns */
  grid-template-rows: repeat(2, auto); /* 2 rows, height auto */
  gap: 5px; /* Gap between moves */
}

.move-item {
   /* Optional: add padding or other styles to individual move items */
   background-color: #f9f9f9; /* Add light grey background */
   /* border: 1px solid #ccc; */
   padding: 5px; /* Add some padding */
   text-align: center; /* Center the move text */
   white-space: nowrap; /* Prevent text wrapping */
   overflow: hidden; /* Hide overflowing text */
   text-overflow: ellipsis; /* Add ellipsis */
   border: 1px solid #eee; /* Add border on all sides */
   font-size: 1.15em;
}

.item-at {
  margin-right: 1px; /* Add space after @ */
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(50px, 68px)); /* Two columns, adjust minmax as needed */
  gap: 3px;
}

.stat-tag {
  /* Optional: adjust padding/height if needed */
}

.stat-tag .el-tag__content {
   width: 100%; /* Ensure content takes full width of tag */
}

.stat-tag-content {
   display: flex;
   justify-content: center; /* Center content within the flex container */
   align-items: center; /* Vertically center items */
   gap: 5px; /* Add gap between label and value */
   width: 100%;
}

.stat-tag-label {
   /* flex-basis: auto; Let content dictate size */
   text-align: center; /* Center label */
}

.stat-tag-value {
   /* flex-basis: auto; Let content dictate size */
   text-align: center; /* Center value */
}

.pokemon-types-tera {
  display: grid;
  grid-template-columns: repeat(2, 1fr); /* Two columns */
  gap: 10px; /* Gap between columns */
  align-items: center; /* Vertically center items in grid cells */
  margin-left: auto; /* Push this element to the far right */
}

.pokemon-types {
  display: flex;
  flex-direction: column; /* Stack types vertically */
  align-items: center; /* Center types horizontally in their column */
  gap: 5px; /* Gap between type icons */
}

.pokemon-tera {
  display: flex;
  flex-direction: column; /* Stack tera label and icon vertically */
  align-items: center; /* Center tera elements horizontally in their column */
  gap: 3px; /* Gap between label and icon */
}

.tera-label {
  font-size: 0.85em;
  color: #606266; /* Match el-descriptions label color */
  margin-bottom: 8px;
}

.scaled-attribute-icon {
  transform: scale(0.9); /* Apply 0.9 scaling */
  transform-origin: center; /* Scale from the center */
}

.pokemon-card-descriptions {
  width: 87%;
  margin: 0 auto;
}

/* Style for the label (header) within descriptions item */
.pokemon-card-descriptions-item :deep(.el-descriptions-item__label) {
  font-size: 1.2em; /* Adjust font size as needed */
  font-weight: bold; /* Example: make label bold */
  margin-left: 5px;
}

/* New styles for custom tags section */
.custom-tags-section {
  display: flex; /* Use flexbox to lay out label and content */
  border: 1px solid #ebeef5; /* Add border similar to el-descriptions */
  border-top: none; /* Remove top border to connect visually below descriptions */
  font-size: 0.875em; /* Match el-descriptions default font size */
}

.custom-tags-label {
  background-color: #f2f6fc;
  padding: 10px 12px;
  font-weight: bold;
  color: #606266;
  flex: 0 0 120px;
  text-align: center;
  border-right: 1px solid #ebeef5;
}

.custom-tags-content {
  padding: 10px 12px;
  flex: 1;
  text-align: left;
}

/* Ensure the tags within the content don't overflow */
.custom-tags-content > div {
    display: flex;
    flex-wrap: wrap;
    gap: 5px;
}

/* New styles for copyright section */
.copyright-section {
    text-align: center;
    padding-top: 10px;
}

.about {
  font-size: 0.7em;
  color: #5f6163;
  width: 100%;
  margin-top: 3px;
}

</style> 