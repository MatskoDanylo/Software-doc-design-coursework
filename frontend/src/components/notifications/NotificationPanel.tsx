import type { UseQueryResult } from '@tanstack/react-query'
import { errorMessage } from '../../api/errors'
import { useMarkAllNotificationsRead, useMarkNotificationRead } from '../../notifications/queries'
import type { NotificationInbox } from '../../types/notification'
import NotificationItem from './NotificationItem'

interface NotificationPanelProps {
  id: string
  inbox: UseQueryResult<NotificationInbox>
}

function PanelBody({ inbox }: { inbox: UseQueryResult<NotificationInbox> }) {
  const markRead = useMarkNotificationRead()

  if (inbox.isPending) return <p className="px-4 py-6 text-center text-sm text-muted">Завантаження…</p>
  if (inbox.isError) return <p className="px-4 py-6 text-center text-sm text-danger">{errorMessage(inbox.error)}</p>
  if (inbox.data.items.length === 0) {
    return <p className="px-4 py-6 text-center text-sm text-muted">Сповіщень поки немає</p>
  }
  return (
    <ul className="max-h-96 divide-y divide-line overflow-y-auto">
      {inbox.data.items.map((notification) => (
        <NotificationItem key={notification.id} notification={notification} onRead={(id) => markRead.mutate(id)} />
      ))}
    </ul>
  )
}

export default function NotificationPanel({ id, inbox }: NotificationPanelProps) {
  const markAll = useMarkAllNotificationsRead()
  const unread = inbox.data?.unread ?? 0

  return (
    <div
      id={id}
      role="region"
      aria-label="Сповіщення"
      className="fixed inset-x-4 top-16 z-20 overflow-hidden rounded-xl border border-line bg-surface shadow-xl sm:absolute sm:inset-x-auto sm:top-auto sm:right-0 sm:mt-2 sm:w-80"
    >
      <div className="flex items-center justify-between gap-3 border-b border-line px-4 py-3">
        <h2 className="text-sm font-semibold">Сповіщення</h2>
        <button
          type="button"
          disabled={unread === 0 || markAll.isPending}
          onClick={() => markAll.mutate()}
          className="text-xs font-medium text-gold hover:text-gold-strong disabled:cursor-not-allowed disabled:text-muted"
        >
          Позначити все як прочитане
        </button>
      </div>
      <PanelBody inbox={inbox} />
    </div>
  )
}
