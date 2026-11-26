import type { TitleKind } from './catalog'

export interface TitlePayload {
  kind: TitleKind
  name: string
  description: string
  year: number
  country: string
  rating: number
  genre_ids: number[]
}

export interface GenrePayload {
  name: string
}

export interface SeasonPayload {
  number: number
}

export interface EpisodePayload {
  number: number
  name: string
}
