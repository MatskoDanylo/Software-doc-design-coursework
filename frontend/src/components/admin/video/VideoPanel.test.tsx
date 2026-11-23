import { fireEvent, screen, waitFor, within } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import { callsTo, errorResponse, mockApi, renderApp, signedInAs, testAdmin } from '../../../test/utils'
import type { VideoAsset } from '../../../types/adminVideo'
import type { TitleDetail } from '../../../types/catalog'

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
  seasons: [{ id: 1, number: 1, episodes: [{ id: 101, number: 1, name: 'Пілот' }] }],
}

const asset = (status: VideoAsset['status'], extra: Partial<VideoAsset> = {}): VideoAsset => ({
  id: 5,
  title_id: 10,
  episode_id: null,
  status,
  error_message: null,
  hls_path: status === 'ready' ? 'hls/5/master.m3u8' : null,
  duration_sec: status === 'ready' ? 40 : null,
  ...extra,
})

const referenceRoutes = { '/api/genres': [], '/api/countries': ['Україна'] }

function chooseFile(name: string) {
  const file = new File(['video'], name, { type: 'video/mp4' })
  fireEvent.change(screen.getByLabelText('Файл відео'), { target: { files: [file] } })
}

async function openMovie(routes: Record<string, unknown>) {
  const fetchMock = mockApi({ ...signedInAs(testAdmin), ...referenceRoutes, '/api/titles/10': movie, ...routes })
  renderApp('/admin/titles/10')
  await screen.findByRole('heading', { name: 'Відео' })
  return fetchMock
}

describe('Admin video upload', () => {
  it('uploads a movie video and polls the status until it is ready', async () => {
    let current: VideoAsset | null = null
    const fetchMock = await openMovie({
      'GET /api/admin/titles/10/video': () =>
        current ? Response.json(current) : errorResponse(404, 'video_asset_not_found'),
      'POST /api/admin/titles/10/video': () => {
        current = asset('ready')
        return Response.json(asset('pending'), { status: 202 })
      },
    })

    expect(await screen.findByText('Відео не завантажено')).toBeInTheDocument()
    chooseFile('movie.mp4')
    expect(screen.getByText('Обрано: movie.mp4')).toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: 'Завантажити' }))

    expect(await screen.findByText('Очікує обробки')).toBeInTheDocument()
    expect(screen.getByText(/Конвертація виконується у фоні/)).toBeInTheDocument()
    expect(screen.getByLabelText('Файл відео')).toBeDisabled()

    expect(await screen.findByText('Готово · 0:40', {}, { timeout: 4000 })).toBeInTheDocument()
    const [upload] = callsTo(fetchMock, 'POST', '/api/admin/titles/10/video')
    expect(upload.init?.body).toBeInstanceOf(FormData)
  })

  it('shows the ffmpeg error of a failed conversion', async () => {
    await openMovie({ '/api/admin/titles/10/video': asset('failed', { error_message: 'ffmpeg exited with code 1' }) })

    expect(await screen.findByText('Помилка обробки')).toBeInTheDocument()
    expect(screen.getByText('ffmpeg exited with code 1')).toBeInTheDocument()
    expect(screen.getByText('Обрати нове відео')).toBeInTheDocument()
  })

  it('rejects unsupported files before uploading', async () => {
    const fetchMock = await openMovie({ '/api/admin/titles/10/video': () => errorResponse(404, 'video_asset_not_found') })

    await screen.findByText('Відео не завантажено')
    chooseFile('movie.avi')

    expect(screen.getByText('Оберіть файл MP4, MKV або MOV')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Завантажити' })).toBeDisabled()
    expect(callsTo(fetchMock, 'POST', '/api/admin/titles/10/video')).toHaveLength(0)
  })

  it('explains server-side upload errors', async () => {
    await openMovie({
      'GET /api/admin/titles/10/video': () => errorResponse(404, 'video_asset_not_found'),
      'POST /api/admin/titles/10/video': () => errorResponse(413, 'payload_too_large'),
    })

    await screen.findByText('Відео не завантажено')
    chooseFile('movie.mp4')
    fireEvent.click(screen.getByRole('button', { name: 'Завантажити' }))

    expect(await screen.findByRole('alert')).toHaveTextContent('Файл завеликий')
  })

  it('shows episode video status inline and uploads per episode', async () => {
    const fetchMock = mockApi({
      ...signedInAs(testAdmin),
      ...referenceRoutes,
      '/api/titles/20': series,
      'GET /api/admin/episodes/101/video': () => errorResponse(404, 'video_asset_not_found'),
      'POST /api/admin/episodes/101/video': () =>
        Response.json(asset('processing', { title_id: null, episode_id: 101 }), { status: 202 }),
    })
    renderApp('/admin/titles/20')

    const row = (await screen.findByText('Пілот')).closest('li')!
    expect(await within(row).findByText('Відео не завантажено')).toBeInTheDocument()
    fireEvent.click(within(row).getByRole('button', { name: 'Відео' }))
    chooseFile('ep1.mkv')
    fireEvent.click(within(row).getByRole('button', { name: 'Завантажити' }))

    await waitFor(() => expect(within(row).getAllByText('Обробляється…')).not.toHaveLength(0))
    expect(callsTo(fetchMock, 'POST', '/api/admin/episodes/101/video')).toHaveLength(1)
  })
})
