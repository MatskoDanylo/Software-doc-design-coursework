const CURRENCY_LABELS: Record<string, string> = { UAH: 'грн' }
const dateFormat = new Intl.DateTimeFormat('uk-UA', { dateStyle: 'long' })

export function formatMoney(amount: string, currency: string): string {
  const value = Number(amount)
  const digits = Number.isInteger(value) ? 0 : 2
  const number = value.toLocaleString('uk-UA', { minimumFractionDigits: digits, maximumFractionDigits: digits })
  return `${number} ${CURRENCY_LABELS[currency] ?? currency}`
}

export function formatDate(iso: string): string {
  return dateFormat.format(new Date(iso))
}
