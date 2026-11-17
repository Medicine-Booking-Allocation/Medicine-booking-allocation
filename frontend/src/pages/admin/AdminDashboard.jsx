import { useAuth } from '../../hooks/useAuth'
import { getUsers, getBookingsReport, getInventoryReport, getNotificationsReport } from '../../api/adminApi'
import { useAsync } from '../../hooks/useAsync'
import PageHeader from '../../components/PageHeader'
import StatCard from '../../components/StatCard'
import Card from '../../components/Card'
import Stack from '../../components/Stack'
import Grid from '../../components/Grid'
import Badge from '../../components/Badge'
import shared from '../../styles/shared.module.css'

export default function AdminDashboard() {
  const { user } = useAuth()
  const users = useAsync(() => getUsers(), [])
  const bookings = useAsync(() => getBookingsReport(), [])
  const inv = useAsync(() => getInventoryReport(), [])
  const notifs = useAsync(() => getNotificationsReport(), [])
  const bookingSummary = bookings.data?.status_summary || {}

  return (
    <div>
      <PageHeader title={`Welcome, ${user?.full_name?.split(' ')[0] || 'Admin'}`} subtitle="Platform overview" />
      <Stack gap="5">
        <Grid min="200px" gap="4">
          <StatCard label="Users" value={users.loading ? '…' : (users.data?.total_users ?? 0)} icon="users" tone="navy" />
          <StatCard label="Bookings" value={bookings.loading ? '…' : (bookings.data?.total_bookings ?? 0)} icon="booking" tone="teal" />
          <StatCard label="Inventory records" value={inv.loading ? '…' : (inv.data?.total_inventory_records ?? 0)} icon="inventory" tone="green" />
          <StatCard label="Notifications" value={notifs.loading ? '…' : (notifs.data?.total_notifications ?? 0)} icon="bell" tone="blue" />
        </Grid>
        <Card title="Booking status summary">
          {bookings.loading ? <p className={shared.meta}>Loading…</p> : Object.keys(bookingSummary).length ? (
            <div className={shared.summary}>
              {Object.entries(bookingSummary).map(([s, c]) => <Badge key={s} tone="neutral">{s}: {c}</Badge>)}
            </div>
          ) : <p className={shared.meta}>No bookings recorded.</p>}
        </Card>
      </Stack>
    </div>
  )
}
