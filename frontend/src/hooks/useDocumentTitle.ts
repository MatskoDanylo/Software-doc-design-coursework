import { useEffect } from 'react'

export const APP_NAME = 'Cinema Platform'

export function pageTitle(title?: string | null): string {
  return title ? `${title} · ${APP_NAME}` : APP_NAME
}

/** Sets the browser tab title; pass null while the page data is still loading. */
export function useDocumentTitle(title: string | null | undefined): void {
  useEffect(() => {
    document.title = pageTitle(title)
  }, [title])
}
