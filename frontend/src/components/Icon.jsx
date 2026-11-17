/*
 * Compact stroke icon set. `name` matches the names used in nav.js.
 */
const ICONS = {
  dashboard: <path d="M3 13h8V3H3v10zm0 8h8v-6H3v6zm10 0h8V11h-8v10zm0-18v6h8V3h-8z" />,
  search: <><circle cx="11" cy="11" r="7" /><path d="M21 21l-4.3-4.3" /></>,
  plus: <><path d="M12 5v14" /><path d="M5 12h14" /></>,
  booking: <><path d="M6 2h9l5 5v15a1 1 0 0 1-1 1H6a1 1 0 0 1-1-1V3a1 1 0 0 1 1-1z" /><path d="M15 2v5h5" /><path d="M9 13h6" /><path d="M9 17h6" /></>,
  prescription: <><path d="M6 2h9l5 5v15a1 1 0 0 1-1 1H6a1 1 0 0 1-1-1V3a1 1 0 0 1 1-1z" /><path d="M15 2v5h5" /><path d="M8 9h6" /></>,
  waitlist: <><circle cx="12" cy="12" r="9" /><path d="M12 7v5l3 2" /></>,
  bell: <><path d="M18 8a6 6 0 0 0-12 0c0 7-3 9-3 9h18s-3-2-3-9" /><path d="M13.7 21a2 2 0 0 1-3.4 0" /></>,
  inventory: <><path d="M21 16V8l-9-5-9 5v8l9 5 9-5z" /><path d="M3.3 8 12 13l8.7-5" /><path d="M12 22V13" /></>,
  users: <><circle cx="9" cy="8" r="3.2" /><path d="M2.5 20a6.5 6.5 0 0 1 13 0" /><path d="M16 5.5a3 3 0 0 1 0 5.6" /><path d="M17 14a6.5 6.5 0 0 1 4.5 6" /></>,
  rules: <><path d="M4 4h10a2 2 0 0 1 2 2v14H6a2 2 0 0 1-2-2V4z" /><path d="M16 4h4v14a2 2 0 0 1-2 2" /><path d="M7 9h6" /><path d="M7 13h6" /></>,
  audit: <><path d="M9 2h6l1 2h3v16H5V4h3l1-2z" /><path d="M9 12l2 2 4-4" /></>,
  reports: <><path d="M4 20V10" /><path d="M10 20V4" /><path d="M16 20v-7" /><path d="M2 20h20" /></>,
  logout: <><path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4" /><path d="M16 17l5-5-5-5" /><path d="M21 12H9" /></>,
  refresh: <><path d="M21 12a9 9 0 1 1-3-6.7" /><path d="M21 3v5h-5" /></>,
  pill: <><path d="M10.5 3.5 3.5 10.5a5 5 0 0 0 7 7l7-7a5 5 0 0 0-7-7z" /><path d="M7 17 17 7" /></>,
}

export default function Icon({ name, size = 18, className = '' }) {
  const path = ICONS[name] || ICONS.dashboard
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.8"
      strokeLinecap="round"
      strokeLinejoin="round"
      className={className}
      aria-hidden="true"
    >
      {path}
    </svg>
  )
}
