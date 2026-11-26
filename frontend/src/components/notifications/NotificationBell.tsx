import { useCallback, useRef, useState } from 'react'
import { useDismiss } from '../../hooks/useDismiss'
import { useNotifications } from '../../notifications/queries'
import BellIcon from './BellIcon'
import NotificationPanel from './NotificationPanel'

const PANEL_ID = 'notifications-panel'
const MAX_BADGE = 9

export default function NotificationBell() {
  const [open, setOpen] = useState(false)
  const containerRef = useRef<HTMLDivElement>(null)
  const inbox = useNotifications()
  const close = useCallback(() => setOpen(false), [])
  useDismiss(containerRef, open, close)

  const unread = inbox.data?.unread ?? 0
  return (
    <div ref={containerRef} className="relative">
      <button
        type="button"
        aria-label={unread > 0 ? `Сповіщення: ${unread} непрочитаних` : 'Сповіщення'}
        aria-expanded={open}
        aria-controls={PANEL_ID}
        onClick={() => setOpen((value) => !value)}
        className="relative rounded-lg p-2 text-zinc-300 transition-colors hover:bg-surface-raised hover:text-zinc-100"
      >
        <BellIcon />
        {unread > 0 && (
          <span
            aria-hidden="true"
            className="absolute -top-0.5 -right-0.5 min-w-5 rounded-full bg-gold px-1 text-center text-[10px] leading-5 font-semibold text-screen"
          >
            {unread > MAX_BADGE ? `${MAX_BADGE}+` : unread}
          </span>
        )}
      </button>
      {open && <NotificationPanel id={PANEL_ID} inbox={inbox} />}
    </div>
  )
}
