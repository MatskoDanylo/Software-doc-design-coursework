import { formatDateTime } from '../../notifications/format'
import type { AppNotification } from '../../types/notification'

interface NotificationItemProps {
  notification: AppNotification
  onRead: (id: number) => void
}

export default function NotificationItem({ notification, onRead }: NotificationItemProps) {
  const content = (
    <>
      <span
        aria-hidden="true"
        className={`mt-1.5 size-2 shrink-0 rounded-full ${notification.read ? 'bg-transparent' : 'bg-gold'}`}
      />
      <span className="min-w-0">
        <span className={`block text-sm ${notification.read ? 'text-muted' : 'text-zinc-100'}`}>{notification.message}</span>
        <time dateTime={notification.created_at} className="mt-0.5 block text-xs text-muted">
          {formatDateTime(notification.created_at)}
        </time>
      </span>
    </>
  )

  if (notification.read) return <li className="flex gap-3 px-4 py-3">{content}</li>
  return (
    <li>
      <button
        type="button"
        onClick={() => onRead(notification.id)}
        aria-label={`${notification.message} — позначити як прочитане`}
        className="flex w-full gap-3 px-4 py-3 text-left hover:bg-surface-raised"
      >
        {content}
      </button>
    </li>
  )
}
