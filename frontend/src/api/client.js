import axios from 'axios'

/*
 * Axios instance used by every API module in the frontend.
 *
 * baseURL is a relative root ('/'), resolved against the Vite dev-server
 * origin (http://localhost:5173); Vite proxies each request to Flask
 * (http://127.0.0.1:5000) per vite.config.js. withCredentials keeps the Flask
 * session cookie attached to every request.
 *
 * 401 handling: a protected endpoint returning 401 means our session is
 * gone/invalid, so we delegate to a sign-out handler registered by
 * <AuthProvider>. Auth endpoints (/api/auth/*) are excluded so a failed
 * login (401) is handled by the Login form, not a forced redirect.
 */
let unauthorizedHandler = null

export function setUnauthorizedHandler(fn) {
  unauthorizedHandler = typeof fn === 'function' ? fn : null
}

const client = axios.create({
  baseURL: '/',
  withCredentials: true,
})

client.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error?.response?.status === 401) {
      const url = error?.config?.url || ''
      if (!url.includes('/api/auth/')) {
        unauthorizedHandler?.()
      }
    }
    return Promise.reject(error)
  }
)

export default client
