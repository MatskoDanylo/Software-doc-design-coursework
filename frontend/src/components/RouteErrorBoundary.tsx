import { Component, type ErrorInfo, type ReactNode } from 'react'
import { Link } from 'react-router-dom'
import StateMessage from './StateMessage'
import { buttonOutline, buttonPrimary } from './ui'

interface RouteErrorBoundaryProps {
  children: ReactNode
}

interface RouteErrorBoundaryState {
  error: Error | null
}

function isChunkLoadError(error: Error): boolean {
  return /dynamically imported module|Importing a module script failed|Failed to fetch/i.test(error.message)
}

/** Catches render errors of a page so the header and navigation keep working. Reset by remounting with a new key. */
export default class RouteErrorBoundary extends Component<RouteErrorBoundaryProps, RouteErrorBoundaryState> {
  state: RouteErrorBoundaryState = { error: null }

  static getDerivedStateFromError(error: Error): RouteErrorBoundaryState {
    return { error }
  }

  componentDidCatch(error: Error, info: ErrorInfo): void {
    console.error('Page crashed', error, info.componentStack)
  }

  render() {
    const { error } = this.state
    if (!error) return this.props.children

    const text = isChunkLoadError(error)
      ? 'Не вдалося завантажити частину застосунку. Можливо, вийшла нова версія — оновіть сторінку.'
      : 'Під час показу сторінки сталася помилка. Спробуйте оновити сторінку або поверніться на головну.'
    return (
      <StateMessage
        tone="error"
        title="Щось пішло не так"
        text={text}
        action={
          <div className="flex flex-wrap justify-center gap-3">
            <button type="button" className={buttonPrimary} onClick={() => window.location.reload()}>
              Оновити сторінку
            </button>
            <Link to="/" className={buttonOutline}>
              На головну
            </Link>
          </div>
        }
      />
    )
  }
}
