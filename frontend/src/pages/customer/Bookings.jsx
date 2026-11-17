import { useEffect, useState } from 'react'
import { useAuth } from '../../hooks/useAuth'
import { getBooking, cancelBooking } from '../../api/bookingApi'
import { getBookings, removeBooking } from '../../utils/bookingStore'
import { useToast } from '../../components/ToastContext'
import { formatDateTime } from '../../utils/domain'
import PageHeader from '../../components/PageHeader'
import Card from '../../components/Card'
import Button from '../../components/Button'
import StatusBadge from '../../components/StatusBadge'
import DetailList from '../../components/DetailList'
import ConfirmDialog from '../../components/ConfirmDialog'
import Spinner from '../../components/Spinner'
import Stack from '../../components/Stack'
import shared from '../../styles/shared.module.css'

export default function Bookings() {
  const { user } = useAuth()
  const toast = useToast()
  const saved = getBookings(user?.user_id)
  const [list, setList] = useState(saved.map((s) => ({ ...s, loading: true, error: null, data: null })))
  const [cancelTarget, setCancelTarget] = useState(null)
  const [cancelling, setCancelling] = useState(false)

  useEffect(() => {
    let active = true
    saved.forEach((s, i) => {
      getBooking(s.id)
        .then((d) => active && setList((prev) => prev.map((x, j) => (j === i ? { ...x, data: d, loading: false } : x))))
        .catch((e) => active && setList((prev) => prev.map((x, j) => (j === i ? { ...x, error: e?.response?.status === 404 ? 'not found' : 'error', loading: false } : x))))
    })
    return () => { active = false }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const refreshOne = async (id) => {
    try {
      const d = await getBooking(id)
      setList((prev) => prev.map((x) => (x.id === id ? { ...x, data: d, loading: false, error: null } : x)))
    } catch { /* ignore */ }
  }

  const handleCancel = async () => {
    if (!cancelTarget) return
    setCancelling(true)
    try {
      await cancelBooking(cancelTarget.data.booking_id)
      toast.success('Booking cancelled.')
      await refreshOne(cancelTarget.id)
    } catch (err) {
      toast.error(err?.response?.data?.error || 'Could not cancel booking.')
    } finally {
      setCancelling(false)
      setCancelTarget(null)
    }
  }

  const handleRemove = (id) => {
    removeBooking(user.user_id, id)
    setList((prev) => prev.filter((x) => x.id !== id))
  }

  return (
    <div>
      <PageHeader title="My bookings" subtitle="Bookings saved in this browser" />
      {list.length === 0 ? (
        <Card><div className={shared.note}>No saved bookings yet. Create one from the “New booking” tab.</div></Card>
      ) : (
        <Stack gap="4">
          <div className={`${shared.note} ${shared.noteInfo}`}>Booking history is stored only in this browser. IDs you did not save cannot be recovered.</div>
          {list.map((b) => (
            <Card key={b.id} title="Booking" actions={b.data ? <StatusBadge status={b.data.status} /> : null}>
              {b.loading ? (
                <div className={shared.inline}><Spinner size="sm" /><span className={shared.meta}>Loading…</span></div>
              ) : b.error ? (
                <Stack gap="3">
                  <p className={shared.meta}>This booking could not be loaded ({b.error}). It may have been removed or the ID is invalid.</p>
                  <div><Button variant="ghost" size="sm" onClick={() => handleRemove(b.id)}>Remove from history</Button></div>
                </Stack>
              ) : b.data ? (
                <Stack gap="3">
                  <DetailList items={[
                    { label: 'Booking ID', value: <span className={shared.codeBox}>{b.data.booking_id}</span> },
                    { label: 'Medicine ID', value: <span className={shared.codeBox}>{b.data.medicine_id}</span> },
                    { label: 'Quantity', value: b.data.quantity },
                    { label: 'Urgency', value: b.data.urgency },
                    { label: 'Priority score', value: b.data.priority_score },
                    { label: 'Created', value: formatDateTime(b.data.created_at) },
                    { label: 'Allocated at', value: formatDateTime(b.data.allocated_at) },
                    { label: 'Prescription', value: b.data.prescription_id ? <span className={shared.codeBox}>{b.data.prescription_id}</span> : '—' },
                  ]} />
                  {(b.data.status === 'Requested' || b.data.status === 'Allocated') && (
                    <div><Button variant="danger" size="sm" onClick={() => setCancelTarget(b)}>Cancel booking</Button></div>
                  )}
                  {b.data.status === 'Waitlisted' && (
                    <div className={`${shared.note} ${shared.noteInfo}`}>Waitlisted bookings can only be cancelled by pharmacy staff (the waitlist cancel endpoint needs a waitlist ID not exposed to customers). Please contact staff.</div>
                  )}
                </Stack>
              ) : null}
            </Card>
          ))}
        </Stack>
      )}

      <ConfirmDialog
        open={!!cancelTarget}
        onClose={() => setCancelTarget(null)}
        onConfirm={handleCancel}
        loading={cancelling}
        tone="danger"
        title="Cancel this booking?"
        message="Reserved stock will be released. This cannot be undone."
        confirmLabel="Yes, cancel"
        cancelLabel="Keep"
      />
    </div>
  )
}
