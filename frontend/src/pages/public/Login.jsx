import { useState } from 'react'
import { Link, Navigate, useLocation, useNavigate } from 'react-router-dom'
import { useAuth } from '../../hooks/useAuth'
import { useToast } from '../../components/ToastContext'
import { dashboardPathForRole } from '../../utils/constants'
import Button from '../../components/Button'
import Card from '../../components/Card'
import Field from '../../components/Field'
import Input from '../../components/Input'
import styles from './Login.module.css'

/*
 * Login for all roles (Customer / Pharmacy Staff / Administrator).
 * Role is returned by the backend; we redirect to the matching dashboard.
 */
export default function Login() {
  const { user, login } = useAuth()
  const toast = useToast()
  const navigate = useNavigate()
  const location = useLocation()

  const [form, setForm] = useState({ email: '', password: '' })
  const [errors, setErrors] = useState({})
  const [submitting, setSubmitting] = useState(false)

  if (user) return <Navigate to={dashboardPathForRole(user.role)} replace />

  const update = (e) => setForm((f) => ({ ...f, [e.target.name]: e.target.value }))

  const validate = () => {
    const next = {}
    if (!form.email.trim()) next.email = 'Email is required.'
    if (!form.password) next.password = 'Password is required.'
    setErrors(next)
    return Object.keys(next).length === 0
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!validate()) return
    setSubmitting(true)
    setErrors({})
    try {
      const data = await login({ email: form.email.trim(), password: form.password })
      toast.success(`Welcome back, ${data.full_name}.`)
      const dest = location.state?.from || dashboardPathForRole(data.role)
      navigate(dest, { replace: true })
    } catch (err) {
      const status = err?.response?.status
      const msg = err?.response?.data?.error
      if (status === 401) setErrors({ form: msg || 'Invalid login credentials.' })
      else if (status === 403) setErrors({ form: msg || 'Account is inactive.' })
      else setErrors({ form: msg || 'Unable to log in. Please try again.' })
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className={styles.page}>
      <Card className={styles.card} padded={false}>
        <div className={styles.header}>
          <h1 className={styles.title}>Medicine Booking Allocation</h1>
          <p className={styles.subtitle}>Sign in to your account</p>
        </div>
        <form className={styles.body} onSubmit={handleSubmit} noValidate>
          {errors.form && <div className={styles.formError} role="alert">{errors.form}</div>}
          <Field label="Email" htmlFor="email" error={errors.email} required>
            <Input
              id="email"
              name="email"
              type="email"
              autoComplete="email"
              value={form.email}
              onChange={update}
              invalid={!!errors.email}
              placeholder="you@example.com"
            />
          </Field>
          <Field label="Password" htmlFor="password" error={errors.password} required>
            <Input
              id="password"
              name="password"
              type="password"
              autoComplete="current-password"
              value={form.password}
              onChange={update}
              invalid={!!errors.password}
              placeholder="••••••••"
            />
          </Field>
          <Button type="submit" fullWidth loading={submitting}>Sign in</Button>
        </form>
        <div className={styles.footer}>
          New customer? <Link to="/register">Create an account</Link>
        </div>
      </Card>
      <p className={styles.note}>
        Customers register here. Pharmacy staff and administrators sign in with their seeded accounts.
      </p>
    </div>
  )
}
