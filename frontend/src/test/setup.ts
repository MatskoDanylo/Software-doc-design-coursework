import '@testing-library/jest-dom/vitest'
import { cleanup } from '@testing-library/react'
import { afterEach, vi } from 'vitest'
import { tokens } from '../api/tokens'

if (!('createObjectURL' in URL)) {
  Object.assign(URL, { createObjectURL: () => 'blob:test', revokeObjectURL: () => undefined })
}

afterEach(() => {
  cleanup()
  tokens.clear()
  vi.unstubAllGlobals()
})
