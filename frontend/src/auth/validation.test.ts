import { describe, expect, it } from 'vitest'
import { hasErrors, validateLogin, validateProfile, validateRegister } from './validation'

const validRegistration = {
  email: 'viewer@example.com',
  display_name: 'Viewer',
  password: 'password123',
  confirm_password: 'password123',
}

describe('validateLogin', () => {
  it('requires email and password', () => {
    expect(validateLogin({ email: ' ', password: '' })).toEqual({
      email: 'Вкажіть електронну пошту',
      password: 'Вкажіть пароль',
    })
  })

  it('accepts a trimmed valid email', () => {
    expect(hasErrors(validateLogin({ email: '  viewer@example.com ', password: 'x' }))).toBe(false)
  })
})

describe('validateRegister', () => {
  it('accepts valid data', () => {
    expect(hasErrors(validateRegister(validRegistration))).toBe(false)
  })

  it.each([
    [{ email: 'viewer@example' }, 'email', 'Некоректна адреса електронної пошти'],
    [{ display_name: 'x'.repeat(101) }, 'display_name', 'Максимум 100 символів'],
    [{ password: 'short', confirm_password: 'short' }, 'password', 'Мінімум 8 символів'],
    [{ password: 'ї'.repeat(37), confirm_password: 'ї'.repeat(37) }, 'password', 'Пароль задовгий'],
    [{ confirm_password: 'password124' }, 'confirm_password', 'Паролі не збігаються'],
  ])('rejects %o', (change, field, message) => {
    expect(validateRegister({ ...validRegistration, ...change })).toMatchObject({ [field]: message })
  })
})

describe('validateProfile', () => {
  const profile = { display_name: 'Viewer', avatar_url: '', country: 'Україна' }

  it('accepts an empty avatar and an https link', () => {
    expect(hasErrors(validateProfile(profile))).toBe(false)
    expect(hasErrors(validateProfile({ ...profile, avatar_url: 'https://example.com/a.png' }))).toBe(false)
  })

  it('requires a name', () => {
    expect(validateProfile({ ...profile, display_name: '  ' }).display_name).toBe('Вкажіть імʼя')
  })

  it.each(['ftp://example.com/a.png', 'not a url', `https://example.com/${'a'.repeat(500)}`])(
    'rejects avatar %s',
    (avatar_url) => {
      expect(validateProfile({ ...profile, avatar_url }).avatar_url).toBeDefined()
    },
  )

  it('limits the country length', () => {
    expect(validateProfile({ ...profile, country: 'x'.repeat(101) }).country).toBe('Максимум 100 символів')
  })
})
