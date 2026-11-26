import { fireEvent, screen, waitFor, within } from '@testing-library/react'
import { afterEach, beforeAll, beforeEach, describe, expect, it, vi } from 'vitest'
import { formatMoney } from '../../reports/format'
import { dashboard, reportRoutes } from '../../test/reports'
import { callsTo, currentUrl, errorResponse, mockApi, renderApp, signedInAs, testAdmin } from '../../test/utils'

beforeAll(() => Promise.all([import('./AdminReportsPage'), import('../AdminPage')]))

function openReports(path = '/admin/reports', routes: Record<string, unknown> = {}) {
  const fetchMock = mockApi({ ...signedInAs(testAdmin), ...reportRoutes(), ...routes })
  renderApp(path)
  return fetchMock
}

function lastQuery(fetchMock: ReturnType<typeof mockApi>, kind: string) {
  const calls = callsTo(fetchMock, 'GET', `/api/admin/reports/${kind}`)
  return Object.fromEntries(calls.at(-1)?.url.searchParams ?? [])
}

describe('AdminReportsPage', () => {
  beforeEach(() => {
    vi.useFakeTimers({ toFake: ['Date'], now: new Date(2026, 10, 25, 12) })
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  it('loads the last 30 days by default and renders tables under charts', async () => {
    const fetchMock = openReports()

    const titles = await screen.findByRole('region', { name: 'Топ тайтлів' })
    expect(within(titles).getByRole('table')).toHaveTextContent('Дюна42')
    expect(screen.getByRole('tab', { name: 'Популярне' })).toHaveAttribute('aria-selected', 'true')
    expect(screen.getByRole('button', { name: '30 днів' })).toHaveAttribute('aria-pressed', 'true')
    expect(lastQuery(fetchMock, 'popular-titles')).toEqual({
      date_from: '2026-10-27',
      date_to: '2026-11-25',
      group_by: 'day',
      format: 'json',
    })
  })

  it('keeps the period and grouping in the URL across tabs', async () => {
    const fetchMock = openReports()
    await screen.findByRole('region', { name: 'Топ тайтлів' })

    fireEvent.click(screen.getByRole('button', { name: '7 днів' }))
    await waitFor(() => expect(currentUrl().search).toBe('?days=7'))
    await waitFor(() => expect(lastQuery(fetchMock, 'popular-titles').date_from).toBe('2026-11-19'))

    fireEvent.click(screen.getByRole('tab', { name: 'Доходи' }))
    expect(await screen.findByRole('region', { name: 'Платежі за статусами' })).toHaveTextContent('Відхилено2')
    expect(currentUrl().searchParams.get('days')).toBe('7')

    fireEvent.change(screen.getByLabelText('Групування'), { target: { value: 'month' } })
    await waitFor(() => expect(currentUrl().search).toBe('?tab=revenue&days=7&group=month'))
    await waitFor(() =>
      expect(lastQuery(fetchMock, 'subscription-revenue')).toMatchObject({ date_from: '2026-11-19', group_by: 'month' }),
    )
  })

  it('reads a custom period from the URL and validates a new one before applying it', async () => {
    const fetchMock = openReports('/admin/reports?tab=activity&from=2026-09-01&to=2026-09-30')

    await screen.findByRole('region', { name: 'Активність за періодами' })
    expect(lastQuery(fetchMock, 'user-activity')).toMatchObject({ date_from: '2026-09-01', date_to: '2026-09-30' })
    expect(screen.getByRole('button', { name: 'Довільний' })).toHaveAttribute('aria-pressed', 'true')

    fireEvent.change(screen.getByLabelText('Від'), { target: { value: '2026-10-15' } })
    fireEvent.change(screen.getByLabelText('До'), { target: { value: '2026-10-01' } })
    fireEvent.click(screen.getByRole('button', { name: 'Застосувати' }))
    expect(screen.getByText('Початок періоду не може бути пізніше за кінець')).toBeInTheDocument()
    expect(currentUrl().searchParams.get('from')).toBe('2026-09-01')

    fireEvent.change(screen.getByLabelText('До'), { target: { value: '2026-10-31' } })
    fireEvent.click(screen.getByRole('button', { name: 'Застосувати' }))
    await waitFor(() => expect(currentUrl().search).toBe('?tab=activity&from=2026-10-15&to=2026-10-31'))
  })

  it('falls back to the default period when the URL is invalid', async () => {
    const fetchMock = openReports('/admin/reports?tab=unknown&from=2026-13-01&to=2026-01-01&days=5')

    await screen.findByRole('region', { name: 'Топ тайтлів' })
    expect(lastQuery(fetchMock, 'popular-titles')).toMatchObject({ date_from: '2026-10-27', date_to: '2026-11-25' })
  })

  it('shows backend validation errors', async () => {
    openReports('/admin/reports?tab=activity', {
      '/api/admin/reports/user-activity': () => errorResponse(422, 'period_too_long'),
    })

    expect(await screen.findByText(/Період задовгий/)).toBeInTheDocument()
  })

  it('downloads the current report as CSV', async () => {
    const createUrl = vi.spyOn(URL, 'createObjectURL').mockReturnValue('blob:report')
    const fetchMock = openReports('/admin/reports?tab=revenue&days=90')
    await screen.findByRole('region', { name: 'Дохід за періодами' })

    fireEvent.click(screen.getByRole('button', { name: 'Експорт CSV' }))

    await waitFor(() => expect(createUrl).toHaveBeenCalledOnce())
    expect(lastQuery(fetchMock, 'subscription-revenue')).toMatchObject({ format: 'csv', date_from: '2026-08-28' })
    const [blob] = createUrl.mock.calls[0]
    expect(blob).toBeInstanceOf(Blob)
  })
})

describe('Admin dashboard', () => {
  it('shows KPI cards and links trend charts to the reports', async () => {
    mockApi({ ...signedInAs(testAdmin), ...reportRoutes(), '/api/admin/dashboard': dashboard })
    renderApp('/admin')

    const grid = await screen.findByLabelText('Ключові показники')
    await waitFor(() => expect(grid).toHaveTextContent('Користувачів41'))
    expect(within(grid).getByText(formatMoney(2587), { normalizer: (text) => text })).toBeInTheDocument()

    const links = await screen.findAllByRole('link', { name: 'Детальніше →' })
    expect(links.map((link) => link.getAttribute('href'))).toEqual([
      '/admin/reports?tab=activity',
      '/admin/reports?tab=revenue',
    ])
  })
})
