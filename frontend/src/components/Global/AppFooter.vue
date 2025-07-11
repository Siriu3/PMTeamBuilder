<template>
  <div class="footer-container">
    <div class="copyright-section">
        <div class="about">© 2025 宝可梦队伍构建系统 by 3irius</div>
        <div class="about">Pokémon © 2002-2025 Pokémon. © 1995-2025 Nintendo/Creatures Inc./GAME FREAK inc.</div>
        <div class="about">"精灵宝可梦"、"宝可梦"、"Pokémon"是任天堂的商标</div>
    </div>
  </div>
</template>

<style scoped>

.footer-container {
  position: relative;
  bottom: 0;
  left: 0;
  right: 0;
  width: 100%;
  height: 100px; /* 设置页脚固定高度 */
  display: flex;
  align-items: center; /* 垂直居中内容 */
  box-sizing: border-box; /* 将 padding 和 border 包含在元素的总宽度和高度内 */
  padding: 20px 20px; /* 添加左右内边距 */
}

.copyright-section {
    text-align: left;
    margin-left: 30px; /* 调整左边距 */
    margin-right: 30px; /* 调整左边距 */
    border-top: 1px solid #ccc; /* 添加顶部边框作为分割线 */
    padding-top: 20px; /* 为 copyright-section 添加顶部填充 */
    padding-bottom: 20px; /* 为 copyright-section 添加底部填充 */
    width: 100%; /* 确保 copyright-section 占据 footer-container 的宽度 */
}

.about {
  font-size: 0.7em;
  color: #5f6163;
  margin-top: 3px;
}
</style> 