import { fireEvent, screen, waitFor, within } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import { plans } from '../test/billing'
import { callsTo, currentUrl, mockApi, renderApp, signedInAs, testPremiumUser, testUser } from '../test/utils'

describe('PricingPage', () => {
  it('shows both plans and sends guests to sign in before checkout', async () => {
    mockApi({ '/api/plans': plans })
    renderApp('/pricing')

    const premium = await screen.findByRole('article', { name: 'Premium' })
    expect(within(premium).getByText('Якість до 1080p')).toBeInTheDocument()
    expect(within(premium).getByText('Без реклами')).toBeInTheDocument()
    expect(within(screen.getByRole('article', { name: 'Free' })).getByText('Реклама перед відео')).toBeInTheDocument()

    fireEvent.click(within(premium).getByRole('link', { name: 'Оформити Premium' }))
    expect(currentUrl().pathname).toBe('/login')
  })

  it('marks the current plan and starts checkout for a signed-in user', async () => {
    const fetchMock = mockApi({
      ...signedInAs(testUser),
      '/api/plans': plans,
      '/api/notifications': { items: [], unread: 0 },
      '/api/billing/payments': [],
      'POST /api/billing/checkout': () =>
        Response.json({ payment_id: 5, amount: '99.00', currency: 'UAH', status: 'created', plan: plans[1] }, { status: 201 }),
    })
    renderApp('/pricing')

    const free = await screen.findByRole('article', { name: 'Free' })
    expect(within(free).getByText('Ваш план')).toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: 'Оформити Premium' }))

    await waitFor(() => expect(currentUrl().pathname).toBe('/checkout/5'))
    expect(callsTo(fetchMock, 'POST', '/api/billing/checkout')).toHaveLength(1)
  })

  it('offers to extend Premium for a premium user', async () => {
    mockApi({ ...signedInAs(testPremiumUser), '/api/plans': plans, '/api/notifications': { items: [], unread: 0 } })
    renderApp('/pricing')

    const premium = await screen.findByRole('article', { name: 'Premium' })
    expect(within(premium).getByText('Ваш план')).toBeInTheDocument()
    expect(within(premium).getByRole('button', { name: 'Продовжити Premium' })).toBeInTheDocument()
  })
})
