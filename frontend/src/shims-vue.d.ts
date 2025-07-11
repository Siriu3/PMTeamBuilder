// 声明 .vue 文件模块，允许 TypeScript 识别 .vue 文件
declare module '*.vue' {
  import { DefineComponent } from 'vue'
  const component: DefineComponent<{}, {}, any>
  export default component
}

// 定义 AttributeIcon 组件的 props 接口
interface AttributeIconProps {
  type: string;
  // 如果 AttributeIcon.vue 有其他 props，请在此处添加
}

// 声明 ./AttributeIcon.vue 模块，为 AttributeIcon 组件提供类型定义
declare module './AttributeIcon.vue' {
  import { DefineComponent } from 'vue';
  const AttributeIcon: DefineComponent<AttributeIconProps, {}, any>;
  export default AttributeIcon;
}
