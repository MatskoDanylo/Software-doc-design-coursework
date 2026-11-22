import { useState } from 'react'

export function useSyncedDraft(value: string) {
  const [draft, setDraft] = useState(value)
  const [synced, setSynced] = useState(value)

  if (value !== synced) {
    setSynced(value)
    setDraft(value)
  }

  return [draft, setDraft] as const
}
