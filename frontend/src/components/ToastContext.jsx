import { createContext, useCallback, useContext, useMemo, useState } from 'react'
import Toast from './Toast'
import styles from './ToastContext.module.css'

const ToastCtx = createContext(null)
let counter = 0

/*
 * App-wide toast provider. Usage:
 *   const toast = useToast()
 *   toast.success('Saved.') | toast.error('Failed.') | toast.info(...) | toast.warning(...)
 * Auto-dismisses after `duration` ms (default 4000); set duration: 0 to persist.
 */
export function ToastProvider({ children }) {
  const [toasts, setToasts] = useState([])

  const remove = useCallback((id) => {
    setToasts((t) => t.filter((x) => x.id !== id))
  }, [])

  const show = useCallback(
    (toast) => {
      const id = ++counter
      const duration = toast.duration ?? 4000
      setToasts((t) => [...t, { id, type: toast.type ?? 'info', message: toast.message }])
      if (duration > 0) setTimeout(() => remove(id), duration)
      return id
    },
    [remove]
  )

  const api = useMemo(
    () => ({
      show,
      success: (message, opts = {}) => show({ type: 'success', message, ...opts }),
      error: (message, opts = {}) => show({ type: 'error', message, ...opts }),
      info: (message, opts = {}) => show({ type: 'info', message, ...opts }),
      warning: (message, opts = {}) => show({ type: 'warning', message, ...opts }),
    }),
    [show]
  )

  return (
    <ToastCtx.Provider value={api}>
      {children}
      <div className={styles.viewport} aria-live="polite">
        {toasts.map((t) => (
          <Toast key={t.id} type={t.type} message={t.message} onClose={() => remove(t.id)} />
        ))}
      </div>
    </ToastCtx.Provider>
  )
}

export function useToast() {
  const ctx = useContext(ToastCtx)
  if (!ctx) throw new Error('useToast must be used within ToastProvider')
  return ctx
}
