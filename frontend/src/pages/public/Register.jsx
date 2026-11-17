import { useState } from 'react'
import { Link, Navigate, useNavigate } from 'react-router-dom'
import { useAuth } from '../../hooks/useAuth'
import { useToast } from '../../components/ToastContext'
import { dashboardPathForRole } from '../../utils/constants'
import Button from '../../components/Button'
import Card from '../../components/Card'
import Field from '../../components/Field'
import Input from '../../components/Input'
import styles from './Register.module.css'

/*
 * Customer registration only. The backend always creates a 'Customer' account
 * and does NOT start a session, so we send the user to /login afterwards.
 * Staff/admin accounts are provisioned separately (not here).
 */
export default function Register() {
  const { user, register } = useAuth()
  const toast = useToast()
  const navigate = useNavigate()

  const [form, setForm] = useState({ full_name: '', email: '', phone: '', password: '', confirm: '' })
  const [errors, setErrors] = useState({})
  const [submitting, setSubmitting] = useState(false)

  if (user) return <Navigate to={dashboardPathForRole(user.role)} replace />

  const update = (e) => setForm((f) => ({ ...f, [e.target.name]: e.target.value }))

  const validate = () => {
    const next = {}
    if (!form.full_name.trim()) next.full_name = 'Full name is required.'
    if (!form.email.trim()) next.email = 'Email is required.'
    else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(form.email.trim())) next.email = 'Enter a valid email.'
    if (form.password.length < 6) next.password = 'Password must be at least 6 characters.'
    if (form.confirm !== form.password) next.confirm = 'Passwords do not match.'
    setErrors(next)
    return Object.keys(next).length === 0
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!validate()) return
    setSubmitting(true)
    setErrors({})
    try {
      await register({
        full_name: form.full_name.trim(),
        email: form.email.trim(),
        phone: form.phone.trim(),
        password: form.password,
      })
      toast.success('Account created. Please sign in.')
      navigate('/login', { replace: true })
    } catch (err) {
      const msg = err?.response?.data?.error
      if (err?.response?.status === 400 && /already registered/i.test(msg || '')) {
        setErrors({ email: msg })
      } else {
        setErrors({ form: msg || 'Could not complete registration.' })
      }
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className={styles.page}>
      <Card className={styles.card} padded={false}>
        <div className={styles.header}>
          <h1 className={styles.title}>Create your account</h1>
          <p className={styles.subtitle}>Customer registration</p>
        </div>
        <form className={styles.body} onSubmit={handleSubmit} noValidate>
          {errors.form && <div className={styles.formError} role="alert">{errors.form}</div>}
          <Field label="Full name" htmlFor="full_name" error={errors.full_name} required>
            <Input id="full_name" name="full_name" autoComplete="name"
              value={form.full_name} onChange={update} invalid={!!errors.full_name} placeholder="Jane Doe" />
          </Field>
          <Field label="Email" htmlFor="email" error={errors.email} required>
            <Input id="email" name="email" type="email" autoComplete="email"
              value={form.email} onChange={update} invalid={!!errors.email} placeholder="you@example.com" />
          </Field>
          <Field label="Phone" htmlFor="phone" hint="Optional">
            <Input id="phone" name="phone" autoComplete="tel"
              value={form.phone} onChange={update} placeholder="9876543210" />
          </Field>
          <Field label="Password" htmlFor="password" error={errors.password} required hint="At least 6 characters.">
            <Input id="password" name="password" type="password" autoComplete="new-password"
              value={form.password} onChange={update} invalid={!!errors.password} placeholder="••••••••" />
          </Field>
          <Field label="Confirm password" htmlFor="confirm" error={errors.confirm} required>
            <Input id="confirm" name="confirm" type="password" autoComplete="new-password"
              value={form.confirm} onChange={update} invalid={!!errors.confirm} placeholder="••••••••" />
          </Field>
          <Button type="submit" fullWidth loading={submitting}>Create account</Button>
        </form>
        <div className={styles.footer}>
          Already have an account? <Link to="/login">Sign in</Link>
        </div>
      </Card>
      <p className={styles.note}>
        Registration is for customers. Pharmacy staff and administrators are provisioned separately.
      </p>
    </div>
  )
}
