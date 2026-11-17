import styles from './Row.module.css'

/*
 * Horizontal flex row with configurable gap, wrap, alignment and justify.
 * gap: 0..7   align: start | center | end   justify: start | center | end | between
 */
export default function Row({
  children,
  gap = '3',
  wrap = true,
  align = 'center',
  justify,
  className = '',
  as: Tag = 'div',
  ...rest
}) {
  const classes = [
    styles.row,
    styles[`gap_${gap}`] || styles.gap_3,
    styles[`align_${align}`] || styles.align_center,
    justify ? styles[`justify_${justify}`] : '',
    wrap ? styles.wrap : '',
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
