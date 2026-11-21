import { useMutation } from '@tanstack/react-query'
import type { FormEvent } from 'react'
import { errorMessage } from '../api/errors'
import { usersApi } from '../api/users'
import { hasErrors, validateProfile, type ProfileValues } from '../auth/validation'
import type { ProfileUpdate, User } from '../types/user'
import FormAlert from './FormAlert'
import FormField from './FormField'
import { buttonPrimary, card } from './ui'
import { useFormState } from './useFormState'

interface ProfileFormProps {
  user: User
  onSaved: (user: User) => void
}

function toProfileUpdate(values: ProfileValues): ProfileUpdate {
  return {
    display_name: values.display_name.trim(),
    avatar_url: values.avatar_url.trim() || null,
    country: values.country.trim() || null,
  }
}

export default function ProfileForm({ user, onSaved }: ProfileFormProps) {
  const form = useFormState<ProfileValues>({
    display_name: user.profile.display_name,
    avatar_url: user.profile.avatar_url ?? '',
    country: user.profile.country ?? '',
  })
  const mutation = useMutation({
    mutationFn: usersApi.updateMe,
    onSuccess: onSaved,
    onError: form.applyServerErrors,
  })

  const handleSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    const errors = validateProfile(form.values)
    form.setErrors(errors)
    if (hasErrors(errors)) return
    mutation.mutate(toProfileUpdate(form.values))
  }

  return (
    <section className={card}>
      <h2 className="font-display text-xl font-semibold">Редагування профілю</h2>
      <form noValidate onSubmit={handleSubmit} className="mt-6 space-y-4">
        {mutation.isError && <FormAlert>{errorMessage(mutation.error)}</FormAlert>}
        {mutation.isSuccess && <FormAlert tone="success">Зміни збережено</FormAlert>}
        <FormField label="Імʼя" autoComplete="nickname" {...form.bind('display_name')} />
        <FormField
          label="Посилання на аватар"
          type="url"
          placeholder="https://…"
          hint="Залиште порожнім, щоб прибрати аватар"
          {...form.bind('avatar_url')}
        />
        <FormField label="Країна" autoComplete="country-name" {...form.bind('country')} />
        <button type="submit" disabled={mutation.isPending} className={buttonPrimary}>
          {mutation.isPending ? 'Збереження…' : 'Зберегти'}
        </button>
      </form>
    </section>
  )
}
