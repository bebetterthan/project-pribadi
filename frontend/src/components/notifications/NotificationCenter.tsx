/**
 * Notification Center - Bell icon with dropdown panel
 * FASE 6: Frontend UI Excellence
 */
'use client';

import { useState, useRef, useEffect } from 'react';
import { useNotifications } from '@/hooks/useNotifications';
import { Bell, Check, CheckCheck, X, Clock, AlertCircle } from 'lucide-react';
import { Badge } from '@/components/ui/Badge';
import { Button } from '@/components/ui/Button';
import { Card } from '@/components/ui/Card';
import { formatDistance } from 'date-fns';

export function NotificationCenter() {
  const [isOpen, setIsOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);
  const {
    notifications,
    unreadCount,
    isLoading,
    markAsRead,
    markAllAsRead,
    deleteNotification,
  } = useNotifications();

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };

    if (isOpen) {
      document.addEventListener('mousedown', handleClickOutside);
      return () => document.removeEventListener('mousedown', handleClickOutside);
    }
  }, [isOpen]);

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'urgent':
        return 'text-red-600 bg-red-50';
      case 'high':
        return 'text-orange-600 bg-orange-50';
      case 'normal':
        return 'text-blue-600 bg-blue-50';
      default:
        return 'text-gray-600 bg-gray-50';
    }
  };

  const getTypeIcon = (type: string) => {
    if (type.includes('critical')) return '🔴';
    if (type.includes('completed')) return '✅';
    if (type.includes('failed')) return '❌';
    if (type.includes('assigned')) return '👤';
    if (type.includes('comment')) return '💬';
    if (type.includes('status')) return '🔄';
    return '🔔';
  };

  const recentNotifications = notifications.slice(0, 5);
  const hasUnread = unreadCount > 0;

  return (
    <div className="relative" ref={dropdownRef}>
      {/* Bell Icon Button */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="relative p-2 rounded-lg hover:bg-gray-800 transition-colors"
        aria-label="Notifications"
      >
        <Bell className={`w-5 h-5 ${hasUnread ? 'text-blue-400' : 'text-gray-400'}`} />
        {unreadCount > 0 && (
          <span className="absolute top-0 right-0 flex items-center justify-center w-5 h-5 text-xs font-bold text-white bg-red-500 rounded-full animate-pulse">
            {unreadCount > 9 ? '9+' : unreadCount}
          </span>
        )}
      </button>

      {/* Dropdown Panel */}
      {isOpen && (
        <div className="absolute right-0 mt-2 w-96 bg-[#1f1f1f] rounded-lg shadow-2xl border border-gray-800 z-50 max-h-[600px] overflow-hidden flex flex-col">
          {/* Header */}
          <div className="flex items-center justify-between px-4 py-3 border-b border-gray-800 bg-[#171717]">
            <div>
              <h3 className="font-semibold text-white">Notifications</h3>
              {unreadCount > 0 && (
                <p className="text-xs text-gray-400">{unreadCount} unread</p>
              )}
            </div>
            <div className="flex items-center gap-2">
              {unreadCount > 0 && (
                <button
                  onClick={markAllAsRead}
                  className="text-xs px-3 py-1.5 rounded-lg hover:bg-gray-800 text-blue-400 transition-colors flex items-center gap-1"
                >
                  <CheckCheck className="w-4 h-4" />
                  Mark all read
                </button>
              )}
            </div>
          </div>

          {/* Notifications List */}
          <div className="overflow-y-auto flex-1">
            {isLoading ? (
              <div className="flex items-center justify-center py-8">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
              </div>
            ) : notifications.length === 0 ? (
              <div className="flex flex-col items-center justify-center py-12 text-gray-500">
                <Bell className="w-12 h-12 mb-2 opacity-20" />
                <p className="text-sm">No notifications yet</p>
              </div>
            ) : (
              <div className="divide-y divide-gray-800">
                {recentNotifications.map((notification) => (
                  <div
                    key={notification.id}
                    className={`px-4 py-3 hover:bg-[#252525] transition-colors ${
                      !notification.is_read ? 'bg-[#1a2332]' : ''
                    }`}
                  >
                    <div className="flex items-start gap-3">
                      {/* Icon */}
                      <div className="flex-shrink-0 text-2xl">
                        {getTypeIcon(notification.type)}
                      </div>

                      {/* Content */}
                      <div className="flex-1 min-w-0">
                        <div className="flex items-start justify-between gap-2 mb-1">
                          <h4 className="font-medium text-sm text-white truncate">
                            {notification.title}
                          </h4>
                          {!notification.is_read && (
                            <button
                              onClick={() => markAsRead(notification.id)}
                              className="flex-shrink-0 text-blue-400 hover:text-blue-300"
                              aria-label="Mark as read"
                            >
                              <Check className="w-4 h-4" />
                            </button>
                          )}
                        </div>

                        <p className="text-sm text-gray-400 line-clamp-2 mb-2">
                          {notification.message}
                        </p>

                        <div className="flex items-center gap-2 text-xs text-gray-500">
                          <Clock className="w-3 h-3" />
                          <span>
                            {formatDistance(new Date(notification.created_at), new Date(), {
                              addSuffix: true,
                            })}
                          </span>
                          {notification.priority !== 'normal' && (
                            <Badge className={getPriorityColor(notification.priority)}>
                              {notification.priority}
                            </Badge>
                          )}
                        </div>
                      </div>

                      {/* Delete Button */}
                      <button
                        onClick={() => deleteNotification(notification.id)}
                        className="flex-shrink-0 text-gray-600 hover:text-red-400 transition-colors"
                        aria-label="Delete notification"
                      >
                        <X className="w-4 h-4" />
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Footer */}
          {notifications.length > 5 && (
            <div className="px-4 py-3 border-t border-gray-800 bg-[#171717]">
              <button
                onClick={() => {
                  setIsOpen(false);
                  // Navigate to notifications page (implement routing)
                }}
                className="w-full text-center text-sm text-blue-400 hover:text-blue-300 font-medium"
              >
                View all notifications ({notifications.length})
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

