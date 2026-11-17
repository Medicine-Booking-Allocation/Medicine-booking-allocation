import { useState } from 'react'
import { getBooking, fulfilBooking, cancelBooking } from '../../api/bookingApi'
import { useToast } from '../../components/ToastContext'
import { formatDateTime } from '../../utils/domain'
import PageHeader from '../../components/PageHeader'
import Card from '../../components/Card'
import Input from '../../components/Input'
import Button from '../../components/Button'
import StatusBadge from '../../components/StatusBadge'
import DetailList from '../../components/DetailList'
import ConfirmDialog from '../../components/ConfirmDialog'
import Stack from '../../components/Stack'
import shared from '../../styles/shared.module.css'

export default function StaffBookings() {
  const toast = useToast()
  const [id, setId] = useState('')
  const [booking, setBooking] = useState(null)
  const [loading, setLoading] = useState(false)
  const [lookupError, setLookupError] = useState('')
  const [busy, setBusy] = useState('')
  const [confirmCancel, setConfirmCancel] = useState(false)

  const lookup = async (e) => {
    e?.preventDefault()
    if (!id.trim()) return
    setLoading(true); setLookupError(''); setBooking(null)
    try { setBooking(await getBooking(id.trim())) }
    catch (err) { setLookupError(err?.response?.data?.error || 'Booking not found.') }
    finally { setLoading(false) }
  }

  const fulfil = async () => {
    setBusy('fulfil')
    try { await fulfilBooking(booking.booking_id); toast.success('Booking fulfilled.'); setBooking(await getBooking(booking.booking_id)) }
    catch (err) { toast.error(err?.response?.data?.error || 'Could not fulfil booking.') }
    finally { setBusy('') }
  }

  const doCancel = async () => {
    setBusy('cancel')
    try { await cancelBooking(booking.booking_id); toast.success('Booking cancelled.'); setBooking(await getBooking(booking.booking_id)) }
    catch (err) { toast.error(err?.response?.data?.error || 'Could not cancel.') }
    finally { setBusy(''); setConfirmCancel(false) }
  }

  return (
    <div>
      <PageHeader title="Bookings" subtitle="Look up a booking by ID to fulfil or cancel" />
      <Stack gap="4">
        <Card title="Lookup by Booking ID">
          <form onSubmit={lookup} className={shared.inline}>
            <div className={shared.grow}><Input placeholder="Enter booking ID…" value={id} onChange={(e) => setId(e.target.value)} /></div>
            <Button type="submit" loading={loading}>Lookup</Button>
          </form>
          {lookupError && <div className={`${shared.note} ${shared.noteDanger}`} style={{ marginTop: 12 }}>{lookupError}</div>}
        </Card>
        {booking && (
          <Card title="Booking" actions={<StatusBadge status={booking.status} />}>
            <Stack gap="3">
              <DetailList items={[
                { label: 'Booking ID', value: <span className={shared.codeBox}>{booking.booking_id}</span> },
                { label: 'User ID', value: <span className={shared.codeBox}>{booking.user_id}</span> },
                { label: 'Medicine ID', value: <span className={shared.codeBox}>{booking.medicine_id}</span> },
                { label: 'Quantity', value: booking.quantity },
                { label: 'Urgency', value: booking.urgency },
                { label: 'Priority score', value: booking.priority_score },
                { label: 'Created', value: formatDateTime(booking.created_at) },
                { label: 'Allocated at', value: formatDateTime(booking.allocated_at) },
                { label: 'Prescription', value: booking.prescription_id ? <span className={shared.codeBox}>{booking.prescription_id}</span> : '—' },
              ]} />
              <div className={shared.inline}>
                {booking.status === 'Allocated' && <Button variant="success" loading={busy === 'fulfil'} onClick={fulfil}>Fulfil booking</Button>}
                {(booking.status === 'Requested' || booking.status === 'Allocated') && <Button variant="danger" onClick={() => setConfirmCancel(true)}>Cancel booking</Button>}
                {booking.status === 'Waitlisted' && <div className={`${shared.note} ${shared.noteInfo}`}>Waitlisted — cancel via the Waitlist tab (uses the waitlist ID shown there).</div>}
                {(booking.status === 'Fulfilled' || booking.status === 'Cancelled' || booking.status === 'Rejected') && <span className={shared.meta}>No further actions for this status.</span>}
              </div>
            </Stack>
          </Card>
        )}
      </Stack>
      <ConfirmDialog open={confirmCancel} onClose={() => setConfirmCancel(false)} onConfirm={doCancel} loading={busy === 'cancel'} tone="danger" title="Cancel this booking?" message="Reserved stock will be released." confirmLabel="Yes, cancel" cancelLabel="Keep" />
    </div>
  )
}
