import { useCallback, useEffect, useRef } from 'react'

export function useDebouncedCallback<A extends unknown[]>(callback: (...args: A) => void, delay: number) {
  const callbackRef = useRef(callback)
  const timerRef = useRef<ReturnType<typeof setTimeout> | undefined>(undefined)

  useEffect(() => {
    callbackRef.current = callback
  })

  useEffect(() => () => clearTimeout(timerRef.current), [])

  return useCallback(
    (...args: A) => {
      clearTimeout(timerRef.current)
      timerRef.current = setTimeout(() => callbackRef.current(...args), delay)
    },
    [delay],
  )
}
