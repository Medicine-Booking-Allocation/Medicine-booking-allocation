import { useState } from 'react'
import * as adminApi from '../../api/adminApi'
import { useAsync } from '../../hooks/useAsync'
import { formatDateTime, NOTIF_EVENT_TYPES, NOTIFICATION_STATUSES } from '../../utils/domain'
import PageHeader from '../../components/PageHeader'
import Card from '../../components/Card'
import Input from '../../components/Input'
import Select from '../../components/Select'
import DataTable from '../../components/DataTable'
import StatusBadge from '../../components/StatusBadge'
import Badge from '../../components/Badge'
import Stack from '../../components/Stack'
import shared from '../../styles/shared.module.css'

const TABS = [
  { id: 'bookings', label: 'Bookings' },
  { id: 'allocations', label: 'Allocations' },
  { id: 'waitlist', label: 'Waitlist' },
  { id: 'inventory', label: 'Inventory' },
  { id: 'prescriptions', label: 'Prescriptions' },
  { id: 'notifications', label: 'Notifications' },
]

const ROW_KEY = {
  bookings: 'booking_id', allocations: 'booking_id', waitlist: 'waitlist_id',
  inventory: 'inventory_id', prescriptions: 'prescription_id', notifications: 'notification_id',
}

export default function Reports() {
  const [tab, setTab] = useState('bookings')
  const [f, setF] = useState({ status: '', medicine_id: '', start_date: '', end_date: '', event_type: '', channel: '' })
  const set = (k, v) => setF((s) => ({ ...s, [k]: v }))

  const fetcher = () => {
    const p = { status: f.status || undefined, medicine_id: f.medicine_id || undefined, start_date: f.start_date || undefined, end_date: f.end_date || undefined }
    switch (tab) {
      case 'bookings': return adminApi.getBookingsReport(p)
      case 'allocations': return adminApi.getAllocationsReport({ ...p, status: f.status || 'Allocated' })
      case 'waitlist': return adminApi.getWaitlistReport(p)
      case 'inventory': return adminApi.getInventoryReport({ medicine_id: f.medicine_id || undefined })
      case 'prescriptions': return adminApi.getPrescriptionsReport({ status: f.status || undefined, start_date: f.start_date || undefined, end_date: f.end_date || undefined })
      case 'notifications': return adminApi.getNotificationsReport({ status: f.status || undefined, event_type: f.event_type || undefined, channel: f.channel || undefined, start_date: f.start_date || undefined, end_date: f.end_date || undefined })
      default: return Promise.resolve(null)
    }
  }
  const { data, loading, error, reload } = useAsync(fetcher, [tab, f.status, f.medicine_id, f.start_date, f.end_date, f.event_type, f.channel])
  const rows = (data && data[tab]) || []

  const columns = (() => {
    switch (tab) {
      case 'bookings': return [
        { key: 'booking_id', header: 'ID', render: (r) => <span className={shared.codeBox}>{r.booking_id}</span> },
        { key: 'medicine_id', header: 'Medicine', render: (r) => <span className={shared.codeBox}>{r.medicine_id}</span> },
        { key: 'quantity', header: 'Qty', align: 'right' },
        { key: 'urgency', header: 'Urgency' },
        { key: 'priority_score', header: 'Priority', align: 'right' },
        { key: 'status', header: 'Status', render: (r) => <StatusBadge status={r.status} /> },
        { key: 'created_at', header: 'Created', render: (r) => formatDateTime(r.created_at) },
      ]
      case 'allocations': return [
        { key: 'booking_id', header: 'ID', render: (r) => <span className={shared.codeBox}>{r.booking_id}</span> },
        { key: 'medicine_id', header: 'Medicine', render: (r) => <span className={shared.codeBox}>{r.medicine_id}</span> },
        { key: 'quantity', header: 'Qty', align: 'right' },
        { key: 'urgency', header: 'Urgency' },
        { key: 'priority_score', header: 'Priority', align: 'right' },
        { key: 'status', header: 'Status', render: (r) => <StatusBadge status={r.status} /> },
        { key: 'allocated_at', header: 'Allocated', render: (r) => formatDateTime(r.allocated_at) },
      ]
      case 'waitlist': return [
        { key: 'position', header: 'Pos', align: 'right' },
        { key: 'booking_id', header: 'Booking', render: (r) => <span className={shared.codeBox}>{r.booking_id}</span> },
        { key: 'medicine_id', header: 'Medicine', render: (r) => <span className={shared.codeBox}>{r.medicine_id}</span> },
        { key: 'quantity', header: 'Qty', align: 'right' },
        { key: 'priority_score', header: 'Priority', align: 'right' },
        { key: 'waitlist_status', header: 'Waitlist', render: (r) => <StatusBadge status={r.waitlist_status} /> },
        { key: 'booking_status', header: 'Booking', render: (r) => <StatusBadge status={r.booking_status} /> },
        { key: 'created_at', header: 'Created', render: (r) => formatDateTime(r.created_at) },
      ]
      case 'inventory': return [
        { key: 'medicine_name', header: 'Medicine', render: (r) => <strong>{r.medicine_name}</strong> },
        { key: 'available_quantity', header: 'Available', align: 'right' },
        { key: 'reserved_quantity', header: 'Reserved', align: 'right' },
        { key: 'fulfilled_quantity', header: 'Fulfilled', align: 'right' },
        { key: 'last_updated_at', header: 'Updated', render: (r) => formatDateTime(r.last_updated_at) },
      ]
      case 'prescriptions': return [
        { key: 'prescription_id', header: 'ID', render: (r) => <span className={shared.codeBox}>{r.prescription_id}</span> },
        { key: 'user_id', header: 'User', render: (r) => <span className={shared.codeBox}>{r.user_id}</span> },
        { key: 'prescription_status', header: 'Status', render: (r) => <StatusBadge status={r.prescription_status} /> },
        { key: 'submitted_at', header: 'Submitted', render: (r) => formatDateTime(r.submitted_at) },
        { key: 'verified_at', header: 'Verified', render: (r) => formatDateTime(r.verified_at) },
      ]
      case 'notifications': return [
        { key: 'notification_id', header: 'ID', render: (r) => <span className={shared.codeBox}>{r.notification_id}</span> },
        { key: 'user_id', header: 'User', render: (r) => <span className={shared.codeBox}>{r.user_id}</span> },
        { key: 'event_type', header: 'Type', render: (r) => <Badge tone="teal">{r.event_type}</Badge> },
        { key: 'channel', header: 'Channel' },
        { key: 'status', header: 'Status', render: (r) => <StatusBadge status={r.status} /> },
        { key: 'created_at', header: 'Created', render: (r) => formatDateTime(r.created_at) },
      ]
      default: return []
    }
  })()

  const showMedId = ['bookings', 'allocations', 'waitlist', 'inventory'].includes(tab)
  const showDates = ['bookings', 'allocations', 'waitlist', 'prescriptions', 'notifications'].includes(tab)
  const showStatus = ['bookings', 'waitlist', 'prescriptions', 'notifications'].includes(tab)
  const showNotif = tab === 'notifications'

  return (
    <div>
      <PageHeader title="Reports" subtitle="Bookings, allocations, waitlist, inventory, prescriptions and notifications" />
      <Stack gap="4">
        <div className={shared.tabBar}>
          {TABS.map((t) => (
            <button key={t.id} className={`${shared.tab} ${tab === t.id ? shared.tabActive : ''}`} onClick={() => setTab(t.id)}>{t.label}</button>
          ))}
        </div>

        <Card>
          <div className={shared.toolbar}>
            {showStatus && (
              <div className={shared.grow}>
                <Select value={f.status} onChange={(e) => set('status', e.target.value)}>
                  <option value="">All statuses</option>
                  {NOTIFICATION_STATUSES.map((s) => <option key={s} value={s}>{s}</option>)}
                </Select>
              </div>
            )}
            {showMedId && <div className={shared.grow}><Input placeholder="Medicine ID" value={f.medicine_id} onChange={(e) => set('medicine_id', e.target.value)} /></div>}
            {showDates && <div className={shared.grow}><Input type="date" value={f.start_date} onChange={(e) => set('start_date', e.target.value)} /></div>}
            {showDates && <div className={shared.grow}><Input type="date" value={f.end_date} onChange={(e) => set('end_date', e.target.value)} /></div>}
            {showNotif && (
              <div className={shared.grow}>
                <Select value={f.event_type} onChange={(e) => set('event_type', e.target.value)}>
                  <option value="">All types</option>
                  {NOTIF_EVENT_TYPES.map((t) => <option key={t} value={t}>{t}</option>)}
                </Select>
              </div>
            )}
            {showNotif && <div className={shared.grow}><Input placeholder="Channel" value={f.channel} onChange={(e) => set('channel', e.target.value)} /></div>}
          </div>
        </Card>

        {data && (
          <div className={shared.inline}>
            {data.status_summary
              ? Object.entries(data.status_summary).map(([s, c]) => <Badge key={s} tone="neutral">{s}: {c}</Badge>)
              : <Badge tone="navy">Total: {data.total_bookings ?? data.total_allocations ?? data.total_entries ?? data.total_inventory_records ?? data.total_prescriptions ?? data.total_notifications ?? rows.length}</Badge>}
            {data.total_quantity_allocated != null && <Badge tone="teal">Units allocated: {data.total_quantity_allocated}</Badge>}
          </div>
        )}

        <Card padded={false}>
          <DataTable columns={columns} rows={rows} loading={loading} error={error} onRetry={reload} rowKey={ROW_KEY[tab]} emptyTitle="No records" emptyMessage="No records match these filters." />
        </Card>
      </Stack>
    </div>
  )
}
