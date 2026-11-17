import { forwardRef } from 'react'
import styles from './Textarea.module.css'

const Textarea = forwardRef(function Textarea(
  { invalid = false, rows = 3, className = '', ...rest },
  ref
) {
  return (
    <textarea
      ref={ref}
      rows={rows}
      className={`${styles.textarea} ${invalid ? styles.invalid : ''} ${className}`}
      {...rest}
    />
  )
})

export default Textarea
