import styles from './Toast.module.css'

const ICON = {
  success: (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
      <polyline points="20 6 9 17 4 12" />
    </svg>
  ),
  error: (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
      <line x1="18" y1="6" x2="6" y2="18" />
      <line x1="6" y1="6" x2="18" y2="18" />
    </svg>
  ),
  info: (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="12" cy="12" r="10" />
      <line x1="12" y1="16" x2="12" y2="12" />
      <line x1="12" y1="8" x2="12.01" y2="8" />
    </svg>
  ),
  warning: (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
      <path d="M10.29 3.86 1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z" />
      <line x1="12" y1="9" x2="12" y2="13" />
      <line x1="12" y1="17" x2="12.01" y2="17" />
    </svg>
  ),
}

const TONE_COLOR = {
  success: 'var(--p47-green-600)',
  error: 'var(--p47-danger)',
  info: 'var(--p47-info)',
  warning: 'var(--p47-warning)',
}

/*
 * A single toast notification. The fixed viewport that stacks these is rendered
 * by <ToastProvider> (ToastContext.jsx).
 */
export default function Toast({ type = 'info', message, onClose }) {
  return (
    <div className={`${styles.toast} ${styles[`type_${type}`] || styles.type_info}`}>
      <span className={styles.icon} style={{ color: TONE_COLOR[type] || TONE_COLOR.info }}>
        {ICON[type] || ICON.info}
      </span>
      <p className={styles.message}>{message}</p>
      <button className={styles.close} onClick={onClose} aria-label="Dismiss">×</button>
    </div>
  )
}
