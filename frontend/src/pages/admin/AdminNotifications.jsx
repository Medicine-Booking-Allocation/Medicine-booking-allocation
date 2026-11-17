import { useState } from 'react'
import { getMyNotifications, updateNotificationStatus, retryNotification } from '../../api/notificationApi'
import { useAsync } from '../../hooks/useAsync'
import { useToast } from '../../components/ToastContext'
import { NOTIFICATION_STATUS_TRANSITIONS, NOTIF_EVENT_TYPES, NOTIFICATION_STATUSES, formatDateTime } from '../../utils/domain'
import PageHeader from '../../components/PageHeader'
import Card from '../../components/Card'
import Select from '../../components/Select'
import DataTable from '../../components/DataTable'
import Button from '../../components/Button'
import StatusBadge from '../../components/StatusBadge'
import Badge from '../../components/Badge'
import Stack from '../../components/Stack'
import shared from '../../styles/shared.module.css'

export default function AdminNotifications() {
  const toast = useToast()
  const [event_type, setEventType] = useState('')
  const [status, setStatus] = useState('')
  const { data, loading, error, reload } = useAsync(() => getMyNotifications({ event_type: event_type || undefined, status: status || undefined }), [event_type, status])
  const [busy, setBusy] = useState('')
  const rows = data?.notifications || []

  const setStatusFor = async (id, newStatus) => {
    setBusy(id + newStatus)
    try { await updateNotificationStatus(id, newStatus); toast.success('Notification status updated.'); reload() }
    catch (err) { toast.error(err?.response?.data?.error || 'Could not update status.') }
    finally { setBusy('') }
  }
  const retry = async (id) => {
    setBusy(id + 'retry')
    try { await retryNotification(id); toast.success('Notification queued for retry.'); reload() }
    catch (err) { toast.error(err?.response?.data?.error || 'Could not retry.') }
    finally { setBusy('') }
  }

  const columns = [
    { key: 'event_type', header: 'Type', render: (r) => <Badge tone="teal">{r.event_type}</Badge> },
    { key: 'message', header: 'Message', render: (r) => <span className={shared.small}>{r.message}</span> },
    { key: 'channel', header: 'Channel' },
    { key: 'status', header: 'Status', render: (r) => <StatusBadge status={r.status} /> },
    { key: 'created_at', header: 'When', render: (r) => formatDateTime(r.created_at) },
    {
      key: 'actions', header: 'Actions', render: (r) => (
        <div className={shared.inline}>
          {(NOTIFICATION_STATUS_TRANSITIONS[r.status] || []).map((s) => (
            <Button key={s} size="sm" variant="secondary" loading={busy === r.notification_id + s} onClick={() => setStatusFor(r.notification_id, s)}>{s}</Button>
          ))}
          {r.status === 'Failed' && <Button size="sm" variant="ghost" loading={busy === r.notification_id + 'retry'} onClick={() => retry(r.notification_id)}>Retry</Button>}
        </div>
      ),
    },
  ]

  return (
    <div>
      <PageHeader title="Notifications" subtitle="Your notifications — manage delivery status and retry" />
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
          <DataTable columns={columns} rows={rows} loading={loading} error={error} onRetry={reload} rowKey="notification_id" emptyTitle="No notifications" emptyMessage="No notifications match these filters." />
        </Card>
      </Stack>
    </div>
  )
}
