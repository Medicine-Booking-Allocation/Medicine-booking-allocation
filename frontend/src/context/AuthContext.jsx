import { createContext, useCallback, useEffect, useMemo, useState } from 'react'
import { login as apiLogin, logout as apiLogout, register as apiRegister } from '../api/authApi'
import { setUnauthorizedHandler } from '../api/client'

export const AuthContext = createContext(null)

const STORAGE_KEY = 'p47_user'

function loadUser() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    return raw ? JSON.parse(raw) : null
  } catch {
    return null
  }
}

function saveUser(user) {
  if (user) localStorage.setItem(STORAGE_KEY, JSON.stringify(user))
  else localStorage.removeItem(STORAGE_KEY)
}

/*
 * AuthProvider manages the client-side user record (user_id, role, full_name),
 * persisted to localStorage so the UI survives a page refresh.
 *
 * Authentication truth is the Flask session cookie, not localStorage.
 * The localStorage record only drives which portal/routes we render.
 * On a 401 from any protected endpoint the interceptor calls clearUser()
 * which signs the user out locally and sends them back to /login.
 *
 * Roles: 'Customer', 'Pharmacy Staff', 'Administrator' (from backend).
 */
export function AuthProvider({ children }) {
  const [user, setUser] = useState(loadUser)

  const setAndPersist = useCallback((u) => {
    setUser(u)
    saveUser(u)
  }, [])

  const clearUser = useCallback(() => {
    setUser(null)
    saveUser(null)
  }, [])

  /* Register the 401 interceptor handler immediately. */
  useEffect(() => {
    setUnauthorizedHandler(() => {
      clearUser()
      window.location.replace('/login')
    })
    return () => setUnauthorizedHandler(null)
  }, [clearUser])

  /*
   * register — creates a Customer account (backend does NOT start a session;
   * the user must log in separately after registration).
   */
  const register = useCallback(async ({ email, password, full_name, phone }) => {
    const res = await apiRegister({ email, password, full_name, phone })
    return res.data   // { message, user_id }
  }, [])

  /*
   * login — authenticates the user and starts the Flask session cookie.
   * On success, persists { user_id, role, full_name } to localStorage.
   */
  const login = useCallback(async ({ email, password }) => {
    const res = await apiLogin({ email, password })
    const { user_id, role, full_name } = res.data
    setAndPersist({ user_id, role, full_name })
    return res.data   // { message, user_id, role, full_name }
  }, [setAndPersist])

  /*
   * logout — calls the backend to clear the session, then wipes local state.
   */
  const logout = useCallback(async () => {
    try { await apiLogout() } catch { /* network error — still clear client state */ }
    clearUser()
  }, [clearUser])

  const hasRole = useCallback(
    (...roles) => !!(user && roles.includes(user.role)),
    [user]
  )

  const value = useMemo(
    () => ({ user, login, logout, register, hasRole, clearUser }),
    [user, login, logout, register, hasRole, clearUser]
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}
