import { Navigate, useLocation } from 'react-router-dom'
import type { RedirectState } from './redirect'

export default function RedirectToLogin() {
  const location = useLocation()
  const state: RedirectState = { from: `${location.pathname}${location.search}` }
  return <Navigate to="/login" replace state={state} />
}
