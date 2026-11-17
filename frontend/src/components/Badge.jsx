import styles from './Badge.module.css'

/*
 * Pill badge. tone maps to status/semantic colours:
 * navy, teal, green, amber, red, blue, neutral.
 * Optional dot renders a leading coloured dot.
 */
export default function Badge({ children, tone = 'neutral', dot = false, size = 'md' }) {
  const classes = [
    styles.badge,
    styles[`tone_${tone}`] || styles.tone_neutral,
    styles[`size_${size}`] || styles.size_md,
  ]
    .filter(Boolean)
    .join(' ')

  return (
    <span className={classes}>
      {dot && <span className={styles.dot} aria-hidden="true" />}
      {children}
    </span>
  )
}
