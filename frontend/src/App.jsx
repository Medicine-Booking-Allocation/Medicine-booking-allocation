import { Routes, Route } from 'react-router-dom'
import Landing from './pages/public/Landing'
import Login from './pages/public/Login'
import Register from './pages/public/Register'
import NotFound from './pages/public/NotFound'
import Styleguide from './pages/Styleguide'
import Layout from './components/Layout'
import RoleRoute from './components/RoleRoute'
import { customerNav, staffNav, adminNav } from './utils/nav'
import { ROLES } from './utils/constants'

// Customer portal
import CustomerDashboard from './pages/customer/CustomerDashboard'
import Medicines from './pages/customer/Medicines'
import NewBooking from './pages/customer/NewBooking'
import Bookings from './pages/customer/Bookings'
import Prescriptions from './pages/customer/Prescriptions'
import Waitlist from './pages/customer/Waitlist'
import Notifications from './pages/customer/Notifications'

// Pharmacy staff portal
import StaffDashboard from './pages/staff/StaffDashboard'
import Inventory from './pages/staff/Inventory'
import StaffBookings from './pages/staff/StaffBookings'
import PrescriptionReview from './pages/staff/PrescriptionReview'
import StaffWaitlist from './pages/staff/StaffWaitlist'
import StaffNotifications from './pages/staff/StaffNotifications'

// Admin portal
import AdminDashboard from './pages/admin/AdminDashboard'
import Users from './pages/admin/Users'
import PriorityRules from './pages/admin/PriorityRules'
import AuditLogs from './pages/admin/AuditLogs'
import Reports from './pages/admin/Reports'
import AdminNotifications from './pages/admin/AdminNotifications'

/*
 * Top-level routes. Public pages + the temporary design preview, then three
 * role-gated portals. Each portal uses <Layout> (sidebar + topbar) with <Outlet/>.
 */
export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Landing />} />
      <Route path="/login" element={<Login />} />
      <Route path="/register" element={<Register />} />
      <Route path="/styleguide" element={<Styleguide />} />

      <Route path="/customer" element={<RoleRoute role={ROLES.CUSTOMER}><Layout navItems={customerNav} portalName="Customer Portal" portalTone="teal" /></RoleRoute>}>
        <Route index element={<CustomerDashboard />} />
        <Route path="medicines" element={<Medicines />} />
        <Route path="bookings/new" element={<NewBooking />} />
        <Route path="bookings" element={<Bookings />} />
        <Route path="prescriptions" element={<Prescriptions />} />
        <Route path="waitlist" element={<Waitlist />} />
        <Route path="notifications" element={<Notifications />} />
      </Route>

      <Route path="/staff" element={<RoleRoute role={ROLES.STAFF}><Layout navItems={staffNav} portalName="Pharmacy Staff Portal" portalTone="blue" /></RoleRoute>}>
        <Route index element={<StaffDashboard />} />
        <Route path="inventory" element={<Inventory />} />
        <Route path="bookings" element={<StaffBookings />} />
        <Route path="prescriptions" element={<PrescriptionReview />} />
        <Route path="waitlist" element={<StaffWaitlist />} />
        <Route path="notifications" element={<StaffNotifications />} />
      </Route>

      <Route path="/admin" element={<RoleRoute role={ROLES.ADMIN}><Layout navItems={adminNav} portalName="Admin Portal" portalTone="navy" /></RoleRoute>}>
        <Route index element={<AdminDashboard />} />
        <Route path="users" element={<Users />} />
        <Route path="priority-rules" element={<PriorityRules />} />
        <Route path="audit-logs" element={<AuditLogs />} />
        <Route path="reports" element={<Reports />} />
        <Route path="notifications" element={<AdminNotifications />} />
      </Route>

      <Route path="*" element={<NotFound />} />
    </Routes>
  )
}
