import AdminSections from '../components/admin/dashboard/AdminSections'
import DashboardTrends from '../components/admin/dashboard/DashboardTrends'
import KpiGrid from '../components/admin/dashboard/KpiGrid'
import { useDocumentTitle } from '../hooks/useDocumentTitle'

export default function AdminPage() {
  useDocumentTitle('Адмінка')
  return (
    <div className="space-y-8">
      <h1 className="font-display text-3xl font-semibold">Адмін-панель</h1>
      <KpiGrid />
      <DashboardTrends />
      <AdminSections />
    </div>
  )
}
