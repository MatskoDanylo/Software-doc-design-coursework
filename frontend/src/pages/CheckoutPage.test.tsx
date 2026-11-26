import { fireEvent, screen, waitFor } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import { makePayment, outcomeFrom, plans, settledPayment } from '../test/billing'
import { callsTo, currentUrl, errorResponse, mockApi, renderApp, signedInAs, testUser } from '../test/utils'
import type { Payment, PaymentOutcome } from '../types/billing'

function mockCheckout(initial: Payment = makePayment()) {
  let payment = initial
  return mockApi({
    ...signedInAs(testUser),
    '/api/plans': plans,
    '/api/notifications': { items: [], unread: 0 },
    '/api/billing/payments': () => Response.json([payment]),
    'POST /api/billing/payments/7/mock-result': (_url: URL, init?: RequestInit) => {
      const outcome = outcomeFrom(init)
      if (outcome === null) return errorResponse(422, 'validation_error')
      payment = settledPayment(payment, outcome)
      return Response.json(payment)
    },
  })
}

describe('CheckoutPage', () => {
  it('marks the payment as a test one and shows the plan and amount', async () => {
    mockCheckout()
    renderApp('/checkout/7')

    expect(await screen.findByRole('note')).toHaveTextContent('Тестова оплата')
    expect(screen.getByText('Преміум')).toBeInTheDocument()
    expect(screen.getByText('99 грн')).toBeInTheDocument()
    expect(screen.getByRole('radio', { name: 'Успішна оплата' })).toBeChecked()
    expect(screen.getByRole('radio', { name: 'Очікує підтвердження' })).toHaveAccessibleDescription(/ще перевіряє платіж/)
  })

  it.each<[string, PaymentOutcome]>([
    ['Успішна оплата', 'success'],
    ['Очікує підтвердження', 'pending'],
    ['Відхилено банком', 'failed'],
  ])('sends the outcome chosen with «%s» and opens the result page', async (label, outcome) => {
    const fetchMock = mockCheckout()
    renderApp('/checkout/7')

    fireEvent.click(await screen.findByRole('radio', { name: label }))
    fireEvent.click(screen.getByRole('button', { name: 'Оплатити' }))

    await waitFor(() => expect(currentUrl().pathname).toBe('/payments/7/result'))
    const [call] = callsTo(fetchMock, 'POST', '/api/billing/payments/7/mock-result')
    expect(outcomeFrom(call.init)).toBe(outcome)
  })

  it('shows the server error and stays on the page when the payment fails to submit', async () => {
    mockApi({
      ...signedInAs(testUser),
      '/api/plans': plans,
      '/api/billing/payments': [makePayment()],
      'POST /api/billing/payments/7/mock-result': () => errorResponse(404, 'mock_payments_disabled'),
    })
    renderApp('/checkout/7')

    fireEvent.click(await screen.findByRole('button', { name: 'Оплатити' }))

    expect(await screen.findByRole('alert')).toHaveTextContent('Тестова оплата вимкнена на сервері')
    expect(currentUrl().pathname).toBe('/checkout/7')
  })

  it('redirects to the result page when the payment was already submitted', async () => {
    mockCheckout(makePayment({ status: 'pending' }))
    renderApp('/checkout/7')

    await waitFor(() => expect(currentUrl().pathname).toBe('/payments/7/result'))
    expect(await screen.findByText('Оплата очікує підтвердження')).toBeInTheDocument()
  })

  it('reports an unknown payment', async () => {
    mockCheckout()
    renderApp('/checkout/99')

    expect(await screen.findByText('Платіж не знайдено')).toBeInTheDocument()
  })
})
