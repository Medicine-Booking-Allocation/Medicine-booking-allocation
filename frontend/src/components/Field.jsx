import styles from './Field.module.css'

/*
 * Form-field wrapper: label, optional required marker, hint, and error.
 * Wrap any control (Input/Textarea/Select) inside <Field>.
 */
export default function Field({ label, htmlFor, hint, error, required, children, className = '' }) {
  return (
    <div className={`${styles.field} ${className}`}>
      {label && (
        <label className={styles.label} htmlFor={htmlFor}>
          {label}
          {required && <span className={styles.required} aria-hidden="true">*</span>}
        </label>
      )}
      {children}
      {hint && !error && <p className={styles.hint}>{hint}</p>}
      {error && <p className={styles.error} role="alert">{error}</p>}
    </div>
  )
}
