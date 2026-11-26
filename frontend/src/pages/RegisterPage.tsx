import { useMutation } from '@tanstack/react-query'
import type { FormEvent } from 'react'
import { Link, useLocation } from 'react-router-dom'
import { errorMessage } from '../api/errors'
import { useAuth } from '../auth/useAuth'
import { hasErrors, validateRegister, type RegisterValues } from '../auth/validation'
import AuthCard from '../components/AuthCard'
import FormAlert from '../components/FormAlert'
import FormField from '../components/FormField'
import { buttonPrimary, textLink } from '../components/ui'
import { useFormState } from '../components/useFormState'
import { useDocumentTitle } from '../hooks/useDocumentTitle'

const initialValues: RegisterValues = { email: '', display_name: '', password: '', confirm_password: '' }

export default function RegisterPage() {
  useDocumentTitle('Реєстрація')
  const { register } = useAuth()
  const location = useLocation()
  const form = useFormState(initialValues)
  const mutation = useMutation({ mutationFn: register, onError: form.applyServerErrors })

  const handleSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    const errors = validateRegister(form.values)
    form.setErrors(errors)
    if (hasErrors(errors)) return
    mutation.mutate({
      email: form.values.email.trim(),
      password: form.values.password,
      display_name: form.values.display_name.trim() || undefined,
    })
  }

  return (
    <AuthCard
      title="Реєстрація"
      subtitle="Створіть акаунт — безкоштовний план доступний одразу"
      footer={
        <>
          Вже маєте акаунт?{' '}
          <Link to="/login" state={location.state} className={textLink}>
            Увійти
          </Link>
        </>
      }
    >
      <form noValidate onSubmit={handleSubmit} className="space-y-4">
        {mutation.isError && <FormAlert>{errorMessage(mutation.error)}</FormAlert>}
        <FormField label="Електронна пошта" type="email" autoComplete="email" {...form.bind('email')} />
        <FormField
          label="Імʼя"
          autoComplete="nickname"
          hint="Необовʼязково, за замовчуванням — частина адреси пошти"
          {...form.bind('display_name')}
        />
        <FormField
          label="Пароль"
          type="password"
          autoComplete="new-password"
          hint="Щонайменше 8 символів"
          {...form.bind('password')}
        />
        <FormField
          label="Повторіть пароль"
          type="password"
          autoComplete="new-password"
          {...form.bind('confirm_password')}
        />
        <button type="submit" disabled={mutation.isPending} className={`${buttonPrimary} w-full`}>
          {mutation.isPending ? 'Створення…' : 'Зареєструватися'}
        </button>
      </form>
    </AuthCard>
  )
}
