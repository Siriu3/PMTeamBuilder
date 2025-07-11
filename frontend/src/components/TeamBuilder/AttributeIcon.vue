<template>
  <div class="attribute" :style="getAttributeStyles(type)">
    <div class="attribute-icon" :style="getAttributeIconStyles(type)"></div>
    <span>{{ typeZh[type] || type }}</span>
  </div>
</template>

<script>
import { computed } from 'vue';

export default {
  name: 'AttributeIcon',
  props: {
    type: {
      type: String,
      required: true
    }
  },
  setup(props) {
    const colors = {
      '一般': { color: '#9fa19f', index: 0 },
      '格斗': { color: '#ff8000', index: 1 },
      '飞行': { color: '#81b9ef', index: 2 },
      '毒': { color: '#9141cb', index: 3 },
      '地面': { color: '#915121', index: 4 },
      '岩石': { color: '#afa981', index: 5 },
      '虫': { color: '#91a119', index: 6 },
      '幽灵': { color: '#704170', index: 7 },
      '钢': { color: '#60a1b8', index: 8 },
      '火': { color: '#e62829', index: 9 },
      '水': { color: '#2980ef', index: 10 },
      '草': { color: '#3fa129', index: 11 },
      '电': { color: '#fac000', index: 12 },
      '超能力': { color: '#ef4179', index: 13 },
      '冰': { color: '#3fbeff', index: 14 },
      '龙': { color: '#5060e1', index: 15 },
      '恶': { color: '#50413f', index: 16 },
      '妖精': { color: '#ef70ef', index: 17 },
      // Add Stellar type
      '星晶': { 
        // Using a conical gradient with colors closest to the rainbow spectrum in counter-clockwise order and adjusted angles for more red and less purple area
        background: 'conic-gradient(from 0deg, #e62829 0deg, #ef4179 35deg, #ef70ef 55deg, #704170 75deg, #9141cb 85deg, #5060e1 115deg, #3fbeff 145deg, #81b9ef 185deg, #2980ef 215deg, #3fa129 245deg, #fac000 280deg, #ff8000 305deg, #e62829 350deg)' 
      },
      '':{} // Handle empty type
    };

    // Mapping English types to Chinese for display, if needed elsewhere
    // const typeZhMap = {
    //     'Normal': '一般', 'Fighting': '格斗', 'Flying': '飞行', 'Poison': '毒',
    //     'Ground': '地面', 'Rock': '岩石', 'Bug': '虫', 'Ghost': '幽灵',
    //     'Steel': '钢', 'Fire': '火', 'Water': '水', 'Grass': '草',
    //     'Electric': '电', 'Psychic': '超能力', 'Ice': '冰', 'Dragon': '龙',
    //     'Dark': '恶', 'Fairy': '妖精', 'Stellar': '星晶'
    // };

    // Mapping Chinese types to Chinese for display (汉化)
    const typeZh = {
      '一般': '一般',
      '格斗': '格斗',
      '飞行': '飞行',
      '毒': '毒',
      '地面': '地面',
      '岩石': '岩石',
      '虫': '虫',
      '幽灵': '幽灵',
      '钢': '钢',
      '火': '火',
      '水': '水',
      '草': '草',
      '电': '电',
      '超能力': '超能力',
      '冰': '冰',
      '龙': '龙',
      '恶': '恶',
      '妖精': '妖精',
      '星晶': '星晶',
      '':'' // Handle empty type
    };

    const getAttributeStyles = (type) => {
      const typeInfo = colors[type] || colors[''];
      if (type === '星晶') {
          return {
              background: typeInfo.background, // Use 'background' to potentially override other background properties
              // Add border or other styles if needed
          };
      } else {
          return {
              backgroundColor: typeInfo.color, // Use solid color for other types
          };
      }
    };

    const getAttributeIconStyles = (type) => {
        if (type === '星晶') {
            // For Stellar, use a separate local image
            return {
                backgroundImage: 'url(/Stellar_icon.png)', // Path to the Stellar icon
                backgroundSize: 'contain', // Ensure the whole icon is visible
                backgroundRepeat: 'no-repeat',
                backgroundPosition: 'center', // Center the icon
            };
        } else {
            // For other types, use the sprite sheet
            const index = colors[type]?.index;
            if (index === undefined || index === null) return {}; // Handle unknown/empty types gracefully
            const offsetY = -index * 20;
            return {
                backgroundImage: 'url(/MST_SV.webp)', // Path to the sprite sheet
                backgroundSize: 'cover', // Or adjust based on your sprite sheet size and desired effect
                backgroundPosition: `0px ${offsetY}px`,
            };
        }
    };

    return {
      colors,
      typeZh,
      getAttributeStyles,
      getAttributeIconStyles,
    };
  }
};
</script>

<style scoped>
.attribute {
  display: grid;
  grid-template-columns: auto 1fr; /* Define two columns: auto for the icon and 1fr for the text */
  align-items: center;
  justify-items: center; /* Ensure elements are centered */
  width: 75px; /* Keep fixed width */
  height: 26px;
  border-radius: 14px;
  padding: 0 5px;
  box-sizing: border-box; /* Include padding in width */
  overflow: hidden; /* Hide anything outside border-radius */
}
.attribute span {
  color: white;
  font-size: 0.9em;
  font-weight: bold;
  text-align: center; /* Center text horizontally */
  white-space: nowrap; /* Prevent text wrapping */
  overflow: hidden; /* Hide overflowing text */
  text-overflow: ellipsis; /* Add ellipsis to overflowing text */
  padding-left: 2px; /* Add a little space between icon and text */
  padding-right: 2px; /* Add some right padding */
}
.attribute-icon {
  width: 20px;
  height: 20px;
  /* Background styles are now handled by getAttributeIconStyles computed property */
}
</style>
