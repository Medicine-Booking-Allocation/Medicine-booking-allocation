import ProtectedRoute from './ProtectedRoute'

/*
 * Convenience wrapper around <ProtectedRoute> that requires a single role.
 * Delegates auth + role gating to ProtectedRoute so the guard logic lives once.
 */
export default function RoleRoute({ role, children }) {
  return <ProtectedRoute roles={[role]}>{children}</ProtectedRoute>
}
