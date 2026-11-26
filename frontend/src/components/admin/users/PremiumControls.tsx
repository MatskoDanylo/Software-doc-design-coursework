import { useState } from 'react'
import { useChangeSubscription } from '../../../admin/billing'
import { usePlan } from '../../../billing/queries'
import type { Account } from '../../../types/user'
import { buttonPrimary, buttonSmall, controlClass } from '../../ui'
import ConfirmButton from '../ConfirmButton'

const MAX_DAYS = 3650

function parseDays(value: string): number | undefined | null {
  if (value.trim() === '') return undefined
  const days = Number(value)
  return Number.isInteger(days) && days >= 1 && days <= MAX_DAYS ? days : null
}

export default function PremiumControls({ user }: { user: Account }) {
  const change = useChangeSubscription(user)
  const premium = usePlan('premium')
  const [days, setDays] = useState('')
  const parsed = parseDays(days)

  return (
    <div className="flex flex-col items-end gap-1">
      <div className="flex flex-wrap items-center justify-end gap-2">
        <input
          type="number"
          min={1}
          max={MAX_DAYS}
          inputMode="numeric"
          value={days}
          placeholder={String(premium?.duration_days ?? 30)}
          onChange={(event) => setDays(event.target.value)}
          aria-label={`Днів Преміуму для ${user.email}`}
          aria-invalid={parsed === null ? true : undefined}
          className={`${controlClass(parsed === null)} w-20 py-1.5`}
        />
        <button
          type="button"
          className={`${buttonPrimary} ${buttonSmall}`}
          disabled={change.isPending || parsed === null}
          onClick={() => change.mutate({ action: 'grant', days: parsed ?? undefined })}
        >
          Видати Преміум
        </button>
        <ConfirmButton
          label="Забрати Преміум"
          question={`Забрати Преміум у ${user.email}?`}
          confirmLabel="Так, забрати"
          pendingLabel="Збереження…"
          dismissLabel="Ні"
          pending={change.isPending}
          onConfirm={() => change.mutate({ action: 'revoke' })}
        />
      </div>
      {parsed === null && <p className="text-xs text-danger">Від 1 до {MAX_DAYS} днів</p>}
    </div>
  )
}
