import { isPaymentStatus, PAYMENT_STATUS } from '../../../billing/statuses'
import type { PaymentStatus } from '../../../types/billing'
import SelectField, { type SelectOption } from '../../SelectField'

const OPTIONS: SelectOption[] = [
  { value: '', label: 'Усі статуси' },
  ...Object.entries(PAYMENT_STATUS).map(([value, { label }]) => ({ value, label })),
]

interface PaymentStatusFilterProps {
  value: PaymentStatus | null
  onChange: (status: PaymentStatus | null) => void
}

export default function PaymentStatusFilter({ value, onChange }: PaymentStatusFilterProps) {
  return (
    <SelectField
      label="Статус"
      options={OPTIONS}
      value={value ?? ''}
      onChange={(event) => onChange(isPaymentStatus(event.target.value) ? event.target.value : null)}
    />
  )
}
