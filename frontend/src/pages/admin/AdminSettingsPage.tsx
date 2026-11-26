import { useAppSettings } from '../../admin/settings'
import { errorMessage } from '../../api/errors'
import SettingsForm from '../../components/admin/settings/SettingsForm'
import PageLoader from '../../components/PageLoader'
import StateMessage from '../../components/StateMessage'
import { formatDateTime } from '../../format/datetime'
import { useDocumentTitle } from '../../hooks/useDocumentTitle'

export default function AdminSettingsPage() {
  useDocumentTitle('Налаштування — Адмінка')
  const query = useAppSettings()

  return (
    <section className="space-y-6">
      <div>
        <h1 className="font-display text-3xl font-semibold">Налаштування</h1>
        <p className="mt-1 text-sm text-muted">
          {query.data?.updated_at
            ? `Востаннє змінено ${formatDateTime(query.data.updated_at)}`
            : 'Діють значення за замовчуванням'}
        </p>
      </div>
      {query.isPending && <PageLoader />}
      {query.isError && <StateMessage tone="error" title="Не вдалося завантажити налаштування" text={errorMessage(query.error)} />}
      {query.data && <SettingsForm settings={query.data} />}
    </section>
  )
}
