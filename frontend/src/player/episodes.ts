import type { Episode, Season } from '../types/catalog'

export interface EpisodeRef extends Episode {
  seasonNumber: number
}

export function flattenEpisodes(seasons: Season[]): EpisodeRef[] {
  return seasons.flatMap((season) => season.episodes.map((episode) => ({ ...episode, seasonNumber: season.number })))
}

export function firstEpisode(seasons: Season[]): EpisodeRef | null {
  return flattenEpisodes(seasons)[0] ?? null
}

export function nextEpisode(seasons: Season[], currentId: number): EpisodeRef | null {
  const episodes = flattenEpisodes(seasons)
  const index = episodes.findIndex((episode) => episode.id === currentId)
  return index === -1 ? null : (episodes[index + 1] ?? null)
}

export function episodeLabel(episode: EpisodeRef): string {
  return `С${episode.seasonNumber} Е${episode.number} · ${episode.name}`
}

export function watchPath(titleId: number, episodeId: number | null = null): string {
  return episodeId === null ? `/watch/${titleId}` : `/watch/${titleId}?episode=${episodeId}`
}
