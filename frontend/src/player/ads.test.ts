import { describe, expect, it } from 'vitest'
import type { Playback } from '../types/playback'
import { prerollUrl, secondsUntilSkip, SKIP_AFTER_SEC } from './ads'

const base: Playback = {
  plan: 'free',
  manifest_url: '/api/playback/1/master.m3u8',
  ads: { enabled: true, preroll_url: '/media/ads/preroll/master.m3u8' },
  allowed_heights: [360, 720],
  resume_position_sec: 0,
}

describe('pre-roll decision', () => {
  it('plays the pre-roll for the free plan', () => {
    expect(prerollUrl(base)).toBe('/media/ads/preroll/master.m3u8')
  })

  it('skips ads for the premium plan', () => {
    expect(prerollUrl({ ...base, plan: 'premium', ads: { enabled: false, preroll_url: null } })).toBeNull()
  })

  it('skips ads when the server has no pre-roll file', () => {
    expect(prerollUrl({ ...base, ads: { enabled: true, preroll_url: null } })).toBeNull()
  })

  it('never shows ads the server did not enable', () => {
    expect(prerollUrl({ ...base, ads: { enabled: false, preroll_url: '/media/ads/preroll/master.m3u8' } })).toBeNull()
  })
})

describe('skip countdown', () => {
  it.each([
    [0, 5],
    [0.2, 5],
    [3.4, 2],
    [4.01, 1],
    [SKIP_AFTER_SEC, 0],
    [7.5, 0],
  ])('after %s s of the ad waits %s s more', (elapsed, wait) => {
    expect(secondsUntilSkip(elapsed)).toBe(wait)
  })
})
