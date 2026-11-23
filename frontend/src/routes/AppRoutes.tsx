import { lazy, Suspense } from 'react'
import { Route, Routes } from 'react-router-dom'
import AdminLayout from '../components/admin/AdminLayout'
import Layout from '../components/Layout'
import PageLoader from '../components/PageLoader'
import AdminGenresPage from '../pages/admin/AdminGenresPage'
import AdminTitleCreatePage from '../pages/admin/AdminTitleCreatePage'
import AdminTitleEditPage from '../pages/admin/AdminTitleEditPage'
import AdminTitlesPage from '../pages/admin/AdminTitlesPage'
import AdminPage from '../pages/AdminPage'
import CatalogPage from '../pages/CatalogPage'
import HomePage from '../pages/HomePage'
import LoginPage from '../pages/LoginPage'
import NotFoundPage from '../pages/NotFoundPage'
import PricingPage from '../pages/PricingPage'
import ProfilePage from '../pages/ProfilePage'
import RegisterPage from '../pages/RegisterPage'
import TitleDetailsPage from '../pages/TitleDetailsPage'
import AdminRoute from './AdminRoute'
import GuestRoute from './GuestRoute'
import ProtectedRoute from './ProtectedRoute'

const WatchPage = lazy(() => import('../pages/WatchPage'))

export default function AppRoutes() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route index element={<HomePage />} />
        <Route path="catalog" element={<CatalogPage />} />
        <Route path="titles/:id" element={<TitleDetailsPage />} />
        <Route path="pricing" element={<PricingPage />} />
        <Route element={<GuestRoute />}>
          <Route path="login" element={<LoginPage />} />
          <Route path="register" element={<RegisterPage />} />
        </Route>
        <Route element={<ProtectedRoute />}>
          <Route path="profile" element={<ProfilePage />} />
          <Route
            path="watch/:titleId"
            element={
              <Suspense fallback={<PageLoader />}>
                <WatchPage />
              </Suspense>
            }
          />
        </Route>
        <Route element={<AdminRoute />}>
          <Route path="admin" element={<AdminLayout />}>
            <Route index element={<AdminPage />} />
            <Route path="titles" element={<AdminTitlesPage />} />
            <Route path="titles/new" element={<AdminTitleCreatePage />} />
            <Route path="titles/:id" element={<AdminTitleEditPage />} />
            <Route path="genres" element={<AdminGenresPage />} />
          </Route>
        </Route>
        <Route path="*" element={<NotFoundPage />} />
      </Route>
    </Routes>
  )
}
