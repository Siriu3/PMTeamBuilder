// src/router/index.ts
import { createRouter, createWebHistory } from 'vue-router';
import { useAuthStore } from '../stores/auth'; // 导入 AuthStore 用于路由守卫
import { ElMessage } from 'element-plus'; // Import ElMessage


// 路由懒加载示例
const HomeView = () => import('../views/HomeView.vue');
const LoginView = () => import('../views/LoginView.vue');
const RegisterView = () => import('../views/RegisterView.vue');
const VerifyEmailView = () => import('../views/VerifyEmailView.vue');
const ProfileView = () => import('../views/ProfileView.vue');
const MyTeamsView = () => import('../views/MyTeamsView.vue');
const FavoritesView = () => import('../views/FavoritesView.vue');
const AdminView = () => import('../views/AdminView.vue');
const TeamReviewView = () => import('../components/Admin/AdminTeamReview.vue');
const ReportsView = () => import('../components/Admin/AdminReportManagement.vue');
const SensitiveWordsView = () => import('../components/Admin/AdminSensitiveWords.vue');
const TeamView = () => import('../views/TeamView.vue'); // Import TeamView
const TeamShareView = () => import('../views/TeamShareView.vue'); // Import the new view
const TeamSquareView = () => import('../views/TeamSquareView.vue'); // Import TeamSquareView
// const NotificationPage = () => import('../views/user/NotificationPage.vue'); // Remove NotificationPage import

const routes = [
  {
    path: '/',
    name: 'Home',
    component: HomeView,
    meta: { requiresAuth: false } // 不需要认证
  },
  {
    path: '/login',
    name: 'Login',
    component: LoginView,
    meta: { requiresAuth: false } // 不需要认证
  },
  {
    path: '/register',
    name: 'Register',
    component: RegisterView,
    meta: { requiresAuth: false } // 不需要认证
  },
  {
    path: '/verify-email/:token', // 邮箱验证路由，从URL参数中获取令牌
    name: 'VerifyEmail',
    component: VerifyEmailView,
    meta: { requiresAuth: false } // 不需要认证
  },
  {
    path: '/profile',
    name: 'Profile',
    component: ProfileView,
    meta: { requiresAuth: true }, // 需要认证
    // Remove children routes if no other child routes are planned under /profile
    // children: [
    //   {
    //     path: 'notifications', // Remove this child route
    //     name: 'ProfileNotifications',
    //     component: NotificationPage,
    //     meta: { requiresAuth: true }
    //   }
    // ]
  },
  {
    path: '/my-teams',
    name: 'MyTeams',
    component: MyTeamsView,
    meta: { requiresAuth: true } // 需要认证
  },
  {
    path: '/favorites',
    name: 'Favorites',
    component: FavoritesView,
    meta: { requiresAuth: true } // 需要认证
  },
  {
    path: '/admin',
    name: 'Admin',
    component: AdminView,
    meta: { requiresAuth: true, requiresAdmin: true }, // 需要认证和管理员权限
    children: [
      {
        path: 'review',
        name: 'TeamReview',
        component: TeamReviewView
      },
      {
        path: 'reports',
        name: 'Reports',
        component: ReportsView
      },
      {
        path: 'sensitive-words',
        name: 'SensitiveWords',
        component: SensitiveWordsView
      }
    ]
  },
  {
    path: '/team-builder',
    name: 'TeamBuilder',
    component: () => import('@/views/TeamBuilderView.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/team-builder/:teamId',
    name: 'TeamBuilderEdit',
    component: () => import('@/views/TeamBuilderEditView.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/teams/:teamId', // New route for viewing a team
    name: 'TeamView',
    component: TeamView,
    props: true, // Pass teamId from route params as a prop
    meta: { requiresAuth: false } // Adjust auth requirement as needed
  },
  // === 新增分享路由 ===
  {
    path: '/team/share/:token',
    name: 'TeamShare',
    component: TeamShareView,
    props: true, // Pass token from route params as a prop
    meta: { requiresAuth: false } // 分享链接不需要认证
  },
  // =====================
  // === 新增团队广场路由 ===
  {
    path: '/square', // 使用 /square 路由
    name: 'TeamSquare',
    component: TeamSquareView, // 指向 TeamSquareView 组件
    meta: { requiresAuth: false } // 团队广场通常是公开的，不需要认证
  }
  // =====================
];

const router = createRouter({
  history: createWebHistory(),
  routes
});

// 全局前置守卫
router.beforeEach(async (to, from, next) => {
  const authStore = useAuthStore();
  const isAuthenticated = authStore.isAuthenticated; // Assume isAuthenticated is a getter in authStore
  const isAdmin = authStore.currentUser?.isAdmin; // 从 currentUser 获取 isAdmin

  // 1. 登录/注册页面的守卫：如果已登录，重定向到首页
  // Note: The original code used requiresGuest meta, but it's not defined in the routes.
  // We will add a check for login/register pages if authenticated.
  if ((to.name === 'Login' || to.name === 'Register') && isAuthenticated) {
      next({ name: 'Home' });
      return;
  }

  // 2. 认证守卫：需要登录才能访问的页面
  if (to.meta.requiresAuth && !isAuthenticated) {
    next({ name: 'Login' });
    return;
  }

  // 3. 管理员权限守卫：需要管理员权限才能访问的页面
  if (to.meta.requiresAdmin && (!isAuthenticated || !isAdmin)) {
    // 强制跳转到首页或显示无权限提示
    next({ name: 'Home' }); // 或者 next('/unauthorized')
    ElMessage.warning('您没有权限访问此页面。'); // 提示信息
    return;
  }

  next(); // 继续导航
});

export default router;