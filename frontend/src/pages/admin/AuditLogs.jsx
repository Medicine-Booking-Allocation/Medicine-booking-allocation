import { useState } from 'react'
import { getAuditLogs } from '../../api/adminApi'
import { useAsync } from '../../hooks/useAsync'
import { formatDateTime } from '../../utils/domain'
import PageHeader from '../../components/PageHeader'
import Card from '../../components/Card'
import Input from '../../components/Input'
import DataTable from '../../components/DataTable'
import Stack from '../../components/Stack'
import shared from '../../styles/shared.module.css'

export default function AuditLogs() {
  const [actor_id, setActorId] = useState('')
  const [action, setAction] = useState('')
  const [entity_type, setEntityType] = useState('')
  const [entity_id, setEntityId] = useState('')
  const [limit, setLimit] = useState('100')
  const { data, loading, error, reload } = useAsync(
    () => getAuditLogs({
      actor_id: actor_id || undefined,
      action: action || undefined,
      entity_type: entity_type || undefined,
      entity_id: entity_id || undefined,
      limit: parseInt(limit, 10) || 100,
    }),
    [actor_id, action, entity_type, entity_id, limit]
  )
  const rows = data?.audit_logs || []

  const columns = [
    { key: 'timestamp', header: 'When', render: (r) => formatDateTime(r.timestamp) },
    { key: 'action', header: 'Action', render: (r) => <span className={shared.strong}>{r.action}</span> },
    { key: 'actor_id', header: 'Actor', render: (r) => r.actor_id ? <span className={shared.codeBox}>{r.actor_id}</span> : '—' },
    { key: 'entity_type', header: 'Entity type' },
    { key: 'entity_id', header: 'Entity ID', render: (r) => r.entity_id ? <span className={shared.codeBox}>{r.entity_id}</span> : '—' },
    { key: 'details', header: 'Details', render: (r) => <span className={shared.small} title={r.details || ''}>{r.details || '—'}</span> },
  ]

  return (
    <div>
      <PageHeader title="Audit logs" subtitle="Security and action history" />
      <Stack gap="4">
        <Card>
          <div className={shared.toolbar}>
            <div className={shared.grow}><Input placeholder="Actor ID" value={actor_id} onChange={(e) => setActorId(e.target.value)} /></div>
            <div className={shared.grow}><Input placeholder="Action (e.g. BOOKING_CREATED)" value={action} onChange={(e) => setAction(e.target.value)} /></div>
            <div className={shared.grow}><Input placeholder="Entity type" value={entity_type} onChange={(e) => setEntityType(e.target.value)} /></div>
            <div className={shared.grow}><Input placeholder="Entity ID" value={entity_id} onChange={(e) => setEntityId(e.target.value)} /></div>
            <div className={shared.grow}><Input type="number" min="1" max="500" placeholder="Limit (1–500)" value={limit} onChange={(e) => setLimit(e.target.value)} /></div>
          </div>
        </Card>
        <Card padded={false}>
          <DataTable columns={columns} rows={rows} loading={loading} error={error} onRetry={reload} rowKey="audit_id" emptyTitle="No audit logs" emptyMessage="No logs match these filters." />
        </Card>
      </Stack>
    </div>
  )
}
