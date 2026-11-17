import styles from './EmptyState.module.css'

const DEFAULT_ICON = (
  <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
    <path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z" />
  </svg>
)

/*
 * Friendly "nothing to show" placeholder with optional action.
 */
export default function EmptyState({ icon, title = 'Nothing here yet', message, action }) {
  return (
    <div className={styles.empty}>
      <div className={styles.icon}>{icon ?? DEFAULT_ICON}</div>
      <h3 className={styles.title}>{title}</h3>
      {message && <p className={styles.message}>{message}</p>}
      {action && <div className={styles.action}>{action}</div>}
    </div>
  )
}
