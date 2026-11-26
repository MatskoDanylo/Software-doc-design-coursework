import { useAuth } from '../auth/useAuth'
import ContinueWatchingRow from '../components/history/ContinueWatchingRow'
import PaymentHistory from '../components/profile/PaymentHistory'
import SubscriptionPanel from '../components/profile/SubscriptionPanel'
import ProfileForm from '../components/ProfileForm'
import ProfileSummary from '../components/ProfileSummary'
import { useDocumentTitle } from '../hooks/useDocumentTitle'

export default function ProfilePage() {
  useDocumentTitle('Профіль')
  const { user, updateUser } = useAuth()
  if (!user) return null

  return (
    <div className="space-y-10">
      <div className="grid gap-6 lg:grid-cols-[18rem_1fr]">
        <ProfileSummary user={user} />
        <ProfileForm user={user} onSaved={updateUser} />
      </div>
      <div className="grid gap-6 lg:grid-cols-[18rem_1fr]">
        <SubscriptionPanel subscription={user.subscription} />
        <PaymentHistory />
      </div>
      <ContinueWatchingRow />
    </div>
  )
}
