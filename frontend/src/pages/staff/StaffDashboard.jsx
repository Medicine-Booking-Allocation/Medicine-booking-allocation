import { useAuth } from '../../hooks/useAuth'
import { searchMedicines } from '../../api/medicineApi'
import { getWaitlist } from '../../api/waitlistApi'
import { getMyNotifications } from '../../api/notificationApi'
import { useAsync } from '../../hooks/useAsync'
import PageHeader from '../../components/PageHeader'
import StatCard from '../../components/StatCard'
import Card from '../../components/Card'
import Stack from '../../components/Stack'
import Grid from '../../components/Grid'
import shared from '../../styles/shared.module.css'

export default function StaffDashboard() {
  const { user } = useAuth()
  const meds = useAsync(() => searchMedicines(''), [])
  const wl = useAsync(() => getWaitlist({ status: 'Active' }), [])
  const notifs = useAsync(() => getMyNotifications(), [])

  return (
    <div>
      <PageHeader title={`Welcome, ${user?.full_name?.split(' ')[0] || 'Staff'}`} subtitle="Inventory, bookings, prescriptions and waitlist" />
      <Stack gap="5">
        <Grid min="200px" gap="4">
          <StatCard label="Active waitlist" value={wl.loading ? '…' : (wl.data?.total_entries ?? 0)} icon="waitlist" tone="amber" hint="Awaiting stock" />
          <StatCard label="Medicines" value={meds.loading ? '…' : (meds.data?.medicines?.length ?? 0)} icon="pill" tone="teal" hint="In catalogue" />
          <StatCard label="Notifications" value={notifs.loading ? '…' : (notifs.data?.notifications?.length ?? 0)} icon="bell" tone="green" />
        </Grid>
        <Card title="Your tools">
          <Stack gap="3">
            <p className={shared.meta}>Add stock (auto-promotes the waitlist), look up bookings by ID to fulfil or cancel, verify prescriptions, and promote the waitlist after replenishment.</p>
            <div className={`${shared.note} ${shared.noteInfo}`}>There is no staff “list all bookings/prescriptions” endpoint — use the manual lookup by ID. Customers can copy their prescription ID to share with you.</div>
          </Stack>
        </Card>
      </Stack>
    </div>
  )
}
