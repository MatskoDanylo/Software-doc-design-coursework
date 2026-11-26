import { fireEvent, screen, within } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import { feedByStrategy, popularFeed, recommendation } from '../../test/recommendations'
import { callsTo, errorResponse, mockApi, renderApp, signedInAs, testUser } from '../../test/utils'

const signedIn = () => ({ ...signedInAs(testUser), '/api/history': [] })

describe('Home recommendation rows', () => {
  it('shows recommended cards with their reason and the strategy used', async () => {
    mockApi({ ...signedIn(), '/api/recommendations': feedByStrategy })
    renderApp('/')

    const row = await screen.findByRole('region', { name: 'Рекомендовано для вас' })
    const link = await within(row).findByRole('link', { name: /Дюна/ })
    expect(link).toHaveAttribute('href', '/titles/11')
    expect(link.closest('article')).toHaveTextContent('Бо ви дивились жанр «Фантастика»')
    expect(within(row).getByText('Схоже на «Матриця»')).toBeInTheDocument()
    expect(within(row).getByText('Алгоритм: Гібридна')).toBeInTheDocument()

    const popular = screen.getByRole('region', { name: 'Популярне' })
    expect(await within(popular).findByRole('heading', { name: 'Тіні забутих предків' })).toBeInTheDocument()
    expect(within(popular).queryByText('Популярне цього тижня')).not.toBeInTheDocument()
  })

  it('explains how to get a personal feed when it falls back to popularity', async () => {
    mockApi({ ...signedIn(), '/api/recommendations': popularFeed })
    renderApp('/')

    const row = await screen.findByRole('region', { name: 'Рекомендовано для вас' })
    expect(await within(row).findByText(/^Алгоритм: Популярне\. Якщо ви ще нічого не дивились/)).toBeInTheDocument()
  })

  it('shows only popular titles and a sign-in call to guests', async () => {
    const fetchMock = mockApi({ '/api/recommendations': feedByStrategy })
    renderApp('/')

    const popular = await screen.findByRole('region', { name: 'Популярне' })
    expect(await within(popular).findByRole('heading', { name: 'Тіні забутих предків' })).toBeInTheDocument()
    expect(screen.getByRole('link', { name: 'Увійти' })).toHaveAttribute('href', '/login')
    expect(screen.queryByRole('region', { name: 'Рекомендовано для вас' })).not.toBeInTheDocument()

    const strategies = callsTo(fetchMock, 'GET', '/api/recommendations').map(({ url }) => url.searchParams.get('strategy'))
    expect(strategies).toEqual(['popularity'])
  })

  it('shows skeletons, then an error with retry, then the empty state', async () => {
    const responses = [errorResponse(422, 'unknown_strategy'), Response.json({ strategy: 'hybrid', items: [] })]
    mockApi({
      ...signedIn(),
      '/api/recommendations': (url: URL) =>
        url.searchParams.get('strategy') ? Response.json(popularFeed) : (responses.shift() ?? errorResponse(500, 'x')),
    })
    renderApp('/')

    const row = await screen.findByRole('region', { name: 'Рекомендовано для вас' })
    expect(within(row).getByRole('status')).toHaveTextContent('Завантаження…')

    const alert = await within(row).findByRole('alert')
    fireEvent.click(within(alert).getByRole('button', { name: 'Спробувати ще раз' }))

    expect(await within(row).findByText(/Ви вже переглянули все/)).toBeInTheDocument()
  })

  it('lists similar titles on the title page', async () => {
    const title = { ...recommendation(5, 'Матриця', ''), seasons: [] }
    mockApi({
      '/api/titles/5': title,
      '/api/titles/5/similar': [recommendation(6, 'Початок', 'Схоже на «Матриця»')],
    })
    renderApp('/titles/5')

    const similar = await screen.findByRole('region', { name: 'Схожі' })
    expect(await within(similar).findByRole('link', { name: /Початок/ })).toHaveAttribute('href', '/titles/6')
  })
})
