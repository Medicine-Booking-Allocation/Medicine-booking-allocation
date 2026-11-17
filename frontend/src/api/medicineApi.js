import client from './client'

// GET /api/medicines/search?q=  (public) -> { medicines: [] }
export async function searchMedicines(q = '') {
  const { data } = await client.get('/api/medicines/search', { params: q ? { q } : {} })
  return data
}
