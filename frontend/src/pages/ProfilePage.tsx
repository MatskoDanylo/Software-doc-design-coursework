import { useAuth } from '../auth/useAuth'
import ContinueWatchingRow from '../components/history/ContinueWatchingRow'
import ProfileForm from '../components/ProfileForm'
import ProfileSummary from '../components/ProfileSummary'

export default function ProfilePage() {
  const { user, updateUser } = useAuth()
  if (!user) return null

  return (
    <div className="space-y-10">
      <div className="grid gap-6 lg:grid-cols-[18rem_1fr]">
        <ProfileSummary user={user} />
        <ProfileForm user={user} onSaved={updateUser} />
      </div>
      <ContinueWatchingRow />
    </div>
  )
}
