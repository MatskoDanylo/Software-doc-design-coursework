const base =
  'inline-flex items-center justify-center gap-2 rounded-lg px-4 py-2 text-sm font-medium transition-colors focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-gold disabled:cursor-not-allowed disabled:opacity-50'

export const buttonPrimary = `${base} bg-gold text-screen hover:bg-gold-strong`
export const buttonGhost = `${base} text-zinc-200 hover:bg-surface-raised`
export const buttonOutline = `${base} border border-line text-zinc-200 hover:border-gold hover:text-gold`
export const buttonDanger = `${base} border border-danger/50 text-danger hover:bg-danger/10`
export const buttonSmall = 'px-3 py-1.5 text-xs'
export const textLink = 'font-medium text-gold hover:text-gold-strong'
export const card = 'rounded-2xl border border-line bg-surface p-6 sm:p-8'

const controlBase =
  'w-full rounded-lg border bg-screen px-3 py-2 text-sm text-zinc-100 placeholder:text-zinc-600 focus:ring-2 focus:outline-none'

export function controlClass(invalid = false): string {
  const state = invalid ? 'border-danger focus:ring-danger/40' : 'border-line focus:border-gold focus:ring-gold/30'
  return `${controlBase} ${state}`
}

export const labelClass = 'block text-sm font-medium text-zinc-300'

export function chipClass(active: boolean): string {
  const state = active
    ? 'border-gold bg-gold/15 text-gold'
    : 'border-line text-zinc-300 hover:border-zinc-500 hover:text-zinc-100'
  return `rounded-full border px-3 py-1 text-xs font-medium transition-colors focus-visible:outline-2 focus-visible:outline-gold ${state}`
}
