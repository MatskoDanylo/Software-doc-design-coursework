import { Outlet } from 'react-router-dom'
import Header from './Header'

const currentYear = new Date().getFullYear()

export default function Layout() {
  return (
    <div className="flex min-h-screen flex-col">
      <Header user={null} onLogout={() => undefined} />
      <main className="mx-auto w-full max-w-6xl flex-1 px-4 py-10">
        <Outlet />
      </main>
      <footer className="border-t border-line py-6 text-center text-xs text-muted">
        Cinema Platform · {currentYear}
      </footer>
    </div>
  )
}
