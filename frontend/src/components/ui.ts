const base =
  'inline-flex items-center justify-center gap-2 rounded-lg px-4 py-2 text-sm font-medium transition-colors focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-gold disabled:cursor-not-allowed disabled:opacity-50'

export const buttonPrimary = `${base} bg-gold text-screen hover:bg-gold-strong`
export const buttonGhost = `${base} text-zinc-200 hover:bg-surface-raised`
export const buttonOutline = `${base} border border-line text-zinc-200 hover:border-gold hover:text-gold`
