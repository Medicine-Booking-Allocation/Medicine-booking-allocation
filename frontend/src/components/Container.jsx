import styles from './Container.module.css'

/*
 * Centred, max-width content container. Renders any element via the `as` prop.
 */
export default function Container({ children, className = '', as: Tag = 'div', ...rest }) {
  return (
    <Tag className={`${styles.container} ${className}`} {...rest}>
      {children}
    </Tag>
  )
}
