import { ApiError } from './client'

const MESSAGES: Record<string, string> = {
  email_taken: 'Користувач з таким email уже зареєстрований',
  invalid_credentials: 'Невірний email або пароль',
  invalid_token: 'Сесія завершилась, увійдіть знову',
  unauthorized: 'Потрібно увійти в акаунт',
  forbidden: 'Недостатньо прав',
  validation_error: 'Перевірте правильність заповнення полів',
  network_error: 'Сервер недоступний. Перевірте, чи запущено бекенд',
  not_found: 'Не знайдено',
  title_not_found: 'Тайтл не знайдено',
  genre_not_found: 'Жанр не знайдено',
  season_not_found: 'Сезон не знайдено',
  episode_not_found: 'Епізод не знайдено',
  title_exists: 'Тайтл з таким типом, назвою і роком уже існує',
  genre_exists: 'Жанр з такою назвою вже існує',
  season_exists: 'Сезон з таким номером уже існує',
  episode_exists: 'Епізод з таким номером уже існує',
  not_a_series: 'Сезони можна додавати лише до серіалів',
  title_has_seasons: 'Серіал із сезонами не можна змінити на фільм. Спершу видаліть сезони',
  unknown_genre: 'Один із жанрів більше не існує. Оновіть сторінку',
  payload_too_large: 'Файл завеликий: максимум 5 МБ',
  unsupported_media_type: 'Постер має бути у форматі JPEG, PNG або WebP',
  video_not_ready: 'Відео для цього тайтлу ще не готове',
  video_not_found: 'Відео не знайдено',
  quality_not_available: 'Для вашого плану немає доступної якості відео',
  episode_required: 'Оберіть епізод серіалу',
  episode_not_allowed: 'У фільму немає епізодів',
}

export function errorMessage(error: unknown): string {
  if (error instanceof ApiError) return MESSAGES[error.code] ?? error.message
  return 'Сталася невідома помилка'
}

export function serverFieldErrors(error: unknown): Record<string, string> {
  if (!(error instanceof ApiError) || error.code !== 'validation_error') return {}
  return Object.fromEntries(error.details.map((detail) => [String(detail.loc.at(-1)), detail.msg]))
}
