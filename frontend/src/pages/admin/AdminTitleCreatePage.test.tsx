import { fireEvent, screen, waitFor } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import { callsTo, currentUrl, errorResponse, mockApi, renderApp, signedInAs, testAdmin, testUser } from '../../test/utils'
import type { TitlePayload } from '../../types/adminCatalog'
import type { Genre, TitleDetail } from '../../types/catalog'

const genres: Genre[] = [
  { id: 1, name: 'Драма' },
  { id: 2, name: 'Фантастика' },
]

const created: TitleDetail = {
  id: 7,
  kind: 'series',
  name: 'Нова серія',
  description: 'Опис серіалу',
  year: 2024,
  country: 'Україна',
  rating: 7.5,
  poster_url: null,
  genres: [genres[1]],
  seasons: [],
}

const referenceRoutes = { '/api/genres': genres, '/api/countries': ['Україна'] }

async function openCreatePage(routes: Record<string, unknown>) {
  const fetchMock = mockApi({ ...signedInAs(testAdmin), ...referenceRoutes, ...routes })
  renderApp('/admin/titles/new')
  await screen.findByRole('heading', { name: 'Новий тайтл' })
  return fetchMock
}

function fillRequiredFields() {
  fireEvent.change(screen.getByLabelText('Назва'), { target: { value: '  Нова серія ' } })
  fireEvent.change(screen.getByLabelText('Рік'), { target: { value: '2024' } })
  fireEvent.change(screen.getByLabelText('Країна'), { target: { value: 'Україна' } })
}

function submit() {
  fireEvent.click(screen.getByRole('button', { name: 'Створити' }))
}

describe('AdminTitleCreatePage', () => {
  it('denies access to non-admin users', async () => {
    mockApi({ ...signedInAs(testUser), ...referenceRoutes })
    renderApp('/admin/titles/new')

    expect(await screen.findByText('Цей розділ доступний лише адміністраторам')).toBeInTheDocument()
    expect(screen.queryByRole('heading', { name: 'Новий тайтл' })).not.toBeInTheDocument()
  })

  it('validates required fields on the client', async () => {
    const fetchMock = await openCreatePage({})

    fireEvent.change(screen.getByLabelText('Рейтинг'), { target: { value: '12' } })
    submit()

    expect(screen.getByText('Вкажіть назву')).toBeInTheDocument()
    expect(screen.getByText('Рік від 1880 до 2100')).toBeInTheDocument()
    expect(screen.getByText('Вкажіть країну')).toBeInTheDocument()
    expect(screen.getByText('Рейтинг від 0 до 10')).toBeInTheDocument()
    expect(callsTo(fetchMock, 'POST', '/api/admin/titles')).toHaveLength(0)
  })

  it('creates a title, uploads the poster and opens the edit page', async () => {
    const fetchMock = await openCreatePage({
      'POST /api/admin/titles': () => Response.json(created, { status: 201 }),
      'POST /api/admin/titles/7/poster': { ...created, poster_url: '/media/posters/7.png' },
      '/api/titles/7': created,
    })

    fillRequiredFields()
    fireEvent.change(screen.getByLabelText('Тип'), { target: { value: 'series' } })
    fireEvent.change(screen.getByLabelText('Опис'), { target: { value: 'Опис серіалу' } })
    fireEvent.change(screen.getByLabelText('Рейтинг'), { target: { value: '7.5' } })
    fireEvent.click(await screen.findByRole('button', { name: 'Фантастика' }))
    const poster = new File(['poster'], 'poster.png', { type: 'image/png' })
    fireEvent.change(screen.getByLabelText('Файл постера'), { target: { files: [poster] } })
    expect(screen.getByText('Буде завантажено: poster.png')).toBeInTheDocument()
    submit()

    expect(await screen.findByText('Тайтл створено, постер завантажено')).toBeInTheDocument()
    expect(screen.getByRole('heading', { name: 'Нова серія' })).toBeInTheDocument()
    expect(currentUrl().pathname).toBe('/admin/titles/7')

    const [createCall] = callsTo(fetchMock, 'POST', '/api/admin/titles')
    const payload: TitlePayload = JSON.parse(String(createCall.init?.body))
    expect(payload).toEqual({
      kind: 'series',
      name: 'Нова серія',
      description: 'Опис серіалу',
      year: 2024,
      country: 'Україна',
      rating: 7.5,
      genre_ids: [2],
    })
    const [uploadCall] = callsTo(fetchMock, 'POST', '/api/admin/titles/7/poster')
    const form = uploadCall.init?.body
    expect(form).toBeInstanceOf(FormData)
    expect(form instanceof FormData && form.get('file')).toBe(poster)
  })

  it('shows backend conflict and field errors in the form', async () => {
    const responses = [
      errorResponse(409, 'title_exists'),
      errorResponse(422, 'validation_error', [{ loc: ['body', 'country'], msg: 'Країна закоротка', type: 'value_error' }]),
    ]
    await openCreatePage({ 'POST /api/admin/titles': () => responses.shift() ?? errorResponse(500, 'internal_error') })

    fillRequiredFields()
    submit()
    expect(await screen.findByRole('alert')).toHaveTextContent('Тайтл з таким типом, назвою і роком уже існує')

    submit()
    expect(await screen.findByText('Країна закоротка')).toBeInTheDocument()
    expect(screen.getByLabelText('Країна')).toHaveAttribute('aria-invalid', 'true')
    await waitFor(() => expect(currentUrl().pathname).toBe('/admin/titles/new'))
  })
})
