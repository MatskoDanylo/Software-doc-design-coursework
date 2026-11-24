import { useState } from 'react'
import { useChangeSubscription } from '../../../admin/billing'
import { errorMessage } from '../../../api/errors'
import { usePlan } from '../../../billing/queries'
import { formatDate } from '../../../format/datetime'
import type { Account, Subscription } from '../../../types/user'
import { buttonPrimary, buttonSmall, controlClass } from '../../ui'
import ConfirmButton from '../ConfirmButton'

const MAX_DAYS = 3650

function parseDays(value: string): number | undefined | null {
  if (value.trim() === '') return undefined
  const days = Number(value)
  return Number.isInteger(days) && days >= 1 && days <= MAX_DAYS ? days : null
}

function resultText(subscription: Subscription): string {
  if (subscription.plan_code === 'free' || !subscription.expires_at) return 'Premium забрано, діє Free'
  return `Premium до ${formatDate(subscription.expires_at)}`
}

export default function PremiumControls({ user }: { user: Account }) {
  const change = useChangeSubscription(user.id)
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
          aria-label={`Днів Premium для ${user.email}`}
          aria-invalid={parsed === null ? true : undefined}
          className={`${controlClass(parsed === null)} w-20 py-1.5`}
        />
        <button
          type="button"
          className={`${buttonPrimary} ${buttonSmall}`}
          disabled={change.isPending || parsed === null}
          onClick={() => change.mutate({ action: 'grant', days: parsed ?? undefined })}
        >
          Видати Premium
        </button>
        <ConfirmButton
          label="Забрати Premium"
          question={`Забрати Premium у ${user.email}?`}
          confirmLabel="Так, забрати"
          pendingLabel="Збереження…"
          dismissLabel="Ні"
          pending={change.isPending}
          onConfirm={() => change.mutate({ action: 'revoke' })}
        />
      </div>
      {parsed === null && <p className="text-xs text-danger">Від 1 до {MAX_DAYS} днів</p>}
      {change.isError && <p className="text-xs text-danger">{errorMessage(change.error)}</p>}
      {change.isSuccess && (
        <p role="status" className="text-xs text-emerald-300">
          {resultText(change.data)}
        </p>
      )}
    </div>
  )
}
