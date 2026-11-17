import client from './client'

// GET /api/inventory/<medicine_id> (public) -> inventory object
export async function getInventory(medicine_id) {
  const { data } = await client.get(`/api/inventory/${medicine_id}`)
  return data
}

// POST /api/inventory/add (Staff/Admin) { medicine_id, quantity }
export async function addStock(payload) {
  const { data } = await client.post('/api/inventory/add', payload)
  return data
}

// POST /api/inventory/reserve (Staff/Admin)
export async function reserveStock(payload) {
  const { data } = await client.post('/api/inventory/reserve', payload)
  return data
}

// POST /api/inventory/release (Staff/Admin)
export async function releaseStock(payload) {
  const { data } = await client.post('/api/inventory/release', payload)
  return data
}

// POST /api/inventory/fulfil (Staff/Admin) { medicine_id, quantity, booking_id? }
export async function fulfilStock(payload) {
  const { data } = await client.post('/api/inventory/fulfil', payload)
  return data
}
