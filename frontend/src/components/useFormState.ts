import { useState, type ChangeEvent } from 'react'
import { serverFieldErrors } from '../api/errors'
import type { FieldErrors } from '../auth/validation'

export function useFormState<T extends Record<string, string>>(initial: T) {
  type Field = keyof T & string
  const [values, setValues] = useState<T>(initial)
  const [errors, setErrors] = useState<FieldErrors<Field>>({})

  const isField = (name: string): name is Field => Object.hasOwn(initial, name)

  const bind = (name: Field) => ({
    name,
    value: values[name],
    error: errors[name],
    onChange: (event: ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => {
      const { value } = event.target
      setValues((current) => ({ ...current, [name]: value }))
      setErrors((current) => ({ ...current, [name]: undefined }))
    },
  })

  const applyServerErrors = (error: unknown) => {
    let next: FieldErrors<Field> = {}
    for (const [name, message] of Object.entries(serverFieldErrors(error))) {
      if (isField(name)) next = { ...next, [name]: message }
    }
    setErrors(next)
  }

  return { values, setErrors, bind, applyServerErrors }
}
