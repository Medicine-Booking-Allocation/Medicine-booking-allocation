import { Navigate, useLocation } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth'
import { dashboardPathForRole } from '../utils/constants'

/*
 * Route guard. Requires a logged-in user; optionally requires a specific role.
 *   - No user            → /login (with return path in state.from)
 *   - User, wrong role   → their own dashboard
 * `roles` is optional; omit it for a role-agnostic protected route.
 */
export default function ProtectedRoute({ roles, children }) {
  const { user } = useAuth()
  const location = useLocation()

  if (!user) {
    return <Navigate to="/login" state={{ from: location.pathname }} replace />
  }
  if (roles && !roles.includes(user.role)) {
    return <Navigate to={dashboardPathForRole(user.role)} replace />
  }
  return children
}
