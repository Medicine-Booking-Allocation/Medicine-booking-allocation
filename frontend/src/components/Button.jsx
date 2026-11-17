import Spinner from './Spinner'
import styles from './Button.module.css'

/*
 * Primary action button. Variants map to the medical theme:
 *   primary  navy (default)
 *   secondary white with navy text + teal hover border
 *   success  green
 *   danger   red
 *   ghost    transparent
 *   subtle   soft teal
 * Sizes: sm, md, lg. Supports loading (shows spinner) and disabled.
 */
export default function Button({
  children,
  variant = 'primary',
  size = 'md',
  type = 'button',
  loading = false,
  disabled = false,
  fullWidth = false,
  leftIcon,
  rightIcon,
  className = '',
  ...rest
}) {
  const classes = [
    styles.btn,
    styles[`variant_${variant}`] || styles.variant_primary,
    styles[`size_${size}`] || styles.size_md,
    fullWidth ? styles.fullWidth : '',
    loading ? styles.loading : '',
    className,
  ]
    .filter(Boolean)
    .join(' ')

  return (
    <button type={type} className={classes} disabled={disabled || loading} {...rest}>
      {loading && (
        <span className={styles.spinnerWrap}>
          <Spinner size={size === 'lg' ? 'md' : 'sm'} />
        </span>
      )}
      {leftIcon && !loading && <span className={styles.icon}>{leftIcon}</span>}
      <span className={styles.label}>{children}</span>
      {rightIcon && !loading && <span className={styles.icon}>{rightIcon}</span>}
    </button>
  )
}
