/*
 * Maps a backend status string to { label, tone }.
 *
 * tone values are understood by <Badge tone="...">:
 * navy, teal, green, amber, red, blue, neutral
 *
 * Covers every status surfaced across the three portals:
 * booking, prescription, waitlist, notification, account & rule.
 */
export const STATUS_META = {
  // Booking
  Requested: { label: 'Requested', tone: 'neutral' },
  Allocated: { label: 'Allocated', tone: 'blue' },
  Waitlisted: { label: 'Waitlisted', tone: 'amber' },
  Fulfilled: { label: 'Fulfilled', tone: 'green' },
  Cancelled: { label: 'Cancelled', tone: 'red' },
  Rejected: { label: 'Rejected', tone: 'red' },

  // Prescription
  Submitted: { label: 'Submitted', tone: 'neutral' },
  'Under Review': { label: 'Under Review', tone: 'amber' },
  Verified: { label: 'Verified', tone: 'green' },

  // Waitlist entry
  Active: { label: 'Active', tone: 'blue' },
  Promoted: { label: 'Promoted', tone: 'teal' },

  // Notification delivery
  Pending: { label: 'Pending', tone: 'amber' },
  Sent: { label: 'Sent', tone: 'blue' },
  Delivered: { label: 'Delivered', tone: 'green' },

  // Account / rule / general
  Inactive: { label: 'Inactive', tone: 'neutral' },
}

export function statusMeta(status) {
  return STATUS_META[status] || { label: status || '—', tone: 'neutral' }
}
