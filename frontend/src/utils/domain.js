/*
 * Domain constants + small formatters. Values mirror the backend validators.
 */

export const URGENCY_OPTIONS = [
  { value: 'emergency', label: 'Emergency' },
  { value: 'high', label: 'High' },
  { value: 'medium', label: 'Medium' },
  { value: 'low', label: 'Low' },
]

// Prescription status transitions (app/prescription.py)
export const PRESCRIPTION_TRANSITIONS = {
  Submitted: ['Under Review', 'Rejected'],
  'Under Review': ['Verified', 'Rejected'],
  Verified: [],
  Rejected: [],
}

// Notification delivery status transitions (app/notification.py)
export const NOTIFICATION_STATUSES = ['Pending', 'Sent', 'Delivered', 'Failed']
export const NOTIFICATION_STATUS_TRANSITIONS = {
  Pending: ['Sent', 'Failed'],
  Sent: ['Delivered', 'Failed'],
  Failed: [],
  Delivered: [],
}

export const WAITLIST_STATUSES = ['Active', 'Promoted', 'Cancelled', 'Fulfilled']

export const NOTIF_EVENT_TYPES = [
  'Booking', 'Allocation', 'Waitlist', 'Prescription',
  'Fulfilment', 'Inventory', 'Rejection', 'Cancellation',
]

export const ROLES_LIST = ['Customer', 'Pharmacy Staff', 'Administrator']

export function formatDate(iso) {
  if (!iso) return '—'
  const d = new Date(iso)
  if (Number.isNaN(d.getTime())) return iso
  return d.toLocaleDateString(undefined, { year: 'numeric', month: 'short', day: 'numeric' })
}

export function formatDateTime(iso) {
  if (!iso) return '—'
  const d = new Date(iso)
  if (Number.isNaN(d.getTime())) return iso
  return d.toLocaleString(undefined, {
    year: 'numeric', month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit',
  })
}
