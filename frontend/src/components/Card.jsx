import styles from './Card.module.css'

/*
 * Surface container with optional header (title + subtitle + actions) and body.
 * elevation: none | sm | md | lg (default md).
 */
export default function Card({
  title,
  subtitle,
  actions,
  children,
  padded = true,
  elevation = 'md',
  className = '',
  ...rest
}) {
  const classes = [styles.card, styles[`elev_${elevation}`] || '', className]
    .filter(Boolean)
    .join(' ')

  return (
    <div className={classes} {...rest}>
      {(title || actions) && (
        <div className={styles.header}>
          <div className={styles.heading}>
            {title && <h3 className={styles.title}>{title}</h3>}
            {subtitle && <p className={styles.subtitle}>{subtitle}</p>}
          </div>
          {actions && <div className={styles.actions}>{actions}</div>}
        </div>
      )}
      <div className={padded ? styles.body : styles.bodyFlush}>{children}</div>
    </div>
  )
}
