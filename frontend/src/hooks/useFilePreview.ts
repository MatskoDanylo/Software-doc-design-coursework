import { useCallback, useEffect, useRef, useState } from 'react'

interface Preview {
  file: File
  url: string
}

export function useFilePreview(file: File | null) {
  const [preview, setPreview] = useState<Preview | null>(null)
  const urlRef = useRef<string | null>(null)

  useEffect(
    () => () => {
      if (urlRef.current) URL.revokeObjectURL(urlRef.current)
    },
    [],
  )

  const show = useCallback((next: File) => {
    if (urlRef.current) URL.revokeObjectURL(urlRef.current)
    urlRef.current = URL.createObjectURL(next)
    setPreview({ file: next, url: urlRef.current })
  }, [])

  return { url: preview && preview.file === file ? preview.url : null, show }
}
