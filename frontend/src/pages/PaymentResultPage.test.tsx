import { fireEvent, screen, waitFor } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import { makePayment, outcomeFrom, plans, settledPayment } from '../test/billing'
import {
  callsTo,
  currentUrl,
  errorResponse,
  mockApi,
  renderApp,
  signedInAs,
  testPremiumUser,
  testUser,
} from '../test/utils'
import type { Payment } from '../types/billing'

function mockResult(initial: Payment) {
  let payment = initial
  const user = () => (payment.status === 'success' ? testPremiumUser : testUser)
  return mockApi({
    ...signedInAs(user()),
    '/api/users/me': () => Response.json(user()),
    '/api/plans': plans,
    '/api/notifications': { items: [], unread: 0 },
    '/api/billing/payments': () => Response.json([payment]),
    'POST /api/billing/payments/7/mock-result': (_url: URL, init?: RequestInit) => {
      const outcome = outcomeFrom(init)
      if (outcome === null) return errorResponse(422, 'validation_error')
      payment = settledPayment(payment, outcome)
      return Response.json(payment)
    },
    'POST /api/billing/checkout': () =>
      Response.json({ payment_id: 8, amount: '99.00', currency: 'UAH', status: 'created', plan: plans[1] }, { status: 201 }),
  })
}

describe('PaymentResultPage', () => {
  it('confirms a successful payment with the expiry date and a watch link', async () => {
    mockResult(settledPayment(makePayment(), 'success'))
    renderApp('/payments/7/result')

    expect(await screen.findByText('Оплату прийнято')).toBeInTheDocument()
    expect(
      await screen.findByText('План Premium активний до 25 грудня 2026 р. Відео без реклами, якість до 1080p.'),
    ).toBeInTheDocument()
    expect(screen.getByRole('link', { name: '▶ Дивитись' })).toHaveAttribute('href', '/catalog')
    expect(screen.getByRole('link', { name: 'Ваш план: Premium' })).toBeInTheDocument()
  })

  it('lets the user confirm a pending payment and refreshes the plan', async () => {
    const fetchMock = mockResult(makePayment({ status: 'pending' }))
    renderApp('/payments/7/result')

    expect(await screen.findByText('Оплата очікує підтвердження')).toBeInTheDocument()
    expect(screen.getByRole('link', { name: 'Ваш план: Free' })).toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: 'Підтвердити оплату' }))

    expect(await screen.findByText('Оплату прийнято')).toBeInTheDocument()
    expect(outcomeFrom(callsTo(fetchMock, 'POST', '/api/billing/payments/7/mock-result')[0].init)).toBe('success')
    expect(await screen.findByRole('link', { name: 'Ваш план: Premium' })).toBeInTheDocument()
    expect(callsTo(fetchMock, 'GET', '/api/users/me').length).toBeGreaterThan(1)
  })

  it('lets the user reject a pending payment', async () => {
    const fetchMock = mockResult(makePayment({ status: 'pending' }))
    renderApp('/payments/7/result')

    fireEvent.click(await screen.findByRole('button', { name: 'Відхилити' }))

    expect(await screen.findByText('Оплату відхилено')).toBeInTheDocument()
    expect(outcomeFrom(callsTo(fetchMock, 'POST', '/api/billing/payments/7/mock-result')[0].init)).toBe('failed')
  })

  it('offers a new attempt after a failed payment', async () => {
    const fetchMock = mockResult(settledPayment(makePayment(), 'failed'))
    renderApp('/payments/7/result')

    expect(await screen.findByText('Гроші не списано, підписка не змінилась.')).toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: 'Спробувати знову' }))

    await waitFor(() => expect(currentUrl().pathname).toBe('/checkout/8'))
    const [call] = callsTo(fetchMock, 'POST', '/api/billing/checkout')
    expect(JSON.parse(String(call.init?.body))).toEqual({ plan_code: 'premium' })
  })

  it('sends an unpaid payment back to the checkout', async () => {
    mockResult(makePayment())
    renderApp('/payments/7/result')

    await waitFor(() => expect(currentUrl().pathname).toBe('/checkout/7'))
  })
})
