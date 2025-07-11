// frontend/src/stores/notification.ts
import { defineStore } from 'pinia';
import { ref } from 'vue';
import { ElMessage } from 'element-plus';
import NotificationService from '@/services/NotificationService';

// Define notification type interface (adjust based on backend structure)
interface Notification {
  id: number | string;
  user_id: number | string;
  type: string; // e.g., 'report_handled', 'team_affected_by_report'
  related_id?: number | string | null;
  content: string;
  created_at: string;
  is_read: boolean;
}

export const useNotificationStore = defineStore('notification', () => {
  // State
  const notifications = ref<Notification[]>([]);
  const pagination = ref({ total: 0, page: 1, per_page: 10 });
  const isLoading = ref(false);
  const unreadCount = ref(0);

  // Actions
  const fetchNotifications = async (page = 1, perPage = 10, isRead: boolean | null = null) => {
    try {
      isLoading.value = true;
      const response = await NotificationService.getUserNotifications(page, perPage, isRead);

      notifications.value = response.items || [];
      pagination.value = {
        total: response.total || 0,
        page: response.page || page,
        per_page: response.per_page || perPage,
      };

      ElMessage.success('通知列表加载成功！');
      return true;
    } catch (error: any) {
      console.error('获取通知列表失败:', error);
      ElMessage.error(error.response?.data?.message || '获取通知列表失败。');
      return false;
    } finally {
      isLoading.value = false;
    }
  };

  const fetchUnreadCount = async () => {
    try {
      const count = await NotificationService.getUnreadCount();
      unreadCount.value = count;
    } catch (error: any) {
      console.error('获取未读通知数量失败:', error);
    }
  };

  const markNotificationAsRead = async (notificationId: number | string) => {
    try {
      const notification = notifications.value.find(notif => notif.id === notificationId);
      if (notification && !notification.is_read) {
         await NotificationService.markNotificationAsRead(notificationId);
        // Update local state
        notification.is_read = true;
        // Decrement unread count
        if (unreadCount.value > 0) {
            unreadCount.value--;
        }
         ElMessage.success('通知已标记为已读！');
      } else if (notification && notification.is_read) {
          ElMessage.info('该通知已是已读状态。');
      } else {
           ElMessage.warning('未找到该通知。');
      }

      return true;
    } catch (error: any) {
      console.error('标记通知为已读失败:', error);
      ElMessage.error(error.response?.data?.message || '标记通知为已读失败。');
      return false;
    }
  };

  // New action to mark all notifications as read
  const markAllAsRead = async () => {
    try {
       isLoading.value = true; // Indicate loading for this action
       await NotificationService.markAllNotificationsAsRead();

      // Update local state: mark all currently loaded notifications as read
      notifications.value.forEach(notif => {
         notif.is_read = true;
      });
      // Reset unread count
      unreadCount.value = 0;

      ElMessage.success('所有通知已标记为已读！');
      return true;
    } catch (error: any) {
      console.error('一键已读失败:', error);
      ElMessage.error(error.response?.data?.message || '一键已读失败。');
      return false;
    } finally {
       isLoading.value = false;
    }
  };

  return {
    notifications,
    pagination,
    isLoading,
    unreadCount,
    fetchNotifications,
    fetchUnreadCount,
    markNotificationAsRead,
    markAllAsRead, // Export the new action
  };
}); 