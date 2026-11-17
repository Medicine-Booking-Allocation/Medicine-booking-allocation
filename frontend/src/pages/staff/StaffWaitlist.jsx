import { useState } from 'react'
import { getWaitlist, cancelWaitlist, promoteWaitlist } from '../../api/waitlistApi'
import { useAsync } from '../../hooks/useAsync'
import { useToast } from '../../components/ToastContext'
import { WAITLIST_STATUSES, formatDateTime } from '../../utils/domain'
import PageHeader from '../../components/PageHeader'
import Card from '../../components/Card'
import Input from '../../components/Input'
import Select from '../../components/Select'
import Button from '../../components/Button'
import StatusBadge from '../../components/StatusBadge'
import DataTable from '../../components/DataTable'
import ConfirmDialog from '../../components/ConfirmDialog'
import Stack from '../../components/Stack'
import shared from '../../styles/shared.module.css'

export default function StaffWaitlist() {
  const toast = useToast()
  const [status, setStatus] = useState('Active')
  const [medicine_id, setMedId] = useState('')
  const { data, loading, error, reload } = useAsync(() => getWaitlist({ status, medicine_id: medicine_id || undefined }), [status, medicine_id])
  const [cancelTarget, setCancelTarget] = useState(null)
  const [cancelling, setCancelling] = useState(false)
  const [promoting, setPromoting] = useState('')
  const rows = data?.waitlist || []

  const doCancel = async () => {
    setCancelling(true)
    try { await cancelWaitlist(cancelTarget.waitlist_id); toast.success('Waitlist entry cancelled.'); reload() }
    catch (err) { toast.error(err?.response?.data?.error || 'Could not cancel.') }
    finally { setCancelling(false); setCancelTarget(null) }
  }

  const doPromote = async (medId) => {
    setPromoting(medId)
    try { const res = await promoteWaitlist(medId); toast.success(`${res.promoted_count} booking(s) promoted.`); reload() }
    catch (err) { toast.error(err?.response?.data?.error || 'Promotion failed.') }
    finally { setPromoting('') }
  }

  const columns = [
    { key: 'position', header: 'Pos', align: 'right' },
    { key: 'medicine_name', header: 'Medicine', render: (r) => <strong>{r.medicine_name}</strong> },
    { key: 'quantity', header: 'Qty', align: 'right' },
    { key: 'urgency', header: 'Urgency' },
    { key: 'priority_score', header: 'Priority', align: 'right', render: (r) => r.priority_score },
    { key: 'waitlist_status', header: 'Waitlist', render: (r) => <StatusBadge status={r.waitlist_status} /> },
    { key: 'booking_status', header: 'Booking', render: (r) => <StatusBadge status={r.booking_status} /> },
    { key: 'created_at', header: 'Created', render: (r) => formatDateTime(r.created_at) },
    {
      key: 'actions', header: 'Actions', render: (r) => (
        <div className={shared.inline}>
          {r.waitlist_status === 'Active' && <Button size="sm" variant="subtle" loading={promoting === r.medicine_id} onClick={() => doPromote(r.medicine_id)}>Promote</Button>}
          {r.waitlist_status === 'Active' && <Button size="sm" variant="ghost" onClick={() => setCancelTarget(r)}>Cancel</Button>}
        </div>
      ),
    },
  ]

  return (
    <div>
      <PageHeader title="Waitlist" subtitle="Promote after stock replenishment or cancel entries" />
      <Stack gap="4">
        <Card>
          <div className={shared.toolbar}>
            <div className={shared.grow}>
              <Select value={status} onChange={(e) => setStatus(e.target.value)}>
                {WAITLIST_STATUSES.map((s) => <option key={s} value={s}>{s}</option>)}
              </Select>
            </div>
            <div className={shared.grow}><Input placeholder="Filter by medicine ID (optional)" value={medicine_id} onChange={(e) => setMedId(e.target.value)} /></div>
          </div>
        </Card>
        <Card padded={false}>
          <DataTable columns={columns} rows={rows} loading={loading} error={error} onRetry={reload} rowKey="waitlist_id" emptyTitle="No waitlist entries" emptyMessage="No entries match these filters." />
        </Card>
      </Stack>
      <ConfirmDialog open={!!cancelTarget} onClose={() => setCancelTarget(null)} onConfirm={doCancel} loading={cancelling} tone="danger" title="Cancel this waitlist entry?" message="The linked booking will also be cancelled." confirmLabel="Yes, cancel" cancelLabel="Keep" />
    </div>
  )
}
