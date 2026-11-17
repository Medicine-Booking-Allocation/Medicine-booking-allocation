/*
 * Sidebar navigation per portal. `icon` is a name understood by <Icon>.
 */

export const customerNav = [
  { to: '/customer', label: 'Dashboard', icon: 'dashboard', end: true },
  { to: '/customer/medicines', label: 'Medicines', icon: 'search' },
  { to: '/customer/bookings/new', label: 'New booking', icon: 'plus' },
  { to: '/customer/bookings', label: 'My bookings', icon: 'booking' },
  { to: '/customer/prescriptions', label: 'Prescriptions', icon: 'prescription' },
  { to: '/customer/waitlist', label: 'Waitlist', icon: 'waitlist' },
  { to: '/customer/notifications', label: 'Notifications', icon: 'bell' },
]

export const staffNav = [
  { to: '/staff', label: 'Dashboard', icon: 'dashboard', end: true },
  { to: '/staff/inventory', label: 'Inventory', icon: 'inventory' },
  { to: '/staff/bookings', label: 'Bookings', icon: 'booking' },
  { to: '/staff/prescriptions', label: 'Prescriptions', icon: 'prescription' },
  { to: '/staff/waitlist', label: 'Waitlist', icon: 'waitlist' },
  { to: '/staff/notifications', label: 'Notifications', icon: 'bell' },
]

export const adminNav = [
  { to: '/admin', label: 'Dashboard', icon: 'dashboard', end: true },
  { to: '/admin/users', label: 'Users', icon: 'users' },
  { to: '/admin/priority-rules', label: 'Priority rules', icon: 'rules' },
  { to: '/admin/audit-logs', label: 'Audit logs', icon: 'audit' },
  { to: '/admin/reports', label: 'Reports', icon: 'reports' },
  { to: '/admin/notifications', label: 'Notifications', icon: 'bell' },
]
