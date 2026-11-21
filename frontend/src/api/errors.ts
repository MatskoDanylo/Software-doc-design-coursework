import { ApiError } from './client'

const MESSAGES: Record<string, string> = {
  email_taken: 'Користувач з таким email уже зареєстрований',
  invalid_credentials: 'Невірний email або пароль',
  invalid_token: 'Сесія завершилась, увійдіть знову',
  unauthorized: 'Потрібно увійти в акаунт',
  forbidden: 'Недостатньо прав',
  validation_error: 'Перевірте правильність заповнення полів',
  network_error: 'Сервер недоступний. Перевірте, чи запущено бекенд',
}

export function errorMessage(error: unknown): string {
  if (error instanceof ApiError) return MESSAGES[error.code] ?? error.message
  return 'Сталася невідома помилка'
}

export function serverFieldErrors(error: unknown): Record<string, string> {
  if (!(error instanceof ApiError) || error.code !== 'validation_error') return {}
  return Object.fromEntries(error.details.map((detail) => [String(detail.loc.at(-1)), detail.msg]))
}
