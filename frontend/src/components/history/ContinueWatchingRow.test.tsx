import { screen, waitFor, within } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import { callsTo, mockApi, renderApp, signedInAs, testUser } from '../../test/utils'
import type { Title } from '../../types/catalog'
import type { HistoryEntry } from '../../types/history'

const series: Title = {
  id: 20,
  kind: 'series',
  name: 'Тестовий серіал',
  description: '',
  year: 2020,
  country: 'Україна',
  rating: 8.0,
  poster_url: null,
  is_favorite: false,
  genres: [],
}

const entries: HistoryEntry[] = [
  {
    title: series,
    episode: { id: 102, number: 2, name: 'Друга', season_number: 1 },
    progress_sec: 675,
    duration_sec: 2700,
    finished: false,
    last_watched: '2026-11-23T12:00:00Z',
  },
  {
    title: { ...series, id: 10, kind: 'movie', name: 'Тестовий фільм' },
    episode: null,
    progress_sec: 3725,
    duration_sec: null,
    finished: false,
    last_watched: '2026-11-23T11:00:00Z',
  },
]

describe('Continue watching', () => {
  it('shows progress cards that resume playback', async () => {
    mockApi({ ...signedInAs(testUser), '/api/history': entries })
    renderApp('/')

    const row = await screen.findByRole('region', { name: 'Продовжити перегляд' })
    const [episodeCard, movieCard] = within(row).getAllByRole('link')

    expect(episodeCard).toHaveAttribute('href', '/watch/20?episode=102')
    expect(within(episodeCard).getByRole('progressbar', { name: 'Переглянуто' })).toHaveAttribute('aria-valuenow', '25')
    expect(within(episodeCard).getByText('С1 Е2 · Друга')).toBeInTheDocument()
    expect(within(episodeCard).getByText('Зупинились на 11:15 з 45:00')).toBeInTheDocument()

    expect(movieCard).toHaveAttribute('href', '/watch/10')
    expect(within(movieCard).queryByRole('progressbar')).not.toBeInTheDocument()
    expect(within(movieCard).getByText('Зупинились на 1:02:05')).toBeInTheDocument()
  })

  it('appears in the profile too', async () => {
    mockApi({ ...signedInAs(testUser), '/api/history': entries })
    renderApp('/profile')

    expect(await screen.findByRole('region', { name: 'Продовжити перегляд' })).toBeInTheDocument()
  })

  it('is hidden for guests', async () => {
    const guest = mockApi({})
    renderApp('/')
    expect(await screen.findByRole('heading', { name: 'Онлайн-кінотеатр' })).toBeInTheDocument()
    expect(callsTo(guest, 'GET', '/api/history')).toHaveLength(0)
  })

  it('is hidden when nothing is in progress', async () => {
    const fetchMock = mockApi({ ...signedInAs(testUser), '/api/history': [] })
    renderApp('/')

    await waitFor(() => expect(callsTo(fetchMock, 'GET', '/api/history')).toHaveLength(1))
    expect(screen.queryByRole('region', { name: 'Продовжити перегляд' })).not.toBeInTheDocument()
  })
})
