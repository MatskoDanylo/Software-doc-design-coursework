export function sentence(text: string): string {
  return text.endsWith('.') ? text : `${text}.`
}
