import Spinner from './Spinner'
import EmptyState from './EmptyState'
import ErrorState from './ErrorState'
import Button from './Button'
import styles from './DataTable.module.css'

/*
 * Generic table. columns: [{ key, header, render?, align?, width? }].
 * Handles loading, error (with optional retry), and empty states.
 */
export default function DataTable({
  columns,
  rows,
  loading,
  error,
  onRetry,
  emptyTitle = 'No records',
  emptyMessage,
  rowKey = 'id',
  onRowClick,
  compact,
}) {
  if (loading) {
    return <div className={styles.loading}><Spinner size="lg" tone="teal" /></div>
  }
  if (error) {
    return (
      <ErrorState
        message={error}
        action={onRetry ? <Button variant="ghost" size="sm" onClick={onRetry}>Try again</Button> : null}
      />
    )
  }
  if (!rows || rows.length === 0) {
    return <EmptyState title={emptyTitle} message={emptyMessage} />
  }

  const key = typeof rowKey === 'function' ? rowKey : (r) => r[rowKey]

  return (
    <div className={styles.wrap}>
      <table className={`${styles.table} ${compact ? styles.compact : ''}`}>
        <thead>
          <tr>
            {columns.map((c) => (
              <th key={c.key} style={c.width ? { width: c.width } : undefined} className={c.align === 'right' ? styles.right : ''}>
                {c.header}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((r) => (
            <tr key={key(r)} className={onRowClick ? styles.clickable : ''} onClick={onRowClick ? () => onRowClick(r) : undefined}>
              {columns.map((c) => (
                <td key={c.key} className={c.align === 'right' ? styles.right : ''}>
                  {c.render ? c.render(r) : (r[c.key] ?? '—')}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
