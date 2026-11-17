import client from './client'

/*
 * Auth API — wired to the real Flask endpoints (app/auth.py).
 *
 * register: creates a Customer account. The backend does NOT start a session
 *   on register, so the user must log in afterwards.
 * login:    validates credentials, starts the Flask session, and returns
 *   { message, user_id, role, full_name }.
 * logout:   clears the server-side session.
 */
export function register({ email, password, full_name, phone }) {
  return client.post('/api/auth/register', { email, password, full_name, phone })
}

export function login({ email, password }) {
  return client.post('/api/auth/login', { email, password })
}

export function logout() {
  return client.post('/api/auth/logout')
}
