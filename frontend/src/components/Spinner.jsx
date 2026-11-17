import styles from './Spinner.module.css'

/*
 * Lightweight CSS spinner. tone="inherit" picks up the surrounding text
 * colour, which is how <Button loading> shows a correctly-coloured spinner.
 */
export default function Spinner({ size = 'md', tone = 'inherit', label = 'Loading' }) {
  return (
    <span
      className={`${styles.spinner} ${styles[`size_${size}`]} ${styles[`tone_${tone}`] || styles.tone_inherit}`}
      role="status"
      aria-label={label}
    />
  )
}
