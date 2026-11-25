import { isPaymentStatus, PAYMENT_STATUS } from '../billing/statuses'
import type { GroupBy, ReportCell } from '../types/report'
import { parseIsoDate } from './dates'

const numberFormat = new Intl.NumberFormat('uk-UA', { maximumFractionDigits: 2 })
const dayFormat = new Intl.DateTimeFormat('uk-UA', { day: 'numeric', month: 'short' })
const monthFormat = new Intl.DateTimeFormat('uk-UA', { month: 'short', year: 'numeric' })
const fullDateFormat = new Intl.DateTimeFormat('uk-UA', { day: 'numeric', month: 'long', year: 'numeric' })

export function formatNumber(value: number): string {
  return numberFormat.format(value)
}

export function formatMoney(value: number): string {
  return `${formatNumber(value)} грн`
}

export function formatBucket(value: string, groupBy: GroupBy): string {
  const date = parseIsoDate(value)
  if (!date) return value
  return (groupBy === 'month' ? monthFormat : dayFormat).format(date)
}

export function formatFullDate(value: string): string {
  const date = parseIsoDate(value)
  return date ? fullDateFormat.format(date) : value
}

export function statusLabel(value: string): string {
  return isPaymentStatus(value) ? PAYMENT_STATUS[value].label : value
}

export function formatCell(key: string, value: ReportCell, groupBy: GroupBy): string {
  if (value === null || value === '') return '—'
  if (typeof value === 'number') return formatNumber(value)
  if (key === 'bucket') return formatBucket(value, groupBy)
  if (key === 'status') return statusLabel(value)
  return value
}
