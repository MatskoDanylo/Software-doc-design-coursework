import { MutationCache } from '@tanstack/react-query'
import { errorMessage } from '../api/errors'
import { toast } from './store'

/**
 * One rule for the whole app: a mutation declares its feedback in `meta`, the cache shows it.
 * - `successToast` — text shown after the change is saved.
 * - `errorToast` — show the translated API error. Forms leave it off and show errors next to the fields.
 */
export interface ToastMeta extends Record<string, unknown> {
  successToast?: string
  errorToast?: boolean
}

declare module '@tanstack/react-query' {
  interface Register {
    mutationMeta: ToastMeta
  }
}

export function createMutationCache(): MutationCache {
  return new MutationCache({
    onSuccess: (_data, _variables, _context, mutation) => {
      const text = mutation.meta?.successToast
      if (text) toast.success(text)
    },
    onError: (error, _variables, _context, mutation) => {
      if (mutation.meta?.errorToast) toast.error(errorMessage(error))
    },
  })
}
