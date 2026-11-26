import type { StreamError as StreamErrorKind } from '../../player/useHlsStream'
import { buttonOutline } from '../ui'

const MESSAGES: Record<StreamErrorKind, string> = {
  unsupported: 'Браузер не підтримує відтворення HLS. Спробуйте Chrome, Firefox, Edge або Safari',
  playback: 'Не вдалося завантажити відео. Перевірте з’єднання і спробуйте ще раз',
}

export default function StreamError({ kind, onRetry }: { kind: StreamErrorKind; onRetry: () => void }) {
  return (
    <div role="alert" className="absolute inset-0 flex flex-col items-center justify-center gap-4 bg-black/85 p-6 text-center">
      <p className="max-w-md text-sm text-zinc-200">{MESSAGES[kind]}</p>
      {kind === 'playback' && (
        <button type="button" className={buttonOutline} onClick={onRetry}>
          Спробувати ще раз
        </button>
      )}
    </div>
  )
}
