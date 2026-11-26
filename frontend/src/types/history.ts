import type { Title } from './catalog'

export interface HistoryEpisode {
  id: number
  number: number
  name: string
  season_number: number
}

export interface HistoryEntry {
  title: Title
  episode: HistoryEpisode | null
  progress_sec: number
  duration_sec: number | null
  finished: boolean
  last_watched: string
}
