/*
 * Persists the customer's booking IDs in localStorage (keyed by user_id).
 *
 * The backend has NO "list my bookings" endpoint, so a customer can only
 * revisit bookings whose IDs they saved. We keep the IDs (and the waitlist
 * position captured at creation time) here. Clearing the browser storage or
 * using another device loses this local history.
 */

const KEY = 'p47_bookings'

function read() {
  try {
    return JSON.parse(localStorage.getItem(KEY)) || {}
  } catch {
    return {}
  }
}

function write(map) {
  localStorage.setItem(KEY, JSON.stringify(map))
}

export function addBooking(user_id, booking_id, waitlist_position = null) {
  if (!user_id || !booking_id) return
  const map = read()
  const arr = map[user_id] || []
  if (!arr.some((b) => b.id === booking_id)) {
    arr.unshift({ id: booking_id, waitlist_position })
  }
  map[user_id] = arr
  write(map)
}

export function getBookings(user_id) {
  if (!user_id) return []
  return read()[user_id] || []
}

export function removeBooking(user_id, booking_id) {
  if (!user_id || !booking_id) return
  const map = read()
  const arr = (map[user_id] || []).filter((b) => b.id !== booking_id)
  map[user_id] = arr
  write(map)
}
