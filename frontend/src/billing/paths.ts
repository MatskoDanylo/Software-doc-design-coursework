export function checkoutPath(paymentId: number): string {
  return `/checkout/${paymentId}`
}

export function paymentResultPath(paymentId: number): string {
  return `/payments/${paymentId}/result`
}

export function parseId(value: string | undefined): number | null {
  const id = Number(value)
  return Number.isInteger(id) && id > 0 ? id : null
}
