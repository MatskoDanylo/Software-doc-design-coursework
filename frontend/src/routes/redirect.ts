export interface RedirectState {
  from: string
}

export function redirectPath(state: unknown): string {
  if (typeof state === 'object' && state !== null && 'from' in state && typeof state.from === 'string') {
    return state.from
  }
  return '/'
}
