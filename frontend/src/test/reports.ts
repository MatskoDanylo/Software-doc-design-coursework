import type { Dashboard, Report, ReportKind } from '../types/report'

const base = {
  date_from: '2026-10-27',
  date_to: '2026-11-25',
  group_by: 'day',
  timezone: 'Europe/Kyiv',
} as const

export const popularReport: Report = {
  ...base,
  kind: 'popular-titles',
  title: 'Популярні тайтли й жанри',
  summary: [{ key: 'total_views', label: 'Переглядів', value: 1234 }],
  sections: [
    {
      key: 'titles',
      title: 'Топ тайтлів',
      columns: [
        { key: 'rank', label: 'Місце' },
        { key: 'name', label: 'Назва' },
        { key: 'viewers', label: 'Глядачі' },
      ],
      rows: [
        { rank: 1, name: 'Дюна', viewers: 42 },
        { rank: 2, name: 'Матриця', viewers: 17 },
      ],
    },
    {
      key: 'genres',
      title: 'Популярні жанри',
      columns: [
        { key: 'genre', label: 'Жанр' },
        { key: 'viewers', label: 'Глядачі' },
      ],
      rows: [{ genre: 'Фантастика', viewers: 59 }],
    },
  ],
}

export const activityReport: Report = {
  ...base,
  kind: 'user-activity',
  title: 'Активність користувачів',
  summary: [{ key: 'new_users', label: 'Нових користувачів', value: 12 }],
  sections: [
    {
      key: 'activity',
      title: 'Активність за періодами',
      columns: [
        { key: 'bucket', label: 'Період' },
        { key: 'registrations', label: 'Реєстрації' },
        { key: 'active_users', label: 'Активні користувачі' },
      ],
      rows: [{ bucket: '2026-11-24', registrations: 3, active_users: 8 }],
    },
  ],
}

export const revenueReport: Report = {
  ...base,
  kind: 'subscription-revenue',
  title: 'Доходи від підписок',
  summary: [
    { key: 'total_revenue', label: 'Дохід, грн', value: 1990 },
    { key: 'paying_users', label: 'Платників', value: 10 },
    { key: 'conversion', label: 'Конверсія free → premium, %', value: 25 },
  ],
  sections: [
    {
      key: 'revenue',
      title: 'Дохід за періодами',
      columns: [
        { key: 'bucket', label: 'Період' },
        { key: 'revenue', label: 'Дохід, грн' },
      ],
      rows: [{ bucket: '2026-11-01', revenue: 1990 }],
    },
    {
      key: 'statuses',
      title: 'Платежі за статусами',
      columns: [
        { key: 'status', label: 'Статус' },
        { key: 'count', label: 'Кількість' },
      ],
      rows: [
        { status: 'success', count: 10 },
        { status: 'failed', count: 2 },
      ],
    },
  ],
}

export const dashboard: Dashboard = {
  total_users: 41,
  active_users_7d: 23,
  active_premium: 13,
  revenue_30d: 2587,
  titles_with_video: 4,
}

const REPORTS: Record<ReportKind, Report> = {
  'popular-titles': popularReport,
  'user-activity': activityReport,
  'subscription-revenue': revenueReport,
}

export function reportRoutes(): Record<string, unknown> {
  return Object.fromEntries(
    Object.entries(REPORTS).map(([kind, report]) => [
      `/api/admin/reports/${kind}`,
      (url: URL) =>
        url.searchParams.get('format') === 'csv'
          ? new Response('a;b\n1;2\n', {
              headers: { 'Content-Type': 'text/csv', 'Content-Disposition': `attachment; filename="${kind}.csv"` },
            })
          : Response.json(report),
    ]),
  )
}
