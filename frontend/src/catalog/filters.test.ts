import { describe, expect, it } from 'vitest'
import { DEFAULT_FILTERS, filtersToParams, parseFilters, toSearchParams } from './filters'

describe('catalog filters', () => {
  it('round-trips every filter through URL query parameters', () => {
    const query = 'q=Dune&genre=2&genre=5&year_from=2000&year_to=2020&country=USA&kind=movie&min_rating=7&sort=year&order=asc&page=3'
    const filters = parseFilters(new URLSearchParams(query))

    expect(filters).toEqual({
      q: 'Dune',
      genres: [2, 5],
      yearFrom: 2000,
      yearTo: 2020,
      country: 'USA',
      kind: 'movie',
      minRating: 7,
      sort: 'year',
      order: 'asc',
      page: 3,
    })
    expect(filtersToParams(filters).toString()).toBe(query)
  })

  it('ignores invalid values and keeps the defaults out of the URL', () => {
    const filters = parseFilters(
      new URLSearchParams('genre=abc&genre=4&genre=4&year_from=1700&kind=cartoon&min_rating=11&sort=random&page=0'),
    )

    expect(filters).toEqual({ ...DEFAULT_FILTERS, genres: [4] })
    expect(filtersToParams({ ...filters, sort: 'rating', order: 'desc' }).toString()).toBe('genre=4')
  })

  it('maps filters to API search parameters', () => {
    const filters = { ...DEFAULT_FILTERS, q: 'Dune', genres: [1, 3], kind: 'series' as const, page: 2 }

    expect(toSearchParams(filters)).toEqual({
      q: 'Dune',
      genre: [1, 3],
      year_from: undefined,
      year_to: undefined,
      country: undefined,
      kind: 'series',
      min_rating: undefined,
      sort: 'rating',
      order: undefined,
      page: 2,
      page_size: 24,
    })
  })
})
