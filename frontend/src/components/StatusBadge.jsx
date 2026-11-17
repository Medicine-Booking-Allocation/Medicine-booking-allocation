import Badge from './Badge'
import { statusMeta } from '../utils/statusMeta'

/*
 * Renders a backend status as a labelled, colour-coded badge.
 * Status strings come straight from the API responses.
 */
export default function StatusBadge({ status, dot = true, size }) {
  const { label, tone } = statusMeta(status)
  return (
    <Badge tone={tone} dot={dot} size={size}>
      {label}
    </Badge>
  )
}
