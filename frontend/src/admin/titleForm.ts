import type { FieldErrors } from '../auth/validation'
import { isValidYear, YEAR_MAX, YEAR_MIN } from '../catalog/filters'
import type { TitlePayload } from '../types/adminCatalog'
import type { TitleDetail, TitleKind } from '../types/catalog'

export type TitleValues = {
  kind: string
  name: string
  description: string
  year: string
  country: string
  rating: string
}

export interface TitleSubmit {
  payload: TitlePayload
  poster: File | null
}

export const POSTER_TYPES = ['image/jpeg', 'image/png', 'image/webp']
export const POSTER_MAX_BYTES = 5 * 1024 * 1024
const NAME_MAX = 255
const COUNTRY_MAX = 100
const DESCRIPTION_MAX = 5000

export const EMPTY_TITLE: TitleValues = {
  kind: 'movie',
  name: '',
  description: '',
  year: '',
  country: '',
  rating: '',
}

export function titleToValues(title: TitleDetail): TitleValues {
  return {
    kind: title.kind,
    name: title.name,
    description: title.description,
    year: String(title.year),
    country: title.country,
    rating: String(title.rating),
  }
}

function requiredText(value: string, max: number, emptyMessage: string): string | undefined {
  const text = value.trim()
  if (!text) return emptyMessage
  return text.length > max ? `Максимум ${max} символів` : undefined
}

function ratingError(value: string): string | undefined {
  if (value.trim() === '') return undefined
  const rating = Number(value)
  return Number.isFinite(rating) && rating >= 0 && rating <= 10 ? undefined : 'Рейтинг від 0 до 10'
}

export function validateTitle(values: TitleValues): FieldErrors<keyof TitleValues> {
  return {
    kind: values.kind === 'movie' || values.kind === 'series' ? undefined : 'Оберіть тип',
    name: requiredText(values.name, NAME_MAX, 'Вкажіть назву'),
    description: values.description.length > DESCRIPTION_MAX ? `Максимум ${DESCRIPTION_MAX} символів` : undefined,
    year: isValidYear(Number(values.year)) && values.year.trim() !== '' ? undefined : `Рік від ${YEAR_MIN} до ${YEAR_MAX}`,
    country: requiredText(values.country, COUNTRY_MAX, 'Вкажіть країну'),
    rating: ratingError(values.rating),
  }
}

function toKind(value: string): TitleKind {
  return value === 'series' ? 'series' : 'movie'
}

export function toTitlePayload(values: TitleValues, genreIds: number[]): TitlePayload {
  return {
    kind: toKind(values.kind),
    name: values.name.trim(),
    description: values.description.trim(),
    year: Number(values.year),
    country: values.country.trim(),
    rating: values.rating.trim() === '' ? 0 : Number(values.rating),
    genre_ids: genreIds,
  }
}

export function posterFileError(file: File): string | undefined {
  if (!POSTER_TYPES.includes(file.type)) return 'Оберіть зображення JPEG, PNG або WebP'
  if (file.size > POSTER_MAX_BYTES) return 'Файл завеликий: максимум 5 МБ'
  return undefined
}
