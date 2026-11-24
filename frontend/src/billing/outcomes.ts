import type { PaymentOutcome } from '../types/billing'

export interface OutcomeOption {
  value: PaymentOutcome
  label: string
  description: string
}

export const OUTCOMES: OutcomeOption[] = [
  {
    value: 'success',
    label: 'Успішна оплата',
    description: 'Банк одразу підтверджує платіж, Premium активується миттєво.',
  },
  {
    value: 'pending',
    label: 'Очікує підтвердження',
    description: 'Банк ще перевіряє платіж. Підписка не зміниться, доки оплату не підтвердять або не відхилять.',
  },
  {
    value: 'failed',
    label: 'Відхилено банком',
    description: 'Гроші не списано, підписка не зміниться. Можна спробувати ще раз.',
  },
]
