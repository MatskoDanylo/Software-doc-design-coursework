import { describe, expect, it } from 'vitest'
import { ApiError } from './client'
import { errorMessage, serverFieldErrors } from './errors'

describe('errorMessage', () => {
  it('translates known error codes', () => {
    expect(errorMessage(new ApiError(401, 'invalid_credentials', 'Invalid credentials'))).toBe(
      'Невірна електронна пошта або пароль',
    )
  })

  it('never shows raw English server messages for unknown codes', () => {
    expect(errorMessage(new ApiError(500, 'something_new', 'Internal error'))).toBe('Помилка на сервері. Спробуйте пізніше')
    expect(errorMessage(new ApiError(404, 'gone', 'Gone'))).toBe('Не знайдено')
    expect(errorMessage(new ApiError(400, 'http_error', 'Bad Request'))).toBe(
      'Запит не виконано. Перевірте дані й спробуйте ще раз',
    )
  })

  it('hides non-API errors behind a generic message', () => {
    expect(errorMessage(new Error('boom'))).toBe('Сталася невідома помилка')
  })
})

describe('serverFieldErrors', () => {
  it('maps validation details to form fields by the last location segment', () => {
    const error = new ApiError(422, 'validation_error', 'invalid', [
      { loc: ['body', 'email'], msg: 'value is not a valid email address', type: 'value_error' },
      { loc: ['body', 'profile', 'country'], msg: 'too long', type: 'string_too_long' },
    ])

    expect(serverFieldErrors(error)).toEqual({ email: 'value is not a valid email address', country: 'too long' })
  })

  it('ignores errors that are not validation errors', () => {
    expect(serverFieldErrors(new ApiError(409, 'email_taken', 'taken'))).toEqual({})
    expect(serverFieldErrors(new Error('boom'))).toEqual({})
  })
})
