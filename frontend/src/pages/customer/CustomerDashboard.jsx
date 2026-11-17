import { useAuth } from '../../hooks/useAuth'
import { searchMedicines } from '../../api/medicineApi'
import { getMyNotifications } from '../../api/notificationApi'
import { getBookings } from '../../utils/bookingStore'
import { useAsync } from '../../hooks/useAsync'
import PageHeader from '../../components/PageHeader'
import StatCard from '../../components/StatCard'
import Card from '../../components/Card'
import Stack from '../../components/Stack'
import Grid from '../../components/Grid'
import shared from '../../styles/shared.module.css'

export default function CustomerDashboard() {
  const { user } = useAuth()
  const meds = useAsync(() => searchMedicines(''), [])
  const notifs = useAsync(() => getMyNotifications(), [])
  const savedCount = getBookings(user?.user_id).length

  return (
    <div>
      <PageHeader title={`Welcome, ${user?.full_name?.split(' ')[0] || 'there'}`} subtitle="Your medicine booking overview" />
      <Stack gap="5">
        <Grid min="200px" gap="4">
          <StatCard label="Available medicines" value={meds.loading ? '…' : (meds.data?.medicines?.length ?? 0)} icon="pill" tone="teal" hint="Active in catalogue" />
          <StatCard label="Saved bookings" value={savedCount} icon="booking" tone="navy" hint="Stored in this browser" />
          <StatCard label="Notifications" value={notifs.loading ? '…' : (notifs.data?.notifications?.length ?? 0)} icon="bell" tone="green" hint="Recent activity" />
        </Grid>
        <Card title="Getting started">
          <Stack gap="3">
            <p className={shared.meta}>Search medicines, place bookings with an urgency level, submit prescription reference details when required, and track your allocation status.</p>
            <div className={`${shared.note} ${shared.noteInfo}`}>Booking history is stored only in this browser — the backend has no list-bookings endpoint. Save the booking IDs returned when you create a booking.</div>
          </Stack>
        </Card>
      </Stack>
    </div>
  )
}
