import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { notificationsApi, notificationsKeys } from '../api/notifications'
import type { NotificationInbox } from '../types/notification'

export const NOTIFICATIONS_POLL_MS = 30_000

export function useNotifications() {
  return useQuery({
    queryKey: notificationsKeys.inbox,
    queryFn: notificationsApi.inbox,
    refetchInterval: NOTIFICATIONS_POLL_MS,
  })
}

function markOne(inbox: NotificationInbox | undefined, id: number): NotificationInbox | undefined {
  const target = inbox?.items.find((item) => item.id === id)
  if (!inbox || !target || target.read) return inbox
  return {
    items: inbox.items.map((item) => (item.id === id ? { ...item, read: true } : item)),
    unread: Math.max(0, inbox.unread - 1),
  }
}

function markAll(inbox: NotificationInbox | undefined): NotificationInbox | undefined {
  return inbox && { items: inbox.items.map((item) => ({ ...item, read: true })), unread: 0 }
}

export function useMarkNotificationRead() {
  const client = useQueryClient()
  return useMutation({
    mutationFn: notificationsApi.markRead,
    onSuccess: ({ id }) => client.setQueryData(notificationsKeys.inbox, (inbox?: NotificationInbox) => markOne(inbox, id)),
    onSettled: () => client.invalidateQueries({ queryKey: notificationsKeys.inbox }),
    meta: { errorToast: true },
  })
}

export function useMarkAllNotificationsRead() {
  const client = useQueryClient()
  return useMutation({
    mutationFn: notificationsApi.markAllRead,
    onSuccess: () => client.setQueryData(notificationsKeys.inbox, markAll),
    onSettled: () => client.invalidateQueries({ queryKey: notificationsKeys.inbox }),
    meta: { errorToast: true },
  })
}
