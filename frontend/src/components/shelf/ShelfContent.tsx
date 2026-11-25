import type { ReactNode } from 'react'
import { errorMessage } from '../../api/errors'
import { ShelfEmpty, ShelfError, ShelfSkeleton } from './ShelfStates'

export interface LoadState {
  isPending: boolean
  isError: boolean
  error: unknown
  refetch: () => unknown
}

interface ShelfContentProps<T> {
  state: LoadState
  items: readonly T[] | undefined
  emptyText?: string
  itemKey: (item: T) => number
  renderItem: (item: T) => ReactNode
}

export default function ShelfContent<T>({ state, items, emptyText, itemKey, renderItem }: ShelfContentProps<T>) {
  if (state.isPending) return <ShelfSkeleton />
  if (state.isError) return <ShelfError message={errorMessage(state.error)} onRetry={() => void state.refetch()} />
  if (!items || items.length === 0) return emptyText ? <ShelfEmpty text={emptyText} /> : null

  return (
    <ol className="flex gap-4 overflow-x-auto pb-2">
      {items.map((item) => (
        <li key={itemKey(item)}>{renderItem(item)}</li>
      ))}
    </ol>
  )
}
