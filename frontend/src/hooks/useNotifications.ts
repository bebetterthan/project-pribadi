/**
 * Notification Hook - Real-time notifications with polling
 * FASE 6: Frontend UI Excellence
 */
import { useState, useEffect, useCallback } from 'react';
import { API_BASE_URL } from '@/lib/constants';

export interface Notification {
  id: string;
  type: string;
  title: string;
  message: string;
  resource_type?: string;
  resource_id?: string;
  priority: string;
  is_read: boolean;
  created_at: string;
  read_at?: string;
}

export function useNotifications(pollingInterval: number = 30000) {
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [unreadCount, setUnreadCount] = useState(0);
  const [isLoading, setIsLoading] = useState(true);

  const fetchNotifications = useCallback(async () => {
    try {
      // Add trailing slash to avoid 307 redirect
      const response = await fetch(`${API_BASE_URL}/notifications/?unread_only=false&limit=50`);
      if (response.ok) {
        const data = await response.json();
        setNotifications(data.notifications || []);
        setUnreadCount(data.total_unread || 0);
      }
    } catch (error) {
      console.error('Failed to fetch notifications:', error);
    } finally {
      setIsLoading(false);
    }
  }, []);

  const markAsRead = useCallback(async (notificationId: string) => {
    try {
      const response = await fetch(`${API_BASE_URL}/notifications/${notificationId}/read`, {
        method: 'POST',
      });
      if (response.ok) {
        // Update local state
        setNotifications(prev =>
          prev.map(n => n.id === notificationId ? { ...n, is_read: true } : n)
        );
        setUnreadCount(prev => Math.max(0, prev - 1));
      }
    } catch (error) {
      console.error('Failed to mark notification as read:', error);
    }
  }, []);

  const markAllAsRead = useCallback(async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/notifications/read-all`, {
        method: 'POST',
      });
      if (response.ok) {
        setNotifications(prev => prev.map(n => ({ ...n, is_read: true })));
        setUnreadCount(0);
      }
    } catch (error) {
      console.error('Failed to mark all as read:', error);
    }
  }, []);

  const deleteNotification = useCallback(async (notificationId: string) => {
    try {
      const response = await fetch(`${API_BASE_URL}/notifications/${notificationId}`, {
        method: 'DELETE',
      });
      if (response.ok) {
        setNotifications(prev => prev.filter(n => n.id !== notificationId));
      }
    } catch (error) {
      console.error('Failed to delete notification:', error);
    }
  }, []);

  // Initial fetch
  useEffect(() => {
    fetchNotifications();
  }, [fetchNotifications]);

  // Polling for updates
  useEffect(() => {
    const interval = setInterval(fetchNotifications, pollingInterval);
    return () => clearInterval(interval);
  }, [fetchNotifications, pollingInterval]);

  return {
    notifications,
    unreadCount,
    isLoading,
    fetchNotifications,
    markAsRead,
    markAllAsRead,
    deleteNotification,
  };
}

