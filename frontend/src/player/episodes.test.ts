import { describe, expect, it } from 'vitest'
import type { Season } from '../types/catalog'
import { episodeLabel, firstEpisode, nextEpisode, watchPath } from './episodes'

const seasons: Season[] = [
  { id: 1, number: 1, episodes: [{ id: 11, number: 1, name: 'Пілот' }, { id: 12, number: 2, name: 'Друга' }] },
  { id: 2, number: 2, episodes: [] },
  { id: 3, number: 3, episodes: [{ id: 31, number: 1, name: 'Повернення' }] },
]

describe('episode navigation', () => {
  it('starts from the first episode of the first non-empty season', () => {
    expect(firstEpisode(seasons)?.id).toBe(11)
    expect(firstEpisode([{ id: 9, number: 1, episodes: [] }])).toBeNull()
  })

  it('moves to the next episode across empty seasons', () => {
    expect(nextEpisode(seasons, 11)?.id).toBe(12)
    expect(nextEpisode(seasons, 12)?.id).toBe(31)
    expect(nextEpisode(seasons, 31)).toBeNull()
    expect(nextEpisode(seasons, 999)).toBeNull()
  })

  it('formats labels and player links', () => {
    expect(episodeLabel({ id: 31, number: 1, name: 'Повернення', seasonNumber: 3 })).toBe('С3 Е1 · Повернення')
    expect(watchPath(20, 31)).toBe('/watch/20?episode=31')
    expect(watchPath(10)).toBe('/watch/10')
  })
})
