import styles from './Grid.module.css'

/*
 * Responsive auto-fill grid. min is a CSS length (default 240px); columns
 * collapse naturally on small screens. gap is a Stack/Row gap token (0..7).
 */
export default function Grid({ children, min = '240px', gap = '4', className = '', as: Tag = 'div', ...rest }) {
  return (
    <Tag
      className={`${styles.grid} ${className}`}
      style={{ '--grid-min': min, '--grid-gap': `var(--p47-space-${gap})` }}
      {...rest}
    >
      {children}
    </Tag>
  )
}
