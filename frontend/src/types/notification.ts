export type NotificationKind = 'payment_pending' | 'payment_failed' | 'subscription_activated'

export interface AppNotification {
  id: number
  kind: NotificationKind
  message: string
  read: boolean
  created_at: string
}

export interface NotificationInbox {
  items: AppNotification[]
  unread: number
}
