import type { Role, User } from '../types/user'
import Avatar from './Avatar'
import { card } from './ui'

const roleLabels: Record<Role, string> = {
  user: 'Користувач',
  admin: 'Адміністратор',
}

const dateFormat = new Intl.DateTimeFormat('uk-UA', { dateStyle: 'long' })

export default function ProfileSummary({ user }: { user: User }) {
  return (
    <aside className={`${card} flex flex-col items-center text-center`}>
      <Avatar name={user.profile.display_name} url={user.profile.avatar_url} size="lg" />
      <h1 className="mt-4 font-display text-xl font-semibold break-all">{user.profile.display_name}</h1>
      <p className="mt-1 text-sm break-all text-muted">{user.email}</p>
      <span className="mt-4 rounded-full border border-gold/40 bg-gold/10 px-3 py-1 text-xs font-medium text-gold">
        {roleLabels[user.role]}
      </span>
      <dl className="mt-6 w-full space-y-2 border-t border-line pt-4 text-left text-sm">
        <div className="flex justify-between gap-4">
          <dt className="text-muted">Країна</dt>
          <dd className="truncate">{user.profile.country || '—'}</dd>
        </div>
        <div className="flex justify-between gap-4">
          <dt className="text-muted">З нами від</dt>
          <dd>{dateFormat.format(new Date(user.created_at))}</dd>
        </div>
      </dl>
    </aside>
  )
}
