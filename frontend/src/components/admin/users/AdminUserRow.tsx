import { formatDate } from '../../../format/datetime'
import type { Account } from '../../../types/user'
import PremiumControls from './PremiumControls'

const ROLE_LABELS = { user: 'Користувач', admin: 'Адміністратор' } as const

export default function AdminUserRow({ user }: { user: Account }) {
  return (
    <tr className="align-middle">
      <td className="py-2 pr-3">
        <p className="max-w-56 truncate font-medium text-zinc-100">{user.email}</p>
        <p className="max-w-56 truncate text-xs text-muted">{user.profile.display_name}</p>
      </td>
      <td className="py-2 pr-3 text-muted">{ROLE_LABELS[user.role]}</td>
      <td className="py-2 pr-3 whitespace-nowrap text-muted">{formatDate(user.created_at)}</td>
      <td className="py-2">
        <PremiumControls user={user} />
      </td>
    </tr>
  )
}
