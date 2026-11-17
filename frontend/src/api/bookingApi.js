import client from './client'

// POST /api/bookings/ (Customer) { medicine_id, quantity, urgency, prescription_id? }
export async function createBooking(payload) {
  const { data } = await client.post('/api/bookings/', payload)
  return data
}

// GET /api/bookings/<id> (owner/Staff/Admin)
export async function getBooking(id) {
  const { data } = await client.get(`/api/bookings/${id}`)
  return data
}

// POST /api/bookings/<id>/fulfil (Staff/Admin)
export async function fulfilBooking(id) {
  const { data } = await client.post(`/api/bookings/${id}/fulfil`)
  return data
}

// PATCH /api/bookings/<id>/cancel (owner/Staff/Admin)
export async function cancelBooking(id) {
  const { data } = await client.patch(`/api/bookings/${id}/cancel`)
  return data
}
