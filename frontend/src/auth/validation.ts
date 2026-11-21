export type FieldErrors<F extends string> = Partial<Record<F, string>>

export type LoginValues = { email: string; password: string }
export type RegisterValues = { email: string; display_name: string; password: string; confirm_password: string }
export type ProfileValues = { display_name: string; avatar_url: string; country: string }

const EMAIL_PATTERN = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
const PASSWORD_MIN_LENGTH = 8
const PASSWORD_MAX_BYTES = 72
const NAME_MAX_LENGTH = 100
const URL_MAX_LENGTH = 500
const URL_FORMAT_ERROR = 'Вкажіть посилання у форматі https://…'

function emailError(value: string): string | undefined {
  const email = value.trim()
  if (!email) return 'Вкажіть email'
  if (!EMAIL_PATTERN.test(email)) return 'Некоректний email'
  return undefined
}

function newPasswordError(value: string): string | undefined {
  if (value.length < PASSWORD_MIN_LENGTH) return `Мінімум ${PASSWORD_MIN_LENGTH} символів`
  if (new TextEncoder().encode(value).length > PASSWORD_MAX_BYTES) return 'Пароль задовгий'
  return undefined
}

function maxLengthError(value: string, max: number): string | undefined {
  return value.trim().length > max ? `Максимум ${max} символів` : undefined
}

function isHttpUrl(value: string): boolean {
  try {
    const { protocol } = new URL(value)
    return protocol === 'http:' || protocol === 'https:'
  } catch {
    return false
  }
}

function urlError(value: string): string | undefined {
  const url = value.trim()
  if (!url) return undefined
  if (url.length > URL_MAX_LENGTH) return `Максимум ${URL_MAX_LENGTH} символів`
  return isHttpUrl(url) ? undefined : URL_FORMAT_ERROR
}

export function hasErrors(errors: FieldErrors<string>): boolean {
  return Object.values(errors).some(Boolean)
}

export function validateLogin(values: LoginValues): FieldErrors<keyof LoginValues> {
  return {
    email: emailError(values.email),
    password: values.password ? undefined : 'Вкажіть пароль',
  }
}

export function validateRegister(values: RegisterValues): FieldErrors<keyof RegisterValues> {
  return {
    email: emailError(values.email),
    display_name: maxLengthError(values.display_name, NAME_MAX_LENGTH),
    password: newPasswordError(values.password),
    confirm_password: values.confirm_password === values.password ? undefined : 'Паролі не збігаються',
  }
}

export function validateProfile(values: ProfileValues): FieldErrors<keyof ProfileValues> {
  return {
    display_name: values.display_name.trim() ? maxLengthError(values.display_name, NAME_MAX_LENGTH) : 'Вкажіть імʼя',
    avatar_url: urlError(values.avatar_url),
    country: maxLengthError(values.country, NAME_MAX_LENGTH),
  }
}
