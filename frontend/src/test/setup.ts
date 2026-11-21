import '@testing-library/jest-dom/vitest'
import { cleanup } from '@testing-library/react'
import { afterEach, vi } from 'vitest'
import { tokens } from '../api/tokens'

afterEach(() => {
  cleanup()
  tokens.clear()
  vi.unstubAllGlobals()
})
