import { useState } from 'react'
import { useAsync } from '../../hooks/useAsync'
import { getMyNotifications } from '../../api/notificationApi'
import { NOTIF_EVENT_TYPES, NOTIFICATION_STATUSES, formatDateTime } from '../../utils/domain'
import PageHeader from '../../components/PageHeader'
import Card from '../../components/Card'
import Select from '../../components/Select'
import DataTable from '../../components/DataTable'
import Stack from '../../components/Stack'
import Badge from '../../components/Badge'
import StatusBadge from '../../components/StatusBadge'
import shared from '../../styles/shared.module.css'

export default function Notifications() {
  const [event_type, setEventType] = useState('')
  const [status, setStatus] = useState('')
  const { data, loading, error, reload } = useAsync(
    () => getMyNotifications({ event_type: event_type || undefined, status: status || undefined }),
    [event_type, status]
  )
  const rows = data?.notifications || []

  const columns = [
    { key: 'event_type', header: 'Type', render: (r) => <Badge tone="teal">{r.event_type}</Badge> },
    { key: 'message', header: 'Message', render: (r) => <span className={shared.small}>{r.message}</span> },
    { key: 'channel', header: 'Channel' },
    { key: 'status', header: 'Status', render: (r) => <StatusBadge status={r.status} /> },
    { key: 'created_at', header: 'When', render: (r) => formatDateTime(r.created_at) },
  ]

  return (
    <div>
      <PageHeader title="Notifications" subtitle="Your booking, allocation and prescription updates" />
      <Stack gap="4">
        <Card>
          <div className={shared.toolbar}>
            <div className={shared.grow}>
              <Select value={event_type} onChange={(e) => setEventType(e.target.value)}>
                <option value="">All event types</option>
                {NOTIF_EVENT_TYPES.map((t) => <option key={t} value={t}>{t}</option>)}
              </Select>
            </div>
            <div className={shared.grow}>
              <Select value={status} onChange={(e) => setStatus(e.target.value)}>
                <option value="">All statuses</option>
                {NOTIFICATION_STATUSES.map((s) => <option key={s} value={s}>{s}</option>)}
              </Select>
            </div>
          </div>
        </Card>
        <Card padded={false}>
          <DataTable
            columns={columns}
            rows={rows}
            loading={loading}
            error={error}
            onRetry={reload}
            rowKey="notification_id"
            emptyTitle="No notifications"
            emptyMessage="You have no notifications matching these filters."
          />
        </Card>
      </Stack>
    </div>
  )
}
