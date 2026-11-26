import { ApiError } from './client'

const MESSAGES: Record<string, string> = {
  email_taken: 'Користувач з такою електронною поштою вже зареєстрований',
  invalid_credentials: 'Невірна електронна пошта або пароль',
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
  plan_not_found: 'Такого тарифу не існує',
  unknown_plan: 'Такого тарифу не існує',
  plan_not_purchasable: 'Цей тариф не потрібно купувати',
  plan_change_not_allowed: 'Перейти на цей тариф з поточного не можна',
  payment_not_found: 'Платіж не знайдено',
  payment_finalized: 'Цей платіж уже завершено',
  payment_not_pending: 'Платіж уже не очікує підтвердження',
  mock_payments_disabled: 'Тестова оплата вимкнена на сервері',
  payment_gateway_error: 'Платіжний шлюз недоступний. Спробуйте пізніше',
  gateway_payment_not_found: 'Платіжний шлюз не знайшов цей платіж',
  gateway_state_conflict: 'Платіжний шлюз уже завершив цей платіж',
  no_active_subscription: 'Активної підписки немає',
  invalid_duration: 'Тривалість підписки має бути щонайменше 1 день',
  notification_not_found: 'Сповіщення не знайдено',
  user_not_found: 'Користувача не знайдено',
  unknown_report: 'Такого звіту не існує',
  invalid_period: 'Початок періоду не може бути пізніше за кінець',
  period_too_long: 'Період задовгий. Для понад рік оберіть групування по місяцях',
  unknown_strategy: 'Невідома стратегія рекомендацій',
  unknown_timezone: 'Невідомий часовий пояс',
  invalid_query: 'Некоректні параметри пошуку',
  invalid_outcome: 'Очікуваний платіж можна лише підтвердити або відхилити',
  not_a_movie: 'Для серіалу відео завантажується до кожного епізоду',
  video_asset_not_found: 'Відеофайл не знайдено',
  video_processing: 'Попереднє відео ще обробляється. Дочекайтесь завершення',
  conflict: 'Дію не виконано: дані вже змінилися. Оновіть сторінку',
  unprocessable: 'Сервер не може обробити ці дані',
  bad_gateway: 'Зовнішній сервіс недоступний. Спробуйте пізніше',
}

function fallbackMessage(status: number): string {
  if (status >= 500) return 'Помилка на сервері. Спробуйте пізніше'
  if (status === 404) return MESSAGES.not_found
  return 'Запит не виконано. Перевірте дані й спробуйте ще раз'
}

export function errorMessage(error: unknown): string {
  if (error instanceof ApiError) return MESSAGES[error.code] ?? fallbackMessage(error.status)
  return 'Сталася невідома помилка'
}

export function serverFieldErrors(error: unknown): Record<string, string> {
  if (!(error instanceof ApiError) || error.code !== 'validation_error') return {}
  return Object.fromEntries(error.details.map((detail) => [String(detail.loc.at(-1)), detail.msg]))
}
