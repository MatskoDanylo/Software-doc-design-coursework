const CURRENCY_LABELS: Record<string, string> = { UAH: 'грн' }

export function formatMoney(amount: string, currency: string): string {
  const value = Number(amount)
  const digits = Number.isInteger(value) ? 0 : 2
  const number = value.toLocaleString('uk-UA', { minimumFractionDigits: digits, maximumFractionDigits: digits })
  return `${number} ${CURRENCY_LABELS[currency] ?? currency}`
}
