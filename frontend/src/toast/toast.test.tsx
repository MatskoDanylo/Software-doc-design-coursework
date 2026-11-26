import { QueryClient } from '@tanstack/react-query'
import { act, fireEvent, render, screen } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { ApiError } from '../api/client'
import { createMutationCache } from './mutationToasts'
import { getToasts, toast, TOAST_DURATION_MS } from './store'
import Toaster from './Toaster'

const texts = () => getToasts().map((item) => item.text)

describe('toast store', () => {
  beforeEach(() => vi.useFakeTimers())
  afterEach(() => vi.useRealTimers())

  it('hides a toast after its tone-specific duration', () => {
    toast.success('Збережено')
    toast.error('Помилка')

    vi.advanceTimersByTime(TOAST_DURATION_MS.success)
    expect(texts()).toEqual(['Помилка'])

    vi.advanceTimersByTime(TOAST_DURATION_MS.error - TOAST_DURATION_MS.success)
    expect(texts()).toEqual([])
  })

  it('does not stack duplicates and keeps only the latest four', () => {
    toast.success('Однакове')
    toast.success('Однакове')
    expect(texts()).toEqual(['Однакове'])

    for (const n of [1, 2, 3, 4]) toast.success(`#${n}`)
    expect(texts()).toEqual(['#1', '#2', '#3', '#4'])
  })
})

describe('Toaster', () => {
  it('announces success politely, errors as alerts, and can be closed', () => {
    render(<Toaster />)

    act(() => {
      toast.success('Жанр додано')
      toast.error('Сервер недоступний')
    })

    expect(screen.getByRole('status')).toHaveTextContent('Жанр додано')
    expect(screen.getByRole('alert')).toHaveTextContent('Сервер недоступний')

    fireEvent.click(screen.getAllByRole('button', { name: 'Закрити повідомлення' })[0])
    expect(screen.queryByText('Жанр додано')).not.toBeInTheDocument()
  })
})

describe('mutation toasts', () => {
  const client = () => new QueryClient({ mutationCache: createMutationCache() })

  it('shows the success text declared in meta', async () => {
    const queryClient = client()
    const mutation = queryClient
      .getMutationCache()
      .build(queryClient, { mutationFn: async () => 'ok', meta: { successToast: 'Зміни збережено' } })

    await mutation.execute(undefined)

    expect(texts()).toEqual(['Зміни збережено'])
  })

  it('translates the API error only when the mutation asks for it', async () => {
    const queryClient = client()
    const failing = (meta: { errorToast?: boolean }) =>
      queryClient.getMutationCache().build(queryClient, {
        mutationFn: () => Promise.reject(new ApiError(409, 'payment_not_pending', 'not pending')),
        meta,
      })

    await failing({}).execute(undefined).catch(() => undefined)
    expect(texts()).toEqual([])

    await failing({ errorToast: true }).execute(undefined).catch(() => undefined)
    expect(texts()).toEqual(['Платіж уже не очікує підтвердження'])
  })
})
