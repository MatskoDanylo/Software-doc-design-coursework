import { fireEvent, screen, waitFor, within } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import { callsTo, currentUrl, errorResponse, mockApi, renderApp, signedInAs, testUser } from '../../test/utils'
import type { Title, TitlePage } from '../../types/catalog'

const title: Title = {
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
}

const catalogPage: TitlePage = { items: [title], total: 1, page: 1, page_size: 24 }

function deferred() {
  let resolve: (response: Response) => void = () => undefined
  const promise = new Promise<Response>((done) => {
    resolve = done
  })
  return { promise, resolve }
}

function mockCatalog(routes: Record<string, unknown>) {
  return mockApi({
    ...signedInAs(testUser),
    '/api/titles': catalogPage,
    '/api/genres': [],
    '/api/countries': [],
    ...routes,
  })
}

const addLabel = 'Додати «Тестовий фільм» у вибране'
const removeLabel = 'Прибрати «Тестовий фільм» з вибраного'

describe('FavoriteButton', () => {
  it('marks the title as favorite before the server answers', async () => {
    const server = deferred()
    const fetchMock = mockCatalog({ 'POST /api/favorites/10': () => server.promise })
    renderApp('/catalog')

    const heart = await screen.findByRole('button', { name: addLabel })
    expect(heart).toHaveAttribute('aria-pressed', 'false')
    fireEvent.click(heart)

    const pressed = await screen.findByRole('button', { name: removeLabel })
    expect(pressed).toHaveAttribute('aria-pressed', 'true')
    expect(callsTo(fetchMock, 'POST', '/api/favorites/10')).toHaveLength(1)

    server.resolve(new Response(null, { status: 204 }))
    await waitFor(() => expect(screen.getByRole('button', { name: removeLabel })).toHaveAttribute('aria-pressed', 'true'))
  })

  it('rolls back when the server rejects the change', async () => {
    const server = deferred()
    mockCatalog({ 'POST /api/favorites/10': () => server.promise })
    renderApp('/catalog')

    fireEvent.click(await screen.findByRole('button', { name: addLabel }))
    expect(await screen.findByRole('button', { name: removeLabel })).toHaveAttribute('aria-pressed', 'true')

    server.resolve(errorResponse(500, 'server_error'))

    expect(await screen.findByRole('button', { name: addLabel })).toHaveAttribute('aria-pressed', 'false')
  })

  it('removes the card from the favorites page right away', async () => {
    const server = deferred()
    const favorites: TitlePage = { ...catalogPage, items: [{ ...title, is_favorite: true }] }
    mockCatalog({ '/api/favorites': favorites, 'DELETE /api/favorites/10': () => server.promise })
    renderApp('/favorites')

    fireEvent.click(await screen.findByRole('button', { name: removeLabel }))

    expect(await screen.findByText('У вибраному поки порожньо')).toBeInTheDocument()
    server.resolve(new Response(null, { status: 204 }))
  })

  it('shows the state on the title page and sends guests to sign in', async () => {
    mockApi({ '/api/titles/10': { ...title, seasons: [] } })
    renderApp('/titles/10')

    const details = await screen.findByRole('article')
    fireEvent.click(within(details).getByRole('button', { name: addLabel }))

    await waitFor(() => expect(currentUrl().pathname).toBe('/login'))
  })
})
