import client from './client'

// GET /api/notifications/mine (all) { event_type?, status? } -> { notifications: [] }
export async function getMyNotifications(params = {}) {
  const { data } = await client.get('/api/notifications/mine', { params })
  return data
}

// GET /api/notifications/<id> (owner/Admin) -> { notification: {...} }
export async function getNotification(id) {
  const { data } = await client.get(`/api/notifications/${id}`)
  return data
}

// PATCH /api/notifications/<id>/status (Staff/Admin) { status }
export async function updateNotificationStatus(id, status) {
  const { data } = await client.patch(`/api/notifications/${id}/status`, { status })
  return data
}

// POST /api/notifications/<id>/retry (Staff/Admin)
export async function retryNotification(id) {
  const { data } = await client.post(`/api/notifications/${id}/retry`)
  return data
}
