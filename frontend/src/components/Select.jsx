import { forwardRef } from 'react'
import styles from './Select.module.css'

/*
 * Styled native select with a custom chevron. Pass <option> children.
 */
const Select = forwardRef(function Select(
  { invalid = false, children, className = '', ...rest },
  ref
) {
  return (
    <div className={styles.wrap}>
      <select
        ref={ref}
        className={`${styles.select} ${invalid ? styles.invalid : ''} ${className}`}
        {...rest}
      >
        {children}
      </select>
      <span className={styles.chevron} aria-hidden="true">▾</span>
    </div>
  )
})

export default Select
