export type TitleKind = 'movie' | 'series'
export type SortField = 'rating' | 'year' | 'name' | 'popularity'
export type SortOrder = 'asc' | 'desc'

export interface Genre {
  id: number
  name: string
}

export interface Episode {
  id: number
  number: number
  name: string
}

export interface Season {
  id: number
  number: number
  episodes: Episode[]
}

export interface Title {
  id: number
  kind: TitleKind
  name: string
  description: string
  year: number
  country: string
  rating: number
  poster_url: string | null
  genres: Genre[]
  is_favorite: boolean
}

export interface TitleDetail extends Title {
  seasons: Season[]
}

export interface TitlePage {
  items: Title[]
  total: number
  page: number
  page_size: number
}

export interface TitleSearchParams {
  q?: string
  genre?: number[]
  year_from?: number
  year_to?: number
  country?: string
  kind?: TitleKind
  min_rating?: number
  sort?: SortField
  order?: SortOrder
  page?: number
  page_size?: number
}
