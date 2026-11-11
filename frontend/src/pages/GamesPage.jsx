import { useState, useEffect } from 'react'
import GameCard from '../components/GameCard'

export default function GamesPage() {
  const [games, setGames] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  // Refresh every 5 s while any rulebook is still processing.
  useEffect(() => {
    let timer
    const load = () =>
      fetch('/api/games')
        .then(r => { if (!r.ok) throw new Error('Failed to fetch'); return r.json() })
        .then(data => {
          setGames(data); setLoading(false)
          if (data.some(g => g.status === 'processing')) timer = setTimeout(load, 5000)
        })
        .catch(e => { setError(e.message); setLoading(false) })
    load()
    return () => clearTimeout(timer)
  }, [])

  const handleDelete = async (id) => {
    if (!confirm('Delete this game?')) return
    await fetch(`/api/games/${id}`, { method: 'DELETE' })
    setGames(g => g.filter(x => x.id !== id))
  }

  if (loading) return <SkeletonGrid />
  if (error) return <ErrorState message={error} />

  if (games.length === 0) return (
    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', minHeight: '40vh', gap: 'var(--space-4)', color: 'var(--text-muted)', textAlign: 'center' }}>
      <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" style={{ color: 'var(--text-faint)' }}><path d="M3 7h18M3 12h18M3 17h18"/></svg>
      <div>
        <h2 style={{ color: 'var(--text)', marginBottom: 'var(--space-2)' }}>No games yet</h2>
        <p style={{ fontSize: 'var(--text-sm)' }}>Upload a rulebook PDF to add your first game.</p>
      </div>
    </div>
  )

  return (
    <div>
      <div style={{ marginBottom: 'var(--space-8)', display: 'flex', justifyContent: 'space-between', alignItems: 'baseline' }}>
        <h1 style={{ fontSize: 'var(--text-xl)', fontWeight: 700 }}>Game Library</h1>
        <span style={{ fontSize: 'var(--text-sm)', color: 'var(--text-muted)' }}>{games.length} game{games.length !== 1 ? 's' : ''}</span>
      </div>
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fill, minmax(min(320px, 100%), 1fr))',
        gap: 'var(--space-6)'
      }}>
        {games.map(g => <GameCard key={g.id} game={g} onDelete={handleDelete} />)}
      </div>
    </div>
  )
}

function SkeletonGrid() {
  return (
    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(min(320px, 100%), 1fr))', gap: 'var(--space-6)' }}>
      {[...Array(3)].map((_, i) => (
        <div key={i} style={{ background: 'var(--surface)', borderRadius: 'var(--radius-xl)', padding: 'var(--space-6)', display: 'flex', flexDirection: 'column', gap: 'var(--space-3)' }}>
          <Skel w="55%" h="1.4em" />
          <Skel w="100%" h="1em" />
          <Skel w="80%" h="1em" />
          <Skel w="40%" h="1em" />
        </div>
      ))}
    </div>
  )
}

function Skel({ w, h }) {
  return <div style={{ width: w, height: h, borderRadius: 'var(--radius-sm)', background: 'linear-gradient(90deg, var(--surface-offset) 25%, var(--surface-dynamic) 50%, var(--surface-offset) 75%)', backgroundSize: '200% 100%', animation: 'shimmer 1.5s ease-in-out infinite' }} />
}

function ErrorState({ message }) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', minHeight: '40vh', gap: 'var(--space-3)', color: 'var(--text-muted)', textAlign: 'center' }}>
      <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="var(--error)" strokeWidth="1.5"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>
      <p style={{ color: 'var(--text)', fontWeight: 500 }}>Couldn't reach the API</p>
      <p style={{ fontSize: 'var(--text-sm)' }}>{message}</p>
    </div>
  )
}
