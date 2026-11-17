import styles from './DetailList.module.css'

/*
 * Key/value detail grid. items: [{ label, value }]
 */
export default function DetailList({ items }) {
  return (
    <dl className={styles.list}>
      {items.map((it) => (
        <div key={it.label} className={styles.row}>
          <dt className={styles.label}>{it.label}</dt>
          <dd className={styles.value}>{it.value ?? '—'}</dd>
        </div>
      ))}
    </dl>
  )
}
