import client from './client'

// GET /api/waitlist/ (Staff/Admin) { medicine_id?, status? } -> { total_entries, waitlist: [] }
export async function getWaitlist(params = {}) {
  const { data } = await client.get('/api/waitlist/', { params })
  return data
}

// PATCH /api/waitlist/<waitlist_id>/cancel (owner/Staff/Admin)
export async function cancelWaitlist(waitlist_id) {
  const { data } = await client.patch(`/api/waitlist/${waitlist_id}/cancel`)
  return data
}

// POST /api/waitlist/promote/<medicine_id> (Staff/Admin)
export async function promoteWaitlist(medicine_id) {
  const { data } = await client.post(`/api/waitlist/promote/${medicine_id}`)
  return data
}
