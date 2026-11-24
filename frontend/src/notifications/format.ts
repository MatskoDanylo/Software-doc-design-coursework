const dateTimeFormat = new Intl.DateTimeFormat('uk-UA', { dateStyle: 'medium', timeStyle: 'short' })

export function formatDateTime(iso: string): string {
  return dateTimeFormat.format(new Date(iso))
}
