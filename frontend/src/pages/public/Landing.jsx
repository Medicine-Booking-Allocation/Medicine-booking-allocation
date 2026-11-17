import { Link, Navigate } from 'react-router-dom'
import { useAuth } from '../../hooks/useAuth'
import { dashboardPathForRole } from '../../utils/constants'
import Button from '../../components/Button'
import styles from './Landing.module.css'

/*
 * Public landing page. A signed-in user is redirected to their role dashboard.
 */
export default function Landing() {
  const { user } = useAuth()
  if (user) return <Navigate to={dashboardPathForRole(user.role)} replace />

  return (
    <div className={styles.page}>
      <div className={styles.hero}>
        <span className={styles.eyebrow}>Priority-Based Medicine Booking &amp; Allocation</span>
        <h1 className={styles.title}>Medicine booking, prioritised for those who need it most.</h1>
        <p className={styles.lead}>
          Search medicines, book with priority scoring, submit prescriptions for verification,
          and track allocations — for customers, pharmacy staff and administrators.
        </p>
        <div className={styles.actions}>
          <Link to="/login"><Button size="lg">Sign in</Button></Link>
          <Link to="/register"><Button variant="secondary" size="lg">Create customer account</Button></Link>
        </div>
      </div>
    </div>
  )
}
