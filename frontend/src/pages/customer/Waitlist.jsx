import { useEffect, useState } from 'react'
import { useAuth } from '../../hooks/useAuth'
import { getBooking } from '../../api/bookingApi'
import { getBookings } from '../../utils/bookingStore'
import PageHeader from '../../components/PageHeader'
import Card from '../../components/Card'
import Stack from '../../components/Stack'
import StatusBadge from '../../components/StatusBadge'
import Badge from '../../components/Badge'
import Spinner from '../../components/Spinner'
import EmptyState from '../../components/EmptyState'
import shared from '../../styles/shared.module.css'

export default function Waitlist() {
  const { user } = useAuth()
  const saved = getBookings(user?.user_id)
  const [items, setItems] = useState(saved.map((s) => ({ ...s, loading: true, data: null })))

  useEffect(() => {
    let active = true
    saved.forEach((s, i) => {
      getBooking(s.id)
        .then((d) => active && setItems((prev) => prev.map((x, j) => (j === i ? { ...x, data: d, loading: false } : x))))
        .catch(() => active && setItems((prev) => prev.map((x, j) => (j === i ? { ...x, data: null, loading: false } : x))))
    })
    return () => { active = false }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const waitlisted = items.filter((i) => i.data?.status === 'Waitlisted')

  return (
    <div>
      <PageHeader title="Waitlist" subtitle="Your waitlisted bookings and priority" />
      <Stack gap="4">
        <div className={`${shared.note} ${shared.noteInfo}`}>The backend exposes no customer waitlist-listing endpoint. This view shows your saved bookings that are currently Waitlisted, with their priority score. The position shown was captured when the booking was created and may change as others are promoted. You cannot cancel a waitlist entry yourself (staff handle that).</div>
        {waitlisted.length === 0 ? (
          <Card><EmptyState title="No waitlisted bookings" message="None of your saved bookings are currently on the waitlist." /></Card>
        ) : waitlisted.map((b) => (
          <Card key={b.id} title="Waitlisted booking" actions={b.data ? <StatusBadge status="Waitlisted" /> : null}>
            {b.loading ? (
              <div className={shared.inline}><Spinner size="sm" /><span className={shared.meta}>Loading…</span></div>
            ) : b.data ? (
              <Stack gap="3">
                <div className={shared.inline}>
                  <Badge tone="amber" dot>Priority {b.data.priority_score}</Badge>
                  {b.waitlist_position != null && <Badge tone="neutral">Position #{b.waitlist_position} (at creation)</Badge>}
                  <Badge tone="blue">{b.data.urgency}</Badge>
                </div>
                <p className={shared.meta}>Quantity: {b.data.quantity} · Booking ID: <span className={shared.codeBox}>{b.data.booking_id}</span></p>
              </Stack>
            ) : <p className={shared.meta}>Could not load this booking.</p>}
          </Card>
        ))}
      </Stack>
    </div>
  )
}
