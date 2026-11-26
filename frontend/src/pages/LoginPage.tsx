import { useMutation } from '@tanstack/react-query'
import type { FormEvent } from 'react'
import { Link, useLocation } from 'react-router-dom'
import { errorMessage } from '../api/errors'
import { useAuth } from '../auth/useAuth'
import { hasErrors, validateLogin, type LoginValues } from '../auth/validation'
import AuthCard from '../components/AuthCard'
import FormAlert from '../components/FormAlert'
import FormField from '../components/FormField'
import { buttonPrimary, textLink } from '../components/ui'
import { useFormState } from '../components/useFormState'
import { useDocumentTitle } from '../hooks/useDocumentTitle'

const initialValues: LoginValues = { email: '', password: '' }

export default function LoginPage() {
  useDocumentTitle('Вхід')
  const { login } = useAuth()
  const location = useLocation()
  const form = useFormState(initialValues)
  const mutation = useMutation({ mutationFn: login, onError: form.applyServerErrors })

  const handleSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    const errors = validateLogin(form.values)
    form.setErrors(errors)
    if (hasErrors(errors)) return
    mutation.mutate({ email: form.values.email.trim(), password: form.values.password })
  }

  return (
    <AuthCard
      title="Вхід"
      subtitle="Увійдіть, щоб дивитися фільми та серіали"
      footer={
        <>
          Немає акаунта?{' '}
          <Link to="/register" state={location.state} className={textLink}>
            Зареєструватися
          </Link>
        </>
      }
    >
      <form noValidate onSubmit={handleSubmit} className="space-y-4">
        {mutation.isError && <FormAlert>{errorMessage(mutation.error)}</FormAlert>}
        <FormField label="Електронна пошта" type="email" autoComplete="email" {...form.bind('email')} />
        <FormField label="Пароль" type="password" autoComplete="current-password" {...form.bind('password')} />
        <button type="submit" disabled={mutation.isPending} className={`${buttonPrimary} w-full`}>
          {mutation.isPending ? 'Вхід…' : 'Увійти'}
        </button>
      </form>
    </AuthCard>
  )
}
