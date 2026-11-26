import type { SortField, SortOrder, TitleKind, TitleSearchParams } from '../types/catalog'

export const CATALOG_PAGE_SIZE = 24
export const YEAR_MIN = 1880
export const YEAR_MAX = 2100

export interface CatalogFilters {
  q: string
  genres: number[]
  yearFrom: number | null
  yearTo: number | null
  country: string
  kind: TitleKind | null
  minRating: number | null
  sort: SortField
  order: SortOrder | null
  page: number
}

export const DEFAULT_FILTERS: CatalogFilters = {
  q: '',
  genres: [],
  yearFrom: null,
  yearTo: null,
  country: '',
  kind: null,
  minRating: null,
  sort: 'rating',
  order: null,
  page: 1,
}

export const DEFAULT_ORDER: Record<SortField, SortOrder> = {
  rating: 'desc',
  year: 'desc',
  name: 'asc',
  popularity: 'desc',
}

const KINDS: readonly TitleKind[] = ['movie', 'series']
const SORT_FIELDS: readonly SortField[] = ['rating', 'year', 'name', 'popularity']
const ORDERS: readonly SortOrder[] = ['asc', 'desc']

function oneOf<T extends string>(value: string | null, allowed: readonly T[]): T | null {
  return allowed.find((item) => item === value) ?? null
}

function integer(value: string | null, min: number, max: number): number | null {
  if (value === null || !/^\d+$/.test(value)) return null
  const number = Number(value)
  return number >= min && number <= max ? number : null
}

function rating(value: string | null): number | null {
  if (value === null || value.trim() === '') return null
  const number = Number(value)
  return Number.isFinite(number) && number >= 0 && number <= 10 ? number : null
}

export function isValidYear(year: number): boolean {
  return Number.isInteger(year) && year >= YEAR_MIN && year <= YEAR_MAX
}

export function parseYear(value: string): number | null {
  return value.trim() === '' ? null : Number(value)
}

export function yearRangeError(from: string, to: string): string | undefined {
  const [start, end] = [parseYear(from), parseYear(to)]
  if ([start, end].some((year) => year !== null && !isValidYear(year))) return `Рік від ${YEAR_MIN} до ${YEAR_MAX}`
  if (start !== null && end !== null && start > end) return 'Рік «від» більший за «до»'
  return undefined
}

export function parseFilters(params: URLSearchParams): CatalogFilters {
  const genres = params.getAll('genre').map((value) => integer(value, 1, Number.MAX_SAFE_INTEGER))
  return {
    q: params.get('q')?.trim() ?? '',
    genres: [...new Set(genres.filter((id) => id !== null))],
    yearFrom: integer(params.get('year_from'), YEAR_MIN, YEAR_MAX),
    yearTo: integer(params.get('year_to'), YEAR_MIN, YEAR_MAX),
    country: params.get('country')?.trim() ?? '',
    kind: oneOf(params.get('kind'), KINDS),
    minRating: rating(params.get('min_rating')),
    sort: oneOf(params.get('sort'), SORT_FIELDS) ?? DEFAULT_FILTERS.sort,
    order: oneOf(params.get('order'), ORDERS),
    page: integer(params.get('page'), 1, Number.MAX_SAFE_INTEGER) ?? 1,
  }
}

export function filtersToParams(filters: CatalogFilters): URLSearchParams {
  const params = new URLSearchParams()
  if (filters.q) params.set('q', filters.q)
  for (const id of filters.genres) params.append('genre', String(id))
  if (filters.yearFrom !== null) params.set('year_from', String(filters.yearFrom))
  if (filters.yearTo !== null) params.set('year_to', String(filters.yearTo))
  if (filters.country) params.set('country', filters.country)
  if (filters.kind) params.set('kind', filters.kind)
  if (filters.minRating !== null) params.set('min_rating', String(filters.minRating))
  if (filters.sort !== DEFAULT_FILTERS.sort) params.set('sort', filters.sort)
  if (filters.order !== null && filters.order !== DEFAULT_ORDER[filters.sort]) params.set('order', filters.order)
  if (filters.page > 1) params.set('page', String(filters.page))
  return params
}

export function toSearchParams(filters: CatalogFilters): TitleSearchParams {
  return {
    q: filters.q || undefined,
    genre: filters.genres.length ? filters.genres : undefined,
    year_from: filters.yearFrom ?? undefined,
    year_to: filters.yearTo ?? undefined,
    country: filters.country || undefined,
    kind: filters.kind ?? undefined,
    min_rating: filters.minRating ?? undefined,
    sort: filters.sort,
    order: filters.order ?? undefined,
    page: filters.page,
    page_size: CATALOG_PAGE_SIZE,
  }
}

export function hasActiveFilters(filters: CatalogFilters): boolean {
  return Boolean(
    filters.q ||
      filters.genres.length ||
      filters.yearFrom !== null ||
      filters.yearTo !== null ||
      filters.country ||
      filters.kind ||
      filters.minRating !== null,
  )
}

export interface SortOption {
  label: string
  sort: SortField
  order: SortOrder
}

export const SORT_OPTIONS: readonly SortOption[] = [
  { label: 'За рейтингом', sort: 'rating', order: 'desc' },
  { label: 'Спочатку нові', sort: 'year', order: 'desc' },
  { label: 'Спочатку старі', sort: 'year', order: 'asc' },
  { label: 'За назвою А–Я', sort: 'name', order: 'asc' },
  { label: 'За назвою Я–А', sort: 'name', order: 'desc' },
  { label: 'Популярні', sort: 'popularity', order: 'desc' },
]

export function sortKey(sort: SortField, order: SortOrder | null): string {
  return `${sort}:${order ?? DEFAULT_ORDER[sort]}`
}
