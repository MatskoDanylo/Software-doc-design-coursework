import { beforeEach, describe, expect, it } from 'vitest'
import { parsePage } from '../admin/billing'
import { callsTo, mockApi, testTokens } from '../test/utils'
import { adminBillingApi } from './adminBilling'
import { tokens } from './tokens'

beforeEach(() => tokens.save(testTokens))

describe('adminBillingApi', () => {
  it('sends the status filter only when it is set', async () => {
    const fetchMock = mockApi({ '/api/admin/payments': { items: [], total: 0, page: 1, page_size: 20 } })

    await adminBillingApi.payments({ status: 'pending', page: 2 })
    await adminBillingApi.payments({ status: null, page: 1 })

    const [filtered, all] = callsTo(fetchMock, 'GET', '/api/admin/payments').map(({ url }) => url.searchParams)
    expect(Object.fromEntries(filtered)).toEqual({ page: '2', page_size: '20', status: 'pending' })
    expect(all.has('status')).toBe(false)
  })

  it('turns a page number into limit and offset for users', async () => {
    const fetchMock = mockApi({ '/api/admin/users': [] })

    await adminBillingApi.users(3)

    const [{ url }] = callsTo(fetchMock, 'GET', '/api/admin/users')
    expect(Object.fromEntries(url.searchParams)).toEqual({ limit: '20', offset: '40' })
  })

  it('posts the resolve outcome and subscription changes', async () => {
    const fetchMock = mockApi({
      'POST /api/admin/payments/7/resolve': { id: 7 },
      'POST /api/admin/users/5/subscription': { plan_code: 'premium' },
    })

    await adminBillingApi.resolve(7, 'success')
    await adminBillingApi.changeSubscription(5, { action: 'grant', days: 30 })

    expect(callsTo(fetchMock, 'POST', '/api/admin/payments/7/resolve')[0].init?.body).toBe('{"outcome":"success"}')
    expect(callsTo(fetchMock, 'POST', '/api/admin/users/5/subscription')[0].init?.body).toBe(
      '{"action":"grant","days":30}',
    )
  })
})

describe('parsePage', () => {
  it.each([
    ['3', 3],
    [null, 1],
    ['0', 1],
    ['-2', 1],
    ['1.5', 1],
    ['abc', 1],
  ])('parses %s as %i', (value, page) => {
    expect(parsePage(value)).toBe(page)
  })
})
