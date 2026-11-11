import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'

export default function Layout({ children }) {
  const [theme, setTheme] = useState(() =>
    window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'
  )

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme)
  }, [theme])

  return (
    <div style={{ minHeight: '100dvh', display: 'flex', flexDirection: 'column' }}>
      <header style={{
        position: 'sticky', top: 0, zIndex: 100,
        background: 'var(--surface)', borderBottom: '1px solid var(--divider)',
        padding: 'var(--space-4) var(--space-6)',
        display: 'flex', alignItems: 'center', justifyContent: 'space-between',
        boxShadow: 'var(--shadow-sm)'
      }}>
        <Link to="/" style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-3)' }}>
          <svg aria-label="Board Games" width="28" height="28" viewBox="0 0 28 28" fill="none">
            <rect x="2" y="2" width="24" height="24" rx="4" stroke="var(--primary)" strokeWidth="2"/>
            <circle cx="9" cy="9" r="2" fill="var(--primary)"/>
            <circle cx="19" cy="9" r="2" fill="var(--primary)"/>
            <circle cx="9" cy="19" r="2" fill="var(--primary)"/>
            <circle cx="19" cy="19" r="2" fill="var(--primary)"/>
            <circle cx="14" cy="14" r="2" fill="var(--text-muted)"/>
          </svg>
          <span style={{ fontWeight: 700, fontSize: 'var(--text-lg)', color: 'var(--text)' }}>
            Board Games
          </span>
        </Link>
        <Link to="/upload" style={{ fontSize: 'var(--text-sm)', color: 'var(--text-muted)', fontWeight: 500 }}>
          + Upload PDF
        </Link>
        <button
          onClick={() => setTheme(t => t === 'dark' ? 'light' : 'dark')}
          aria-label={`Switch to ${theme === 'dark' ? 'light' : 'dark'} mode`}
          style={{ padding: 'var(--space-2)', borderRadius: 'var(--radius-md)', color: 'var(--text-muted)' }}
        >
          {theme === 'dark'
            ? <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="12" cy="12" r="5"/><path d="M12 1v2M12 21v2M4.22 4.22l1.42 1.42M18.36 18.36l1.42 1.42M1 12h2M21 12h2M4.22 19.78l1.42-1.42M18.36 5.64l1.42-1.42"/></svg>
            : <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/></svg>
          }
        </button>
      </header>

      <main style={{ flex: 1, padding: 'var(--space-8) var(--space-6)', maxWidth: '1200px', margin: '0 auto', width: '100%' }}>
        {children}
      </main>
    </div>
  )
}
