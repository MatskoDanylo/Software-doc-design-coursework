export function formatClock(totalSec: number): string {
  const safe = Math.max(0, Math.floor(totalSec))
  const hours = Math.floor(safe / 3600)
  const minutes = Math.floor((safe % 3600) / 60)
  const seconds = String(safe % 60).padStart(2, '0')
  return hours > 0 ? `${hours}:${String(minutes).padStart(2, '0')}:${seconds}` : `${minutes}:${seconds}`
}

export function progressPercent(progressSec: number, durationSec: number | null): number | null {
  if (durationSec === null || durationSec <= 0) return null
  return Math.min(100, Math.round((progressSec / durationSec) * 100))
}
