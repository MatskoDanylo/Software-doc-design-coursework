import { describe, expect, it } from 'vitest'
import { formatClock, progressPercent } from './time'

describe('time helpers', () => {
  it.each([
    [0, '0:00'],
    [7.9, '0:07'],
    [675, '11:15'],
    [3725, '1:02:05'],
    [-3, '0:00'],
  ])('formats %s s as %s', (seconds, text) => {
    expect(formatClock(seconds)).toBe(text)
  })

  it('computes progress only when the duration is known', () => {
    expect(progressPercent(675, 2700)).toBe(25)
    expect(progressPercent(3000, 2700)).toBe(100)
    expect(progressPercent(60, null)).toBeNull()
    expect(progressPercent(60, 0)).toBeNull()
  })
})
