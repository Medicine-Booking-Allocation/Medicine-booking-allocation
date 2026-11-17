import { useState } from 'react'
import { NavLink, Outlet } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth'
import Icon from './Icon'
import Badge from './Badge'
import Button from './Button'
import styles from './Layout.module.css'

/*
 * App shell shared by all three portals: fixed navy sidebar with nav items,
 * a sticky topbar with the user's name + role + sign out, and a content area
 * that renders the active route via <Outlet />. Sidebar collapses on mobile.
 */
export default function Layout({ navItems, portalName, portalTone = 'navy' }) {
  const { user, logout } = useAuth()
  const [open, setOpen] = useState(false)

  return (
    <div className={styles.app}>
      <aside className={`${styles.sidebar} ${open ? styles.open : ''}`}>
        <div className={styles.brand}>
          <span className={styles.brandMark}><Icon name="pill" size={18} /></span>
          <span className={styles.brandText}>Project 47</span>
        </div>
        <p className={styles.portalName}>{portalName}</p>
        <nav className={styles.nav}>
          {navItems.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.end}
              className={({ isActive }) => `${styles.link} ${isActive ? styles.active : ''}`}
              onClick={() => setOpen(false)}
            >
              <Icon name={item.icon} size={18} />
              <span>{item.label}</span>
            </NavLink>
          ))}
        </nav>
      </aside>

      <div className={styles.main}>
        <header className={styles.topbar}>
          <button className={styles.menuBtn} onClick={() => setOpen((o) => !o)} aria-label="Menu">
            <Icon name="dashboard" size={20} />
          </button>
          <div className={styles.spacer} />
          <div className={styles.userBox}>
            <span className={styles.userName}>{user?.full_name}</span>
            <Badge tone={portalTone} dot>{user?.role}</Badge>
          </div>
          <Button variant="ghost" size="sm" leftIcon={<Icon name="logout" size={16} />} onClick={() => logout()}>
            Sign out
          </Button>
        </header>
        <main className={styles.content}>
          <Outlet />
        </main>
      </div>

      {open && <div className={styles.overlay} onClick={() => setOpen(false)} />}
    </div>
  )
}
