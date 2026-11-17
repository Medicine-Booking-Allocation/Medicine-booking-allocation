import client from './client'

// Users
export async function getUsers(params = {}) {
  const { data } = await client.get('/api/admin/users', { params })
  return data
}
export async function updateUserRole(user_id, role) {
  const { data } = await client.patch(`/api/admin/users/${user_id}/role`, { role })
  return data
}

// Priority rules
export async function getPriorityRules(params = {}) {
  const { data } = await client.get('/api/admin/priority-rules', { params })
  return data
}
export async function createPriorityRule(payload) {
  const { data } = await client.post('/api/admin/priority-rules', payload)
  return data
}
export async function updatePriorityRule(rule_id, payload) {
  const { data } = await client.patch(`/api/admin/priority-rules/${rule_id}`, payload)
  return data
}

// Audit logs
export async function getAuditLogs(params = {}) {
  const { data } = await client.get('/api/admin/audit-logs', { params })
  return data
}

// Reports
export async function getBookingsReport(params = {}) {
  const { data } = await client.get('/api/admin/reports/bookings', { params })
  return data
}
export async function getAllocationsReport(params = {}) {
  const { data } = await client.get('/api/admin/reports/allocations', { params })
  return data
}
export async function getWaitlistReport(params = {}) {
  const { data } = await client.get('/api/admin/reports/waitlist', { params })
  return data
}
export async function getInventoryReport(params = {}) {
  const { data } = await client.get('/api/admin/reports/inventory', { params })
  return data
}
export async function getPrescriptionsReport(params = {}) {
  const { data } = await client.get('/api/admin/reports/prescriptions', { params })
  return data
}
export async function getNotificationsReport(params = {}) {
  const { data } = await client.get('/api/admin/reports/notifications', { params })
  return data
}
