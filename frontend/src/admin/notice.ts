export interface AdminNotice {
  tone: 'success' | 'error'
  text: string
}

export function readNotice(state: unknown): AdminNotice | null {
  if (typeof state !== 'object' || state === null || !('notice' in state)) return null
  const { notice } = state
  if (typeof notice !== 'object' || notice === null || !('text' in notice) || !('tone' in notice)) return null
  const { text, tone } = notice
  if (typeof text !== 'string' || (tone !== 'success' && tone !== 'error')) return null
  return { text, tone }
}
