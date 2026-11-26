export type ToastTone = 'success' | 'error'

export interface Toast {
  id: number
  tone: ToastTone
  text: string
}

export const TOAST_DURATION_MS: Record<ToastTone, number> = { success: 4000, error: 7000 }
const MAX_TOASTS = 4

let toasts: Toast[] = []
let nextId = 1
const listeners = new Set<() => void>()
const timers = new Map<number, ReturnType<typeof setTimeout>>()

function emit(): void {
  for (const listener of listeners) listener()
}

export function dismissToast(id: number): void {
  clearTimeout(timers.get(id))
  timers.delete(id)
  const next = toasts.filter((toast) => toast.id !== id)
  if (next.length === toasts.length) return
  toasts = next
  emit()
}

function show(tone: ToastTone, text: string): number {
  const duplicate = toasts.find((toast) => toast.tone === tone && toast.text === text)
  if (duplicate) dismissToast(duplicate.id)
  while (toasts.length >= MAX_TOASTS) dismissToast(toasts[0].id)

  const id = nextId++
  toasts = [...toasts, { id, tone, text }]
  timers.set(
    id,
    setTimeout(() => dismissToast(id), TOAST_DURATION_MS[tone]),
  )
  emit()
  return id
}

export const toast = {
  success: (text: string) => show('success', text),
  error: (text: string) => show('error', text),
}

export function subscribeToasts(listener: () => void): () => void {
  listeners.add(listener)
  return () => listeners.delete(listener)
}

export function getToasts(): Toast[] {
  return toasts
}

export function clearToasts(): void {
  for (const id of [...timers.keys()]) dismissToast(id)
}
