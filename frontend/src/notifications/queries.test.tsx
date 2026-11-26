import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { act, renderHook, waitFor } from '@testing-library/react'
import type { ReactNode } from 'react'
import { beforeEach, describe, expect, it } from 'vitest'
import { notificationsKeys } from '../api/notifications'
import { tokens } from '../api/tokens'
import { callsTo, mockApi, testTokens } from '../test/utils'
import type { AppNotification, NotificationInbox } from '../types/notification'
import { useMarkAllNotificationsRead, useMarkNotificationRead, useNotifications } from './queries'

function notification(id: number, read = false): AppNotification {
  return { id, kind: 'payment_pending', message: `#${id}`, read, created_at: '2026-11-25T10:00:00Z' }
}

const inbox: NotificationInbox = { items: [notification(1), notification(2), notification(3, true)], unread: 2 }

let client: QueryClient

function wrapper({ children }: { children: ReactNode }) {
  return <QueryClientProvider client={client}>{children}</QueryClientProvider>
}

beforeEach(() => {
  tokens.save(testTokens)
  client = new QueryClient({ defaultOptions: { queries: { retry: false, staleTime: Infinity } } })
  client.setQueryData(notificationsKeys.inbox, inbox)
})

const cached = () => client.getQueryData<NotificationInbox>(notificationsKeys.inbox)

describe('notification queries', () => {
  it('loads the inbox with the configured limit', async () => {
    client.removeQueries({ queryKey: notificationsKeys.inbox })
    const fetchMock = mockApi({ '/api/notifications': inbox })

    const { result } = renderHook(() => useNotifications(), { wrapper })

    await waitFor(() => expect(result.current.data).toEqual(inbox))
    expect(callsTo(fetchMock, 'GET', '/api/notifications')[0].url.searchParams.get('limit')).toBe('10')
  })

  it('marks one unread notification as read and decrements the counter', async () => {
    mockApi({ 'POST /api/notifications/2/read': notification(2, true), '/api/notifications': inbox })
    const { result } = renderHook(() => useMarkNotificationRead(), { wrapper })

    await act(() => result.current.mutateAsync(2))

    expect(cached()?.unread).toBe(1)
    expect(cached()?.items.map((n) => n.read)).toEqual([false, true, true])
  })

  it('does not decrement the counter for an already read notification', async () => {
    mockApi({ 'POST /api/notifications/3/read': notification(3, true), '/api/notifications': inbox })
    const { result } = renderHook(() => useMarkNotificationRead(), { wrapper })

    await act(() => result.current.mutateAsync(3))

    expect(cached()?.unread).toBe(2)
  })

  it('marks every notification as read', async () => {
    mockApi({ 'POST /api/notifications/read-all': { updated: 2 }, '/api/notifications': inbox })
    const { result } = renderHook(() => useMarkAllNotificationsRead(), { wrapper })

    await act(() => result.current.mutateAsync())

    expect(cached()?.unread).toBe(0)
    expect(cached()?.items.every((n) => n.read)).toBe(true)
  })
})
