<template>
  <div class="selection-panel">
    <div class="panel-controls">
      <el-input 
        v-if="type==='pokemon'" 
        v-model="searchQueryPokemonDebounced" 
        placeholder="搜索宝可梦 (中英名称)" 
        clearable 
        class="search-input"
      />
      <el-input 
        v-if="type==='item'" 
        v-model="searchQueryItemDebounced" 
        placeholder="搜索道具 (中英名称)"
        clearable
        class="search-input"
      />
      <el-input 
        v-if="type==='move'" 
        v-model="searchQueryMoveDebounced" 
        placeholder="搜索招式 (中英名称)"
        clearable
        class="search-input"
      />
      <!-- Tera types usually don't need search, shown as a grid -->
      <template v-if="type==='pokemon'">
        <el-button @click="showPokemonTypeFilterDialog = true" size="small" style="margin-left: 12px;">
          属性筛选 <span v-if="selectedPokemonFilterTypes.length > 0">({{ selectedPokemonFilterTypes.map(t => typeZhMap[t] || t).join(' / ') }})</span>
        </el-button>
        <el-button @click="clearPokemonTypeFilter" size="small" :disabled="selectedPokemonFilterTypes.length === 0">
          <div> <el-icon><Refresh /></el-icon> 清除筛选</div>
        </el-button>
      </template>
    </div>

    <el-scrollbar 
      v-if="type==='pokemon'" 
      height="400px" 
      @scroll="handlePokemonScroll" 
      ref="pokemonScrollbarRef"
      class="pokemon-list-scrollbar"
    >
      <el-table 
        :data="filteredPokemonList" 
        @row-click="onSelectPokemon" 
        :empty-text="getEmptyText('pokemon')"
        style="width: 100%"
        :row-key="(row: any) => row.id"
        sticky-header
      >
        <el-table-column prop="sprite" label="" width="100">
          <template #default="scope">
            <img 
                :src="scope.row.sprite || '/ball_default.png'"
                :alt="scope.row.name_zh || scope.row.name"
                style="width:60px;height:60px; object-fit: contain;"
                :style="!scope.row.sprite ? { backgroundColor: '#eee', borderRadius: '4px' } : {}"
            />
          </template>
        </el-table-column>
        <el-table-column prop="name_zh" label="名称" width="120" sortable />
        <el-table-column prop="types" label="属性" width="100">
          <template #default="scope">
            <div style="display:flex; flex-wrap: wrap; gap: 4px; justify-content: center;">
              <AttributeIcon v-for="t in scope.row.types" :key="t" :type="t" class="scaled-attribute-icon" />
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="abilities" label="特性" width="150">
          <template #default="scope">
            <div style="display:flex; flex-wrap: wrap; gap: 4px;">
              <el-tag v-for="ability_obj in scope.row.abilities" :key="ability_obj.id || ability_obj.name_en || ability_obj.name_zh" size="small"
                :type="ability_obj.is_hidden ? 'warning' : 'info'"
                style="margin:2px;"
              >
                {{ ability_obj.name_zh || ability_obj.name_en }}
              </el-tag>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="base_stats" label="种族值">
          <template #default="scope">
            <div style="display:flex;gap:8px; justify-content: center;">
               <div style="display:flex;flex-direction:column;align-items:center;">
                 <span style="font-size:12px;color:#888;">HP</span>
                 <span style="font-weight:bold;">{{ scope.row.base_stats.hp }}</span>
               </div>
               <div style="display:flex;flex-direction:column;align-items:center;">
                 <span style="font-size:12px;color:#888;">攻击</span>
                 <span style="font-weight:bold;">{{ scope.row.base_stats.attack }}</span>
               </div>
               <div style="display:flex;flex-direction:column;align-items:center;">
                 <span style="font-size:12px;color:#888;">防御</span>
                 <span style="font-weight:bold;">{{ scope.row.base_stats.defense }}</span>
               </div>
               <div style="display:flex;flex-direction:column;align-items:center;">
                 <span style="font-size:12px;color:#888;">特攻</span>
                 <span style="font-weight:bold;">{{ scope.row.base_stats['special-attack'] }}</span>
               </div>
               <div style="display:flex;flex-direction:column;align-items:center;">
                 <span style="font-size:12px;color:#888;">特防</span>
                 <span style="font-weight:bold;">{{ scope.row.base_stats['special-defense'] }}</span>
               </div>
               <div style="display:flex;flex-direction:column;align-items:center;">
                 <span style="font-size:12px;color:#888;">速度</span>
                 <span style="font-weight:bold;">{{ scope.row.base_stats.speed }}</span>
               </div>
               <div style="display:flex;flex-direction:column;align-items:center;">
                 <span style="font-size:12px;color:#888;">总计</span>
                 <span style="font-weight:bold;">{{ scope.row.base_stats.hp + scope.row.base_stats.attack + scope.row.base_stats.defense + scope.row.base_stats['special-attack'] + scope.row.base_stats['special-defense'] + scope.row.base_stats.speed }}</span>
               </div>
             </div>
          </template>
        </el-table-column>
      </el-table>
      <p v-if="type==='pokemon' && loadingPokemon && pokemonList.length > 0" class="loading-more-text">加载中...</p>
      <p v-if="type==='pokemon' && !canLoadMorePokemon && pokemonList.length > 0" class="loading-more-text">没有更多了</p>
    </el-scrollbar>
    
    <div v-else-if="type==='item'">
      <div class="panel-controls">
        <!-- 搜索框已经添加在顶部 -->
      </div>
      <el-collapse v-model="activeCategories" class="item-category-collapse">
        <el-collapse-item 
          v-for="group in groupedItems"
          :key="group.category"
          :title="`${itemCategoryZh[group.category] || group.category} (${group.items.length})`"
          :name="group.category"
        >
          <div class="item-list-in-group">
            <div v-for="item in group.items" :key="item.id" class="item-row" @click="onSelectItem(item)">
              <img 
                :src="item.sprite || '/ball_default.png'"
                :alt="item.name_zh || item.name"
                class="item-sprite"
                :style="!item.sprite ? { backgroundColor: '#eee', borderRadius: '4px' } : {}"
              />
              <span class="item-name">{{ item.name_zh || item.name }}</span>
              <span class="item-effect">{{ (item.effect || item.effect_en || '无描述').replace(/[\s\n]/g, '') }}</span>
            </div>
            <el-empty v-if="group.items.length === 0" description="无道具"></el-empty>
          </div>
        </el-collapse-item>
        <el-empty v-if="groupedItems.length === 0 && !loadingItems" description="无匹配道具"></el-empty>
      </el-collapse>
      <p v-if="loadingItems" class="loading-text">加载中...</p>
      <!-- Corrected item sprite fallback path -->
      <div style="display: none;"><img src="/ball_default.png" alt="精灵球"></div>
      <!-- Note: Pagination/Load more not implemented for grouped view -->
      <!-- Note: Empty text for initial load is handled by the last el-empty -->
    </div>
    <el-table 
      v-else-if="type==='move'"
      :data="filteredMoveList"
      height="400"
      @row-click="onSelectMove"
      :empty-text="getEmptyText('move')"
      style="width: 100%"
      row-key="id"
      sticky-header
      :row-class-name="getRowClassName"
    >
      <el-table-column prop="name_zh" label="名称" width="80" sortable/>
      <el-table-column prop="type" label="属性" width="95">
          <template #header>
              <el-select v-model="selectedMoveType" placeholder="属性" size="small" clearable>
                  <el-option
                      v-for="typeOption in uniqueMoveTypes"
                      :key="typeOption"
                      :label="typeZhMap[typeOption] || typeOption"
                      :value="typeOption"
                  />
              </el-select>
          </template>
          <template #default="scope">
              <AttributeIcon :type="typeZhMap[scope.row.type] || scope.row.type" class="scaled-attribute-icon" />
          </template>
      </el-table-column>
      <el-table-column prop="category" label="分类" width="90">
           <template #header>
              <el-select v-model="selectedMoveCategory" placeholder="分类" size="small" clearable>
                  <el-option
                      v-for="categoryOption in uniqueMoveCategories"
                      :key="categoryOption"
                      :label="moveCategoryZh[categoryOption] || categoryOption"
                      :value="categoryOption"
                  />
              </el-select>
          </template>
          <template #default="scope">
              {{ moveCategoryZh[scope.row.category] || scope.row.category }}
          </template>
      </el-table-column>
      <el-table-column prop="power" label="威力" width="80" sortable>
          <template #default="scope">
              {{ scope.row.power == null ? '—' : scope.row.power }}
          </template>
      </el-table-column>
      <el-table-column prop="accuracy" label="命中" width="80" sortable>
          <template #default="scope">
              {{ scope.row.accuracy == null ? '—' : scope.row.accuracy }}
          </template>
      </el-table-column>
      <el-table-column prop="pp" label="PP" width="60" sortable>
          <template #default="scope">
            {{ calculateMaxPP(scope.row.pp) }}
          </template>
      </el-table-column>
      <el-table-column prop="desc" label="描述" />
    </el-table>
    <div v-else-if="type==='nature'" class="nature-selection-container">
      <el-collapse v-model="activeNatureGroups" class="nature-collapse">
          <el-collapse-item 
              v-for="group in groupedNatures"
              :key="group.increased || 'neutral'"
              :title="`${group.increased ? '+ ' + statLabelZh[group.increased] : '无增减'} (${group.natures.length})`"
              :name="group.increased || 'neutral'"
          >
              <div class="nature-list-in-group">
                  <el-button 
                      v-for="nature in group.natures" 
                      :key="nature.name" 
                      @click="$emit('select', nature.name)" 
                      class="nature-button el-button"
                  >
                      {{ nature.display }}
                  </el-button>
                  <el-empty v-if="group.natures.length === 0" description="无性格"></el-empty>
              </div>
          </el-collapse-item>
          <el-empty v-if="groupedNatures.length === 0" description="无性格数据"></el-empty>
      </el-collapse>
       <p v-if="loadingMoves" class="loading-text">加载中...</p>
    </div>
    <div v-else-if="type==='tera'" class="button-grid tera-type-list">
       <AttributeIcon 
         v-for="teraType in teraTypes" 
         :key="teraType" 
         :type="teraTypeZh[teraType] || teraType" 
         @click="onSelectTera(teraType)"
         class="tera-type-button-final"
       />
    </div>
    <div v-else-if="type==='ability'" class="button-list">
      <div v-if="normalAbilities.length > 0" class="ability-group">
        <h4>普通特性</h4>
        <div class="button-list">
          <div
            v-for="ability in normalAbilities"
            :key="ability.id || ability.name_en || ability.name_zh"
            class="ability-item"
            @click="$emit('select', ability.name_zh)"
          >
            <div class="ability-name">{{ ability.name_zh || ability.name_en }}</div>
            <div class="ability-desc">{{ ability.description_zh_hans || ability.description_en || '无描述' }}</div>
          </div>
        </div>
      </div>

      <div v-if="hiddenAbilities.length > 0" class="ability-group">
        <h4>隐藏特性</h4>
        <div class="button-list">
           <div
            v-for="ability in hiddenAbilities"
            :key="ability.id || ability.name_en || ability.name_zh"
            class="ability-item"
            @click="$emit('select', ability.name_zh)"
          >
            <div class="ability-name">{{ ability.name_zh || ability.name_en }}</div>
            <div class="ability-desc">{{ ability.description_zh_hans || ability.description_en || '无描述' }}</div>
          </div>
        </div>
      </div>

      <el-empty v-if="abilityList.length === 0 && !loadingAbilities" description="无特性数据或该宝可梦无特性信息"></el-empty>
      <p v-if="loadingAbilities" class="loading-text">加载中...</p>
    </div>
  </div>

  <!-- Pokemon Type Filter Dialog -->
  <el-dialog style="width: 570px;"
    v-model="showPokemonTypeFilterDialog"
    title="选择宝可梦属性 (最多两个)"
    width="500px"
  >
    <div class="type-filter-dialog-content">
      <div class="type-selection-grid">
        <AttributeIcon
          v-for="type in allPokemonTypes"
          :key="type"
          :type="typeZhMap[type] || type"
          :class="['type-filter-icon', { selected: tempSelectedPokemonFilterTypes.includes(type) }]"
          @click="togglePokemonFilterType(type)"
        />
      </div>
      <div v-if="tempSelectedPokemonFilterTypes.length > 0" class="selected-types-display">
        <div style="text-align: left; margin-bottom: 15px; left: 0;">已选属性: </div>
        <div 
          v-for="type in tempSelectedPokemonFilterTypes"
          :key="type"
          class="selected-type-row"
        >
          <AttributeIcon
            :type="typeZhMap[type] || type"
            class="selected-type-icon"
          />
          <el-icon class="remove-type-icon" @click="togglePokemonFilterType(type)"><Close /></el-icon>
        </div>
      </div>
    </div>
    <template #footer>
      <span class="dialog-footer">
        <el-button @click="showPokemonTypeFilterDialog = false">取消</el-button>
        <el-button type="primary" @click="applyPokemonTypeFilter">确定</el-button>
      </span>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, onMounted, computed, watch } from 'vue';
import UserService from '@/services/UserService';
import { ElMessage } from 'element-plus';
import type { ScrollbarInstance } from 'element-plus';
import AttributeIcon from './AttributeIcon.vue';
import { typeZhMap } from '@/utils/constants';
import { Close, Refresh } from '@element-plus/icons-vue';

// 缓存宝可梦和物品数据到 localStorage
function getCachedOrFetch(key: string, fetchFn: () => Promise<any[]>) {
  const cache = localStorage.getItem(key);
  if (cache) {
    try {
      return Promise.resolve(JSON.parse(cache));
    } catch {
      localStorage.removeItem(key);
    }
  }
  return fetchFn().then(data => {
    localStorage.setItem(key, JSON.stringify(data));
    return data;
  });
}

const props = defineProps<{
  type: string,
  currentPokemonData?: any, // Contains species_id and id (form_id)
  generation?: string | number, // e.g., "Gen 9" or 9
  versionGroupId?: number | null, // Actual DB ID for version_group
  allowedItemCategories?: string[] // For item filtering
  selectedMoves?: string[]; // Added for move selection panel to indicate pre-selected moves
}>();
const emit = defineEmits(['select', 'close']);

// Actual search queries that trigger filtering
const searchQueryPokemon = ref('');
const searchQueryItem = ref('');
const searchQueryMove = ref('');

// Debounce utility
function debounce<F extends (...args: any[]) => any>(func: F, waitFor: number) {
  let timeout: ReturnType<typeof setTimeout> | null = null;

  const debounced = (...args: Parameters<F>) => {
    if (timeout !== null) {
      clearTimeout(timeout);
      timeout = null;
    }
    timeout = setTimeout(() => func(...args), waitFor);
  };

  return debounced as (...args: Parameters<F>) => ReturnType<F>;
}

// Debounced versions of search queries for v-model
const setSearchQueryPokemon = debounce((value: string) => {
  searchQueryPokemon.value = value;
  // 当搜索查询变化时，重置并从后端获取数据
  fetchPokemonData(false); 
}, 350);
const searchQueryPokemonDebounced = computed({
  get: () => searchQueryPokemon.value,
  set: (newValue) => setSearchQueryPokemon(newValue)
});

const setSearchQueryItem = debounce((value: string) => searchQueryItem.value = value, 300);
const searchQueryItemDebounced = computed({
  get: () => searchQueryItem.value,
  set: (newValue) => setSearchQueryItem(newValue)
});

const setSearchQueryMove = debounce((value: string) => searchQueryMove.value = value, 300);
const searchQueryMoveDebounced = computed({
  get: () => searchQueryMove.value,
  set: (newValue) => setSearchQueryMove(newValue)
});

const panelTitle = computed(() => {
  switch (props.type) {
    case 'pokemon': return '选择宝可梦';
    case 'item': return '选择道具';
    case 'move': return '选择招式';
    case 'ability': return '选择特性';
    case 'nature': return '选择性格';
    case 'tera': return '选择太晶属性';
    default: return '';
  }
});

const pokemonList = ref<any[]>([]);
const itemList = ref<any[]>([]);
const moveList = ref<any[]>([]);
const abilityList = ref<any[]>([]);

// Pagination for Pokemon List
const pokemonListPageSize = ref(50); // Number of items per page for API request
const pokemonListCurrentOffset = ref(0);
const canLoadMorePokemon = ref(true); 
const pokemonScrollbarRef = ref<ScrollbarInstance>();
const pokemonListTotalCount = ref(0); // <--- 新增：存储总数

const teraTypes = ref<string[]>([
    'Normal', 'Fire', 'Water', 'Grass', 'Electric', 'Ice', 'Fighting', 'Poison', 
    'Ground', 'Flying', 'Psychic', 'Bug', 'Rock', 'Ghost', 'Dragon', 'Dark', 'Steel', 'Fairy',
    'Stellar'
]);

// Mapping English Tera types to Chinese for display
const teraTypeZh: Record<string, string> = {
    'Normal': '一般', 'Fire': '火', 'Water': '水', 'Grass': '草', 'Electric': '电', 'Ice': '冰',
    'Fighting': '格斗', 'Poison': '毒', 'Ground': '地面', 'Flying': '飞行', 'Psychic': '超能力', 'Bug': '虫',
    'Rock': '岩石', 'Ghost': '幽灵', 'Dragon': '龙', 'Dark': '恶', 'Steel': '钢', 'Fairy': '妖精',
    'Stellar': '星晶'
};

const moveCategoryZh: Record<string, string> = {
    'physical': '物理',
    'special': '特殊',
    'status': '变化',
};

const itemCategories = ref<string[]>([]); // Store unique item categories
const selectedItemCategories = ref<string[]>([]); // Store selected categories for filtering

const showPokemonTypeFilterDialog = ref(false);
const selectedPokemonFilterTypes = ref<string[]>([]);
const tempSelectedPokemonFilterTypes = ref<string[]>([]); // Temporary state for dialog selection
const allPokemonTypes = Object.keys(typeZhMap).filter(t => t !== 'unknown' && t !== 'shadow' && t !== 'stellar'); // Get all types, excluding 'unknown', 'shadow' and 'stellar'

const filteredPokemonList = computed(() => {
  // 现在列表直接来自后端，不再需要客户端过滤
  return pokemonList.value;
});

const filteredItemList = computed(() => {
  let currentList = itemList.value;

  // Apply search query filter
  if (searchQueryItem.value) {
    const query = searchQueryItem.value.toLowerCase();
    currentList = currentList.filter(i => 
      (i.name_zh && i.name_zh.toLowerCase().includes(query)) || 
      (i.name && i.name.toLowerCase().includes(query))
    );
  }

  // Apply category filter
  if (selectedItemCategories.value.length > 0) {
    currentList = currentList.filter(item => selectedItemCategories.value.includes(item.category));
  }

  return currentList;
});

const filteredMoveList = computed(() => {
  let currentList = moveList.value;

  if (!searchQueryMove.value && !selectedMoveType.value && !selectedMoveCategory.value) return currentList; // No filters applied, return original list

  const query = searchQueryMove.value.toLowerCase();

  currentList = currentList.filter(m => 
    (m.name_zh && m.name_zh.toLowerCase().includes(query)) || 
    (m.name && m.name.toLowerCase().includes(query))
  );

  // Apply type filter
  if (selectedMoveType.value) {
    currentList = currentList.filter(m => m.type === selectedMoveType.value);
  }

  // Apply category filter
  if (selectedMoveCategory.value) {
     currentList = currentList.filter(m => m.category === selectedMoveCategory.value);
  }

  return currentList;
});

// Computed property to group items by category
const groupedItems = computed(() => {
    let itemsToGroup = itemList.value;
    
    // Apply search filter first
    if (searchQueryItem.value) {
        const query = searchQueryItem.value.toLowerCase();
        itemsToGroup = itemsToGroup.filter(i => 
            (i.name_zh && i.name_zh.toLowerCase().includes(query)) || 
            (i.name && i.name.toLowerCase().includes(query))
        );
    }

    // Group by category
    const groups: { [key: string]: any[] } = {};
    itemsToGroup.forEach(item => {
        const category = item.category || '无分类';
        if (!groups[category]) {
            groups[category] = [];
        }
        groups[category].push(item);
    });

    // Sort categories (optional) and items within categories (optional)
    const sortedCategories = Object.keys(groups).sort();
    const sortedGroups: { category: string; items: any[] }[] = [];
    sortedCategories.forEach(cat => {
      // Optional: sort items within category, e.g., by name_zh
      const sortedItems = groups[cat].sort((a, b) => (a.name_zh || a.name).localeCompare(b.name_zh || b.name, 'zh-CN'));
      sortedGroups.push({ category: cat, items: sortedItems });
    });

    return sortedGroups;
});

// 计算属性：过滤普通特性和隐藏特性
const normalAbilities = computed(() => {
  // 假设 abilityList 中的每个特性对象都有 is_hidden 属性
  return abilityList.value.filter(ab => !ab.is_hidden);
});

const hiddenAbilities = computed(() => {
  return abilityList.value.filter(ab => ab.is_hidden);
});

// Loading states for specific lists
const loadingPokemon = ref(false);
const loadingItems = ref(false);
const loadingMoves = ref(false);
const loadingAbilities = ref(false);

async function fetchPokemonData(isLoadMore = false) {
  if (loadingPokemon.value && isLoadMore) return;
  
  loadingPokemon.value = true;

  if (!isLoadMore) {
    pokemonList.value = [];
    pokemonListCurrentOffset.value = 0;
    pokemonListTotalCount.value = 0; // 重置总数
    canLoadMorePokemon.value = true; 
    pokemonScrollbarRef.value?.setScrollTop(0);
  }

  try {
    // Derive generation ID from props.generation string like "Gen 9" or directly use number/null
    let generationId: number | null | undefined;
    if (typeof props.generation === 'number') {
        generationId = props.generation;
    } else if (typeof props.generation === 'string' && props.generation.toLowerCase().startsWith('gen ')) {
        const genNum = parseInt(props.generation.split(' ')[1]);
        generationId = isNaN(genNum) ? null : genNum;
    } else {
        generationId = undefined; // Default to undefined if generation prop is null, undefined, or in unexpected format
    }

    // Pass the derived generationId (number | null | undefined) to the service
    const response = await UserService.getAllPokemon(
      pokemonListPageSize.value, 
      pokemonListCurrentOffset.value,
      generationId, // Pass the parsed/derived number | null | undefined
      searchQueryPokemon.value || null, // Ensure passing null for empty search
      selectedPokemonFilterTypes.value.join(',') // Add type filtering parameters
    );

    // 增加更严格的检查
    if (response && response.results && typeof response.count === 'number') {
      if (response.results.length > 0) {
        pokemonList.value = isLoadMore ? [...pokemonList.value, ...response.results] : response.results;
        pokemonListCurrentOffset.value += response.results.length;
      }
      pokemonListTotalCount.value = response.count; // 更新总数
      canLoadMorePokemon.value = pokemonList.value.length < pokemonListTotalCount.value;
    } else {
      // 处理 response 无效或不符合预期结构的情况
      console.warn("Received invalid or empty response from getAllPokemon. Response:", response);
      if (!isLoadMore) { // 仅在非加载更多时清空列表和总数
        pokemonList.value = [];
        pokemonListTotalCount.value = 0;
      }
      canLoadMorePokemon.value = false; // 无法加载更多
    }
    
    // 判断是否还能加载更多 (这行现在应该在上面的 if/else 逻辑中处理完毕)
    // canLoadMorePokemon.value = pokemonList.value.length < pokemonListTotalCount.value; // 这行可以移除或注释

  } catch (e) {
    console.error("Error fetching pokemon list:", e);
    ElMessage.error("加载宝可梦列表失败");
    canLoadMorePokemon.value = false; 
  } finally {
    loadingPokemon.value = false;
  }
}

const handlePokemonScroll = ({ scrollTop }: { scrollTop: number, scrollLeft: number }) => {
  if (loadingPokemon.value || !canLoadMorePokemon.value || !pokemonScrollbarRef.value) return;

  const scrollContainer = pokemonScrollbarRef.value.wrapRef;
  if (scrollContainer) {
    const threshold = 50; // Pixels from bottom to trigger load
    const isAtBottom = scrollContainer.scrollTop + scrollContainer.clientHeight >= scrollContainer.scrollHeight - threshold;
    if (isAtBottom) {
      fetchPokemonData(true); // Load more
    }
  }
};

async function fetchItemData() {
  if (loadingItems.value) return;
  loadingItems.value = true;

  try {
    // We are intentionally ignoring props.generation here to fetch all items regardless of generation
    // Update cache key to no longer include generation information
    const cacheKey = `itemListCache-cats-${props.allowedItemCategories?.join('-') || 'all'}`;
    const fetchedItems = await getCachedOrFetch(cacheKey,
        // Pass undefined as the generationId to fetch all items regardless of generation
        () => UserService.getAllItems(undefined, props.allowedItemCategories) 
    );
    
    // Sort items within the fetched list before grouping
    itemList.value = fetchedItems.sort((a: any, b: any) => (a.name_zh || a.name).localeCompare(b.name_zh || b.name, 'zh-CN'));

    // Extract unique categories from the fetched items
    const categories = new Set<string>();
    itemList.value.forEach(item => {
        if (item.category) {
            categories.add(item.category);
        }
    });
    itemCategories.value = Array.from(categories).sort();

  } catch (e) {
    console.error("Error fetching item list:", e);
    ElMessage.error("加载道具列表失败");
  } finally {
    loadingItems.value = false;
  }
}

async function fetchData() {
  // Reset common lists and loading states
  itemList.value = [];
  moveList.value = [];
  abilityList.value = [];
  loadingItems.value = false;
  loadingMoves.value = false;
  loadingAbilities.value = false;
  
  // Pokemon list is handled by fetchPokemonData
  if (props.type === 'pokemon') {
    await fetchPokemonData(false); // Initial fetch for pokemon
  } else if (props.type === 'item') {
    await fetchItemData();
  } else if (props.type === 'move') {
    console.log('Fetching moves...');
    loadingMoves.value = true;
    try {
      let fetchedMoves = [];
      const speciesId = props.currentPokemonData?.species_id;
      const currentGenerationName = typeof props.generation === 'string' ? props.generation.toLowerCase() : null;
      // 将世代名称字符串转换为数字ID
      const generationId = currentGenerationName?.startsWith('gen ') ? parseInt(currentGenerationName.split(' ')[1]) : null;


      // 现在我们使用新的接口，只依赖 species_id 和 generationId
      if (speciesId !== undefined && generationId !== null) {
          console.log(`Fetching learnable moves for Species ID: ${speciesId}, Generation ID: ${generationId}`);
          // 调用新的 Service 方法
          fetchedMoves = await UserService.getLearnableMovesByGeneration(speciesId, generationId);

          // 后端接口已经处理了去重，前端只需接收和处理描述换行符
          moveList.value = Array.isArray(fetchedMoves) ? fetchedMoves.map(move => ({
              ...move,
              desc: (move.desc || '').replace('\n', '') // Remove newlines from desc field
          })) : [];

      } else {
        // 如果没有足够的上下文信息 (Species ID 或 Generation ID 为 null)，清空列表
        console.warn("Cannot fetch learnable moves: Missing Species ID or Generation ID.",
                     "Species ID:", speciesId,
                     "Generation ID:", generationId);
        moveList.value = []; // Clear the move list
        // Optional: Show a message to the user
        // ElMessage.warning("请先选择宝可梦和队伍世代以查看其可学习招式。");
      }

    } catch (e) {
      console.error("Error fetching move list:", e);
      ElMessage.error("加载招式列表失败");
      moveList.value = []; // Clear list on error
    } finally {
      loadingMoves.value = false;
    }
  } else if (props.type === 'ability') {
    console.log('Fetching abilities...');
    console.log('currentPokemonData prop:', props.currentPokemonData);

    loadingAbilities.value = true;
    try {
      let rawAbilities = [];

      // Directly use the abilities array from the currentPokemonData prop if available
      if (props.currentPokemonData?.abilities && Array.isArray(props.currentPokemonData.abilities)) {
           rawAbilities = props.currentPokemonData.abilities;
           console.log('Using abilities from currentPokemonData prop:', rawAbilities);

           // Optional: If you still want to fetch from backend for saved teams to ensure latest data,
           // you could add a condition here:
           // if (props.currentPokemonData.id && !String(props.currentPokemonData.id).startsWith('local-')) {
           //    console.log('Fetching abilities from backend for saved Pokemon:', props.currentPokemonData.id);
           //    rawAbilities = await UserService.getPokemonFormAbilities(props.currentPokemonData.id);
           // }
           // For now, let's prioritize using the prop data as requested.

      } else {
        // If abilities are not available in the prop data, clear the list
        console.warn('Ability list cannot be populated: Abilities not found in currentPokemonData prop.', props.currentPokemonData);
        rawAbilities = []; // Clear the list
      }

      // Normalize the ability data - this is still necessary to ensure consistent structure
      const normalizedAbilities = Array.isArray(rawAbilities) ? rawAbilities.map(ab => {
           if (typeof ab === 'string') {
               // Handle simple string names if they somehow appear
               return {
                   name_en: ab,
                   name_zh: ab,
                   is_hidden: false,
                   description_en: '',
                   description_zh_hans: ''
               };
           } else if (typeof ab === 'object' && ab !== null) {
               // Assume it's an object with expected fields
               return {
                    id: ab.id,
                    name_en: ab.name_en, // Keep English name
                    name_zh: ab.name_zh, // Keep Chinese name
                    description_en: (ab.description_en || '').replace(/\n/g, ''), // Remove newlines
                    description_zh_hans: (ab.description_zh_hans || '').replace(/\n/g, ''), // Remove newlines
                    is_hidden: ab.is_hidden ?? false // Ensure is_hidden exists, default to false
               };
           }
           return null; // Filter out unexpected formats
      }).filter(ab => ab !== null) : [];

       abilityList.value = normalizedAbilities; // Assign the normalized list

    } catch (e) {
      console.error("Error fetching abilities:", e);
      ElMessage.error("加载特性列表失败");
      abilityList.value = []; // Clear list on error
    } finally {
      loadingAbilities.value = false;
    }
  }
}

onMounted(() => {
  console.log('SelectionPanel received generation prop:', props.generation);
  fetchData();
});

// Watch for changes in showPokemonTypeFilterDialog to initialize temp state
watch(showPokemonTypeFilterDialog, (newValue) => {
  if (newValue) {
    // When the dialog is opened, initialize temp state from the current selected types
    tempSelectedPokemonFilterTypes.value = [...selectedPokemonFilterTypes.value];
  }
});

// Watch for changes that require refetching data
watch(
  () => [props.type, props.currentPokemonData?.species_id, props.versionGroupId, props.generation], // Watch species_id, versionGroupId and generation
  async (newValues, oldValues) => {
    const newType = newValues[0];
    const oldType = oldValues ? oldValues[0] : null;
    const newSpeciesId = newValues[1];
    const oldSpeciesId = oldValues ? oldValues[1] : null;
    const newVersionGroupId = newValues[2];
    const oldVersionGroupId = oldValues ? oldValues[2] : null;
    const newGeneration = newValues[3];
    const oldGeneration = oldValues ? oldValues[3] : null;

    // Trigger refetch if type changes
    // Or if type is 'pokemon' and generation changes
    // Or if type is 'move' and species_id or versionGroupId changes
    // Or if type is 'ability' and species_id changes (since abilities come from prop now, only need to trigger if species changes)
    if (
        newType !== oldType ||
        (newType === 'pokemon' && (newGeneration !== oldGeneration)) ||
        (newType === 'move' && (newSpeciesId !== oldSpeciesId || newVersionGroupId !== oldVersionGroupId)) ||
        (newType === 'ability' && (newSpeciesId !== oldSpeciesId))
       )
    {
      // searchQueryPokemon 的变化会通过其自己的 debounced setter -> fetchPokemonData(false)
      // 这里处理其他类型的变化或 pokemon list 的 generation 变化
      if (newType === 'pokemon') {
         // Only refetch pokemon list if generation changes, search is handled by debounced watcher
         if (newGeneration !== oldGeneration) {
            await fetchPokemonData(false);
         }
      } else {
        await fetchData();
      }
    }
  },
  { deep: true } // Deep watch is important for currentPokemonData object properties
);

function getEmptyText(listType: string): string {
    switch(listType) {
        case 'pokemon': 
          return loadingPokemon.value && pokemonList.value.length === 0 ? '加载中...' : 
                 (pokemonListTotalCount.value === 0 && !searchQueryPokemon.value ? '无宝可梦数据' : '无匹配宝可梦');
        case 'item': return loadingItems.value ? '加载中...' : (itemList.value.length === 0 && !searchQueryItem.value ? '无道具数据' : '无匹配数据');
        case 'move': return loadingMoves.value ? '加载中...' : (moveList.value.length === 0 && !searchQueryMove.value ? '无招式数据或该宝可梦无法学会招式' : '无匹配数据');
        case 'ability': return loadingAbilities.value ? '加载中...' : (abilityList.value.length === 0 ? '无特性数据或该宝可梦无特性信息' : '无匹配特性');
        default: return '无数据';
    }
}

function getTypeClass(typeName: string | undefined): string {
  if (!typeName) return 'type-unknown';
  return `type-${typeName.toLowerCase()}`;
}

// Add a function to map backend stat keys to frontend keys
function mapStatKeys(baseStats: any): any {
    const keyMap: Record<string, string> = {
        'hp': 'hp',
        'attack': 'atk',
        'defense': 'def',
        'special-attack': 'spa',
        'special-defense': 'spd',
        'speed': 'spe',
    };
    const mappedStats: any = {};
    for (const backendKey in baseStats) {
        if (keyMap[backendKey]) {
            mappedStats[keyMap[backendKey]] = baseStats[backendKey];
        } else {
            // Keep other keys if any, or log a warning
            mappedStats[backendKey] = baseStats[backendKey];
        }
    }
    return mappedStats;
}

function onSelectPokemon(row: any) {
  // Map base_stats keys before emitting
  const pokemonWithMappedStats = {
    ...row,
    base_stats: mapStatKeys(row.base_stats)
  };
  emit('select', pokemonWithMappedStats);
}

function onSelectItem(row: any) {
  emit('select', row);
}

function onSelectMove(row: any) {
  // Prevent selection if the move is already in the selectedMoves prop
  if (props.selectedMoves?.includes(row.name_zh)) {
    ElMessage.warning('该招式已被选中');
    return; 
  }
  emit('select', row);
}

const activeCategories = ref<string[]>([]); // Control active collapse items

// Map for item category localization
const itemCategoryZh: Record<string, string> = {
    'held-items': '一般携带道具',
    'medicine': '树果',
    'mega-stones': '超级石',
    'z-crystals': 'Z 纯晶',
    'plates': '石板系列',
    'bad-held-items': '负面道具', // 例如：紧缠带
    'choice': '讲究/专爱系列', // 例如：讲究系列
    'picky-healing': '巨树果', // 巨树果
    'species-specific': '专属道具', // 例如：各种专属道具
    '无分类': '无分类', // Handle items without a category
};

// Watch groupedItems to expand all panels by default when data loads
watch(groupedItems, (newGroups) => {
    if (newGroups && newGroups.length > 0) {
        // Expand all groups by default except 'bad-held-items'
        activeCategories.value = newGroups
            .filter(group => group.category !== 'bad-held-items')
            .map(group => group.category);
    }
}, { immediate: true });

// Computed property to group natures by stat effect
const NATURE_EFFECTS: Record<string, { increased: string | null, decreased: string | null }> = {
  // Format: NatureName: { increased: 'stat_key', decreased: 'stat_key' }
  // HP is never affected by nature
  '固执': { increased: 'atk', decreased: 'spa' }, '怕寂寞': { increased: 'atk', decreased: 'def' },
  '顽皮': { increased: 'atk', decreased: 'spd' }, '勇敢': { increased: 'atk', decreased: 'spe' },
  '大胆': { increased: 'def', decreased: 'atk' }, '悠闲': { increased: 'def', decreased: 'spe' },
  '淘气': { increased: 'def', decreased: 'spa' }, '乐天': { increased: 'def', decreased: 'spd' }, //淘气 Impish, 乐天 Lax
  '内敛': { increased: 'spa', decreased: 'atk' }, '慢吞吞': { increased: 'spa', decreased: 'spe' },
  '马虎': { increased: 'spa', decreased: 'spd' }, '冷静': { increased: 'spa', decreased: 'def' },
  '温和': { increased: 'spd', decreased: 'atk' }, '温顺': { increased: 'spd', decreased: 'def' }, //温顺 Gentle
  '慎重': { increased: 'spd', decreased: 'spa' }, '自大': { increased: 'spd', decreased: 'spe' }, //自大 Sassy
  '胆小': { increased: 'spe', decreased: 'atk' }, '急躁': { increased: 'spe', decreased: 'def' }, //急躁 Hasty
  '爽朗': { increased: 'spe', decreased: 'spa' }, '天真': { increased: 'spe', decreased: 'spd' }, //天真 Naive
  // Neutral Natures
  '勤奋': { increased: null, decreased: null }, '坦率': { increased: null, decreased: null },
  '害羞': { increased: null, decreased: null }, '浮躁': { increased: null, decreased: null },
  '认真': { increased: null, decreased: null },
};

const statLabelZh: Record<string, string> = { hp: 'HP', atk: '攻击', def: '防御', spa: '特攻', spd: '特防', spe: '速度' };

const groupedNatures = computed(() => {
  const groups: { [key: string]: { increased: string | null, natures: { name: string; display: string }[] } } = {};

  const statOrder = ['atk', 'def', 'spa', 'spd', 'spe']; // Desired sort order for stats

  for (const natureName in NATURE_EFFECTS) {
    const effects = NATURE_EFFECTS[natureName];
    const increasedStat = effects.increased || 'neutral'; // Group neutral natures under 'neutral'
    const decreasedStat = effects.decreased;

    // Format display string
    let displayString = natureName;
    const statEffects: string[] = [];
    if (increasedStat !== 'neutral' && statLabelZh[increasedStat]) {
        statEffects.push(`+${statLabelZh[increasedStat]}`);
    }
    if (decreasedStat && statLabelZh[decreasedStat]) {
        statEffects.push(`-${statLabelZh[decreasedStat]}`);
    }
    if (statEffects.length > 0) {
        displayString += ` (${statEffects.join(', ')})`;
    }

    if (!groups[increasedStat]) {
        groups[increasedStat] = { increased: effects.increased, natures: [] };
    }
    groups[increasedStat].natures.push({ name: natureName, display: displayString });
  }

  // Convert groups object to sorted array
  const sortedGroups = Object.keys(groups)
    .sort((a, b) => {
        const indexA = statOrder.indexOf(a);
        const indexB = statOrder.indexOf(b);
        if (indexA === -1 && indexB === -1) return 0; // Both neutral or unknown, keep order
        if (indexA === -1) return 1; // a is neutral/unknown, sort after b
        if (indexB === -1) return -1; // b is neutral/unknown, sort after a
        return indexA - indexB; // Sort by predefined stat order
    })
    .map(key => groups[key]);

    // Optional: Sort natures within each group by name
    sortedGroups.forEach(group => {
        group.natures.sort((a, b) => a.name.localeCompare(b.name, 'zh-CN'));
    });

  return sortedGroups;
});

// Computed property to get the list of active categories for el-collapse
// Initially empty, will be populated on data load to expand all by default
const activeNatureGroups = ref<string[]>([]); // Control active collapse items

// Watch groupedNatures to expand all panels by default
watch(groupedNatures, (newGroups) => {
    if (newGroups && newGroups.length > 0) {
        // Expand all groups except the 'neutral' group by default
        activeNatureGroups.value = newGroups
            .filter(group => group.increased !== null) // Exclude neutral group (which has increased: null)
            .map(group => group.increased as string); // Cast to string after filtering nulls
    }
}, { immediate: true });

// Function to handle Tera type selection (re-added)
function onSelectTera(teraType: string) {
    emit('select', teraType);
}

function getRowClassName({ row }: { row: any }): string {
  // Check if the move's Chinese name is included in the selectedMoves array
  // Use optional chaining (?) and nullish coalescing (?? '') for safety
  if (props.selectedMoves?.includes(row.name_zh ?? '')) {
    return 'selected-move-row';
  }
  return '';
}

const selectedMoveType = ref<string | null>(null);
const selectedMoveCategory = ref<string | null>(null);
const uniqueMoveTypes = computed(() => {
  return new Set(moveList.value.map(m => m.type));
});
const uniqueMoveCategories = computed(() => {
  return new Set(moveList.value.map(m => m.category));
});

function togglePokemonFilterType(type: string) {
  const index = tempSelectedPokemonFilterTypes.value.indexOf(type);
  if (index > -1) {
    // Type is already selected in temp state, remove it
    tempSelectedPokemonFilterTypes.value.splice(index, 1);
  } else {
    // Type is not selected in temp state, add it if less than 2 are already selected
    if (tempSelectedPokemonFilterTypes.value.length < 2) {
      tempSelectedPokemonFilterTypes.value.push(type);
    } else {
      ElMessage.warning('最多只能选择两个属性进行筛选');
    }
  }
}

function applyPokemonTypeFilter() {
  // Apply the temporary selection to the actual filter state
  selectedPokemonFilterTypes.value = [...tempSelectedPokemonFilterTypes.value];
  fetchPokemonData(false);
  showPokemonTypeFilterDialog.value = false;
}

function removePokemonFilterType(type: string) {
  selectedPokemonFilterTypes.value = selectedPokemonFilterTypes.value.filter(t => t !== type);
  // Re-apply filter immediately after removing a type
  fetchPokemonData(false);
}

function clearPokemonTypeFilter() {
  selectedPokemonFilterTypes.value = []; // Clear the selected types array
  fetchPokemonData(false); // Fetch data without filters
}

function closeActivePanel() {
  showPokemonTypeFilterDialog.value = false;
}

function handlePanelSelection(selectedData: any) {
  // ... existing code ...
}

function calculateMaxPP(originalPP: number | null): number | string {
  if (originalPP === null) {
    return '—';
  }
  if (originalPP === 1) {
    return 1;
  }
  // Calculate 1.6 times the original PP. Since original PP > 1 is usually divisible by 5, 1.6 times will be an integer.
  return Math.round(originalPP * 1.6);
}
</script>

<style scoped>
.selection-panel {
  width: 96%;
  background: #fff;
  border-radius: 8px;
  padding: 16px;
}

.pokemon-list-scrollbar {
  border: 1px solid #ebeef5;
  border-radius: 4px;
}

.loading-more-text {
  text-align: center;
  color: #909399;
  padding: 10px 0;
  font-size: 0.9em;
}

.panel-controls {
  margin-bottom: 10px;
  display: flex;
  gap: 10px;
  align-items: center;
}
.search-input {
  flex-grow: 1;
}

.nature-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin: 12px 0;
}

.button-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(100px, 1fr));
  gap: 8px;
  margin-top: 10px;
}

.button-list {
    display: flex;
    flex-direction: column;
    gap: 8px;
    margin-top: 10px;
}

.ability-item {
    padding: 8px 12px;
    border: 1px solid #e0e0e0;
    border-radius: 4px;
    cursor: pointer;
    transition: background-color 0.2s, border-color 0.2s;
    display: flex;
    align-items: center;
    gap: 8px;
}

.ability-item:hover {
    background-color: #f5f5f5;
    border-color: #409EFF;
}

.ability-name {
    font-weight: bolder;
}

.ability-desc {
    font-size: 0.9em;
    color: #666;
    margin-left: 50px;
}

.grid-button {
  width: 100%; /* Make buttons in grid take full cell width */
}

/* Type Tag base style - assumed to be in global CSS like pokemon-types.css */
/* These styles are duplicated here for completeness if global CSS is not set up yet */
.scaled-attribute-icon {
  transform: scale(0.8); /* Adjusted scale for the selection panel lists, closer to config view */
  transform-origin: left center; /* Scale from the left center */
  margin-right: 2px; /* Adjust margin to compensate for new scale, positive gap */
  margin-left: 2px; /* Adjust margin for new scale, positive gap */
}

.type-tag {
  padding: 4px 8px;
  border-radius: 4px;
  color: white !important; /* Important to override ElButton text color */
  font-size: 12px;
  text-align: center;
  text-transform: uppercase;
  border: none; /* Remove ElButton border */
}
.type-tag:hover,
.type-tag:focus {
  color: white; /* Keep text color on hover/focus */
  opacity: 0.9;
}

.type-normal { background-color: #A8A878; }
.type-fighting { background-color: #C03028; }
.type-flying { background-color: #A890F0; }
.type-poison { background-color: #A040A0; }
.type-ground { background-color: #E0C068; }
.type-rock { background-color: #B8A038; }
.type-bug { background-color: #A8B820; }
.type-ghost { background-color: #705898; }
.type-steel { background-color: #B8B8D0; }
.type-fire { background-color: #F08030; }
.type-water { background-color: #6890F0; }
.type-grass { background-color: #78C850; }
.type-electric { background-color: #F8D030; }
.type-psychic { background-color: #F85888; }
.type-ice { background-color: #98D8D8; }
.type-dragon { background-color: #7038F8; }
.type-dark { background-color: #705848; }
.type-fairy { background-color: #EE99AC; }
.type-unknown { background-color: #68A090; } /* For unknown or typeless, e.g. Stellar */

.nature-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin: 12px 0;
}

.item-category-filter {
    margin-bottom: 10px;
    padding-bottom: 10px;
    border-bottom: 1px solid #eee;
}

.item-category-filter .el-check-tag {
    cursor: pointer;
}

.item-category-collapse {
    margin-top: 10px;
}

.item-list-in-group {
    padding-left: 10px;
}

.item-row {
    display: flex;
    align-items: center;
    padding: 8px 0;
    border-bottom: 1px dashed #eee;
    cursor: pointer;
    transition: background-color 0.2s;
}

.item-row:hover {
    background-color: #f5f5f5;
}

.item-sprite,
.item-sprite-placeholder {
    width: 24px;
    height: 24px;
    object-fit: contain;
    margin-right: 10px;
    flex-shrink: 0; /* Prevent shrinking */
}

.item-sprite-placeholder {
    display: flex;
    align-items: center;
    justify-content: center;
    background-color: #eee;
    border-radius: 4px;
    color: #999;
    font-size: 1.2em;
}

.item-name {
    font-weight: bold;
    margin-right: 10px;
    flex-shrink: 0; /* Prevent shrinking */
    width: 120px; /* Adjust as needed */
}

.item-effect {
    flex-grow: 1;
    color: #666;
    font-size: 0.9em;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}

.loading-text {
    text-align: center;
    color: #909399;
    padding: 10px 0;
    font-size: 0.9em;
}

.nature-list-in-group {
    /* Use flex for button layout */
    display: flex;
    flex-wrap: wrap; /* Allow buttons to wrap to the next line */
    gap: 6px; /* Adjust gap */
    padding: 8px; /* Smaller padding */
    background-color: #f8f8f8;
    border-radius: 4px;
    justify-content: center; /* Center flex items along the main axis (horizontal) */
}

.nature-button {
    /* Remove width: 100%; when using flexbox to allow items to size based on content/min-width */
    /* You might keep a min-width if needed */
    min-width: 120px; /* Keep a minimum width */
    text-align: center; /* Align text to center */
    padding: 8px 12px; /* Keep padding */
    display: flex;
    justify-content: center; /* Center horizontally within the button */
    align-items: center;
    height: auto; /* Allow height to adjust based on content */
    /* Remove justify-self in flex context */
}

/* Optional: styles to reduce collapse item content padding */
/* You might need to target a deeper class like .el-collapse-item__content */
/* For example: */
/* :deep(.el-collapse-item__content) { padding-bottom: 10px; } */

/* Adjust padding within collapse item content */
:deep(.el-collapse-item__content) {
    padding-bottom: 10px;
    padding-top: 0;
    padding-left: 0;
    padding-right: 0;
}

.nature-collapse {
    width: 100%; /* Ensure el-collapse takes full width */
    font-size: 0.9em;
    font-weight: bold;
}

/* Add styles for the new nature selection container */
.nature-selection-container {
    /* This should be a block element by default, taking full width */
    margin-top: 10px; /* Add some top margin for spacing */
}

.tera-type-button-final {
    width: 100%; /* Make it fill the grid cell */
    height: 40px; /* Fixed height */
    cursor: pointer; /* Indicate clickable */
    border-radius: 4px; /* Match button border radius */
    transition: opacity 0.2s; /* Add hover effect transition */
    overflow: hidden; /* Hide overflowing content */
}

.tera-type-button-final:hover {
    opacity: 0.8; /* Reduce opacity on hover */
}

/* Styles for the internal attribute div within the scaled AttributeIcon */
.tera-type-button-final :deep(.attribute) {
    width: 100%; /* Fill parent width */
    height: 100%; /* Fill parent height */
    display: flex; /* Use flexbox */
    flex-direction: column; /* Stack icon and text vertically */
    align-items: center; /* Center horizontally */
    justify-content: center; /* Center vertically */
    padding: 0; /* Remove internal padding if parent provides it */
    box-sizing: border-box; /* Include padding in dimensions */
    border-radius: 4px; /* Match button border radius */
    /* Background color/gradient handled by AttributeIcon's getAttributeStyles */
}

/* Further simplified styles for the internal attribute-icon div */
.tera-type-button-final :deep(.attribute-icon) {
    width: 20px; /* Revert to original icon size */
    height: 20px; /* Revert to original icon size */
    margin-bottom: 2px; /* Space between icon and text */
    /* Rely on AttributeIcon's getAttributeIconStyles for background */
    background-size: contain;
    background-repeat: no-repeat;
    background-position: center;
    /* Remove background-image: var(...) as it might conflict */
}

/* Styles for the internal span (text) */
.tera-type-button-final :deep(span) {
    font-size: 0.9em; /* Adjust text size, slightly larger */
    font-weight: bold; /* Make text bold */
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    /* Text color handled by AttributeIcon internal span */
}

/* Ensure Stellar text color is white */
.tera-type-button-final.type-stellar :deep(span) {
    color: white;
}

.button-grid.tera-type-list {
    padding: 0 10px; /* Add symmetric padding to the container */
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

/* Style for selected move rows */
.selected-move-row {
  background-color: #cccccc !important; /* Slightly darker grey background */
  /* You can add other styles like font-weight or border here */
  font-weight: bold !important;
}
.selected-move-row:hover {
  background-color: #b7b6b6 !important; /* Darker grey on hover */
  cursor: not-allowed; /* Change cursor */
}

/* Pokemon Type Filter Dialog */
.type-filter-dialog-content {
  padding: 10px;
  width: 100%;
}

.type-selection-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 50px;
}

.type-filter-icon {
  width: 80px; /* Adjusted size */
  height: 25px; /* Adjusted size */
  cursor: pointer;
  transition: opacity 0.2s;
}

.type-filter-icon:hover {
  opacity: 0.8;
}

.type-filter-icon.selected {
  border: 2px solid #409EFF; /* Highlight with primary color */
  box-sizing: border-box; /* Ensure border doesn't add to size */
}

.selected-types-display {
  margin-top: 10px;
  margin-left: 20px;
  text-align: left;
}

.selected-type-row {
  display: flex;
  align-items: center;
  gap: 8px; /* Space between icon and close button */
  margin-bottom: 8px; /* Space between rows */
}

.remove-type-icon {
  cursor: pointer;
  color: #f56c6c; /* Danger color */
  font-size: 1.2em; /* Slightly larger icon */
}

.selected-type-icon {
  width: 80px; /* Keep the adjusted size */
  height: 25px; /* Keep the adjusted size */
}

.dialog-footer {
  text-align: right;
}

.el-dialog__title {
  font-weight: bold;
}
</style>
