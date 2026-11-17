import { forwardRef } from 'react'
import styles from './Input.module.css'

/*
 * Styled text input. Supports an optional leftIcon adornment and an `invalid`
 * flag that renders the error border (the message itself is shown by <Field>).
 */
const Input = forwardRef(function Input(
  { invalid = false, leftIcon, className = '', ...rest },
  ref
) {
  return (
    <div className={`${styles.wrap} ${leftIcon ? styles.hasIcon : ''}`}>
      {leftIcon && <span className={styles.icon}>{leftIcon}</span>}
      <input
        ref={ref}
        className={`${styles.input} ${invalid ? styles.invalid : ''} ${className}`}
        {...rest}
      />
    </div>
  )
})

export default Input
