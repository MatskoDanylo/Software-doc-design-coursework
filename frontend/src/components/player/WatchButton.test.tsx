import { screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import { errorResponse, mockApi, renderApp, signedInAs, testUser } from '../../test/utils'
import type { TitleDetail } from '../../types/catalog'
import type { Playback } from '../../types/playback'

const movie: TitleDetail = {
  id: 10,
  kind: 'movie',
  name: 'Тестовий фільм',
  description: '',
  year: 2015,
  country: 'Україна',
  rating: 8.1,
  poster_url: null,
  genres: [],
  seasons: [],
}

const playback: Playback = {
  plan: 'free',
  manifest_url: '/api/playback/5/master.m3u8',
  ads: { enabled: false, preroll_url: null },
  allowed_heights: [360, 720],
  resume_position_sec: 0,
}

describe('WatchButton on the title page', () => {
  it('asks guests to sign in before watching', async () => {
    mockApi({ '/api/titles/10': movie })
    renderApp('/titles/10')

    expect(await screen.findByRole('link', { name: '▶ Увійти, щоб дивитись' })).toHaveAttribute('href', '/watch/10')
  })

  it('links to the player when the video is ready', async () => {
    mockApi({ ...signedInAs(testUser), '/api/titles/10': movie, '/api/titles/10/playback': playback })
    renderApp('/titles/10')

    expect(await screen.findByRole('link', { name: '▶ Дивитись' })).toHaveAttribute('href', '/watch/10')
  })

  it('stays disabled while the video is not uploaded', async () => {
    mockApi({
      ...signedInAs(testUser),
      '/api/titles/10': movie,
      '/api/titles/10/playback': () => errorResponse(404, 'video_not_ready'),
    })
    renderApp('/titles/10')

    expect(await screen.findByText('Відео ще не завантажено')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: '▶ Дивитись' })).toBeDisabled()
  })
})
