import styles from './Stack.module.css'

/*
 * Vertical flex column with a configurable gap and optional alignment.
 * gap: 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7   align: start | center | end | stretch
 */
export default function Stack({ children, gap = '4', align, className = '', as: Tag = 'div', ...rest }) {
  const classes = [
    styles.stack,
    styles[`gap_${gap}`] || styles.gap_4,
    align ? styles[`align_${align}`] : '',
    className,
  ]
    .filter(Boolean)
    .join(' ')

  return (
    <Tag className={classes} {...rest}>
      {children}
    </Tag>
  )
}
