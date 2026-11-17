import client from './client'

// POST /api/prescriptions/submit (Customer)
export async function submitPrescription(payload) {
  const { data } = await client.post('/api/prescriptions/submit', payload)
  return data
}

// GET /api/prescriptions/<id> (owner/Staff/Admin)
export async function getPrescription(id) {
  const { data } = await client.get(`/api/prescriptions/${id}`)
  return data
}

// GET /api/prescriptions/user/<user_id> (owner/Staff/Admin) -> { prescriptions: [] }
export async function getUserPrescriptions(user_id) {
  const { data } = await client.get(`/api/prescriptions/user/${user_id}`)
  return data
}

// PATCH /api/prescriptions/<id>/status (Staff/Admin) { prescription_status }
export async function updatePrescriptionStatus(id, prescription_status) {
  const { data } = await client.patch(`/api/prescriptions/${id}/status`, { prescription_status })
  return data
}
