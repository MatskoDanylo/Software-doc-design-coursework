import type { Playback } from '../types/playback'

export const SKIP_AFTER_SEC = 5

export function prerollUrl(playback: Playback): string | null {
  return playback.ads.enabled ? playback.ads.preroll_url : null
}

export function secondsUntilSkip(elapsedSec: number): number {
  return Math.max(0, Math.ceil(SKIP_AFTER_SEC - elapsedSec))
}
