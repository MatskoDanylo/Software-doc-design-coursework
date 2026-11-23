import { fireEvent, screen, waitFor } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'
import type { HlsStream } from '../player/useHlsStream'
import { callsTo, currentUrl, errorResponse, mockApi, renderApp, signedInAs, testUser } from '../test/utils'
import type { TitleDetail } from '../types/catalog'
import type { Playback, ProgressUpdate } from '../types/playback'

const stream: HlsStream = {
  heights: [720, 360],
  selectedHeight: null,
  activeHeight: 720,
  selectHeight: () => undefined,
  error: null,
  retry: () => undefined,
  blocked: false,
  play: () => undefined,
}

vi.mock('../player/useHlsStream', () => ({ useHlsStream: () => stream }))

const movie: TitleDetail = {
  id: 10,
  kind: 'movie',
  name: 'Тестовий фільм',
  description: '',
  year: 2015,
  country: 'Україна',
  rating: 8.1,
  poster_url: null,
  is_favorite: false,
  genres: [],
  seasons: [],
}

const series: TitleDetail = {
  ...movie,
  id: 20,
  kind: 'series',
  name: 'Тестовий серіал',
  seasons: [{ id: 1, number: 1, episodes: [{ id: 101, number: 1, name: 'Пілот' }, { id: 102, number: 2, name: 'Друга' }] }],
}

const freePlayback: Playback = {
  plan: 'free',
  manifest_url: '/api/playback/5/master.m3u8',
  ads: { enabled: true, preroll_url: '/media/ads/preroll/master.m3u8' },
  allowed_heights: [360, 720],
  resume_position_sec: 0,
}

const premiumPlayback: Playback = {
  ...freePlayback,
  plan: 'premium',
  ads: { enabled: false, preroll_url: null },
  allowed_heights: [360, 720, 1080],
}

function mockWatch(playback: Playback | Response, title: TitleDetail = movie) {
  return mockApi({
    ...signedInAs(testUser),
    [`/api/titles/${title.id}`]: title,
    [`/api/titles/${title.id}/playback`]: () => (playback instanceof Response ? playback : Response.json(playback)),
    'PUT /api/history/progress': () => new Response(null, { status: 200 }),
  })
}

function setTime(video: HTMLElement, seconds: number) {
  Object.defineProperty(video, 'currentTime', { value: seconds, configurable: true })
  fireEvent.timeUpdate(video)
}

describe('WatchPage', () => {
  it('shows a skippable pre-roll before the movie for the free plan', async () => {
    mockWatch(freePlayback)
    renderApp('/watch/10')

    const ad = await screen.findByRole('region', { name: 'Реклама' })
    expect(screen.queryByLabelText('Відеоплеєр')).not.toBeInTheDocument()
    expect(screen.getByText('План: Free')).toBeInTheDocument()
    expect(screen.getByRole('link', { name: 'Преміум: до 1080p без реклами' })).toHaveAttribute('href', '/pricing')

    const skip = screen.getByRole('button', { name: 'Пропустити через 5' })
    expect(skip).toBeDisabled()
    setTime(ad.querySelector('video')!, 5)
    fireEvent.click(screen.getByRole('button', { name: 'Пропустити ›' }))

    expect(await screen.findByLabelText('Відеоплеєр')).toBeInTheDocument()
    expect(screen.queryByRole('region', { name: 'Реклама' })).not.toBeInTheDocument()
  })

  it('starts the movie right away for the premium plan', async () => {
    mockWatch(premiumPlayback)
    renderApp('/watch/10')

    expect(await screen.findByLabelText('Відеоплеєр')).toBeInTheDocument()
    expect(screen.queryByRole('region', { name: 'Реклама' })).not.toBeInTheDocument()
    expect(screen.getByText('План: Premium')).toBeInTheDocument()
    expect(screen.queryByRole('link', { name: /Преміум/ })).not.toBeInTheDocument()
    expect(screen.getByLabelText('Якість')).toHaveDisplayValue('Авто (720p)')
  })

  it('reports progress on pause and marks the video finished on end', async () => {
    const fetchMock = mockWatch(premiumPlayback)
    renderApp('/watch/10')

    const video = await screen.findByLabelText('Відеоплеєр')
    setTime(video, 42.7)
    fireEvent.pause(video)
    setTime(video, 90)
    fireEvent.ended(video)

    await waitFor(() => expect(callsTo(fetchMock, 'PUT', '/api/history/progress')).toHaveLength(2))
    const bodies = callsTo(fetchMock, 'PUT', '/api/history/progress').map(
      ({ init }) => JSON.parse(String(init?.body)) as ProgressUpdate,
    )
    expect(bodies).toEqual([
      { title_id: 10, episode_id: null, progress_sec: 42, finished: false },
      { title_id: 10, episode_id: null, progress_sec: 90, finished: true },
    ])
  })

  it('opens the first episode of a series and links to the next one', async () => {
    mockWatch(premiumPlayback, series)
    renderApp('/watch/20')

    expect(await screen.findByText('С1 Е1 · Пілот')).toBeInTheDocument()
    expect(currentUrl().search).toBe('?episode=101')
    expect(screen.getByRole('link', { name: 'Епізод 1: Пілот' })).toHaveAttribute('aria-current', 'true')
    expect(await screen.findByRole('link', { name: /Наступний епізод: С1 Е2 · Друга/ })).toHaveAttribute(
      'href',
      '/watch/20?episode=102',
    )
  })

  it('explains when the video is not ready yet', async () => {
    mockWatch(errorResponse(404, 'video_not_ready'))
    renderApp('/watch/10')

    expect(await screen.findByText('Відео ще недоступне')).toBeInTheDocument()
    expect(screen.getByText('Відео для цього тайтлу ще не готове')).toBeInTheDocument()
  })

  it('sends guests to the login page and back to the player', async () => {
    mockApi({ '/api/titles/10': movie })
    renderApp('/watch/10')

    await waitFor(() => expect(currentUrl().pathname).toBe('/login'))
  })
})
