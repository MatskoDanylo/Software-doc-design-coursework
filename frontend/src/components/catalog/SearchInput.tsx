import { useId } from 'react'
import { useDebouncedCallback } from '../../hooks/useDebouncedCallback'
import { useSyncedDraft } from '../../hooks/useSyncedDraft'
import { controlClass, labelClass } from '../ui'

export const SEARCH_DEBOUNCE_MS = 400

interface SearchInputProps {
  label: string
  value: string
  onCommit: (value: string) => void
  placeholder?: string
}

export default function SearchInput({ label, value, onCommit, placeholder }: SearchInputProps) {
  const id = useId()
  const [draft, setDraft] = useSyncedDraft(value)
  const commit = useDebouncedCallback((next: string) => onCommit(next.trim()), SEARCH_DEBOUNCE_MS)

  return (
    <div className="space-y-1.5">
      <label htmlFor={id} className={labelClass}>
        {label}
      </label>
      <input
        id={id}
        type="search"
        value={draft}
        placeholder={placeholder}
        maxLength={100}
        className={controlClass()}
        onChange={(event) => {
          setDraft(event.target.value)
          commit(event.target.value)
        }}
      />
    </div>
  )
}
