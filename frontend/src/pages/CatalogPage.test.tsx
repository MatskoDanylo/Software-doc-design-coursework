import { fireEvent, screen, waitFor } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import { callsTo, currentUrl, mockApi, renderApp } from '../test/utils'
import type { Genre, Title, TitlePage } from '../types/catalog'

const genres: Genre[] = [
  { id: 1, name: 'Драма' },
  { id: 2, name: 'Комедія' },
  { id: 3, name: 'Фантастика' },
]

const title: Title = {
  id: 10,
  kind: 'movie',
  name: 'Тестовий фільм',
  description: '',
  year: 2015,
  country: 'Україна',
  rating: 8.1,
  poster_url: null,
  genres: [genres[0]],
}

const page: TitlePage = { items: [title], total: 1, page: 1, page_size: 24 }

function mockCatalog() {
  return mockApi({ '/api/titles': page, '/api/genres': genres, '/api/countries': ['Україна', 'США'] })
}

function lastSearch(fetchMock: ReturnType<typeof mockCatalog>): URLSearchParams {
  const calls = callsTo(fetchMock, 'GET', '/api/titles')
  return calls[calls.length - 1].url.searchParams
}

describe('CatalogPage filters and URL', () => {
  it('restores filters from the URL and sends them to the API', async () => {
    const fetchMock = mockCatalog()
    renderApp('/catalog?q=Тест&genre=1&genre=3&kind=series&year_from=2000&sort=year&order=asc&page=2')

    expect(await screen.findByRole('heading', { name: 'Тестовий фільм' })).toBeInTheDocument()
    expect(screen.getByLabelText('Пошук')).toHaveValue('Тест')
    expect(screen.getByLabelText('Рік від')).toHaveValue(2000)
    expect(screen.getByRole('button', { name: 'Серіали' })).toHaveAttribute('aria-pressed', 'true')
    expect(await screen.findByRole('button', { name: 'Драма' })).toHaveAttribute('aria-pressed', 'true')
    expect(screen.getByRole('button', { name: 'Комедія' })).toHaveAttribute('aria-pressed', 'false')
    expect(screen.getByRole('button', { name: 'Фантастика' })).toHaveAttribute('aria-pressed', 'true')
    expect(screen.getByLabelText('Сортування')).toHaveValue('year:asc')

    const search = lastSearch(fetchMock)
    expect(search.get('q')).toBe('Тест')
    expect(search.getAll('genre')).toEqual(['1', '3'])
    expect(search.get('kind')).toBe('series')
    expect(search.get('year_from')).toBe('2000')
    expect(search.get('sort')).toBe('year')
    expect(search.get('order')).toBe('asc')
    expect(search.get('page')).toBe('2')
  })

  it('writes filter changes to the URL and resets the page', async () => {
    const fetchMock = mockCatalog()
    renderApp('/catalog?page=3')

    fireEvent.click(await screen.findByRole('button', { name: 'Комедія' }))
    expect(currentUrl().searchParams.getAll('genre')).toEqual(['2'])
    expect(currentUrl().searchParams.has('page')).toBe(false)

    fireEvent.click(screen.getByRole('button', { name: 'Фільми' }))
    fireEvent.change(screen.getByLabelText('Мінімальний рейтинг'), { target: { value: '7' } })
    fireEvent.change(screen.getByLabelText('Сортування'), { target: { value: 'name:asc' } })
    expect(currentUrl().search).toBe('?genre=2&kind=movie&min_rating=7&sort=name')

    await waitFor(() => expect(lastSearch(fetchMock).get('sort')).toBe('name'))
    expect(lastSearch(fetchMock).get('min_rating')).toBe('7')
  })

  it('debounces the search input before updating the URL', async () => {
    mockCatalog()
    renderApp('/catalog')

    fireEvent.change(await screen.findByLabelText('Пошук'), { target: { value: 'Дюна' } })
    expect(currentUrl().searchParams.has('q')).toBe(false)
    await waitFor(() => expect(currentUrl().searchParams.get('q')).toBe('Дюна'))
  })

  it('resets filters but keeps sorting', async () => {
    mockCatalog()
    renderApp('/catalog?q=Тест&kind=movie&sort=year&order=asc')

    fireEvent.click(await screen.findByRole('button', { name: 'Скинути фільтри' }))
    expect(currentUrl().search).toBe('?sort=year&order=asc')
    expect(screen.getByLabelText('Пошук')).toHaveValue('')
  })
})
