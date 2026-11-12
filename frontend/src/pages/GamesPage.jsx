import { useState, useEffect, useMemo, useRef } from 'react'
import { useSearchParams, Link } from 'react-router-dom'
import GameCard from '../components/GameCard'
import './GamesPage.css'

// Search, filter and sort run in the browser: the list endpoint already
// returns every game. ponytail: move to query params on GET /games if the
// library ever grows past a few hundred games.

const WEIGHTS = {
  light: { label: 'Light (under 2)', test: c => c < 2 },
  medium: { label: 'Medium (2 to 3)', test: c => c >= 2 && c <= 3 },
  heavy: { label: 'Heavy (over 3)', test: c => c > 3 },
}

const SORTS = {
  added: { label: 'Recently added', cmp: (a, b) => (b.created_at || '').localeCompare(a.created_at || '') },
  name: { label: 'Name (A to Z)', cmp: (a, b) => a.name.localeCompare(b.name) },
  light: { label: 'Lightest first', cmp: (a, b) => (a.complexity_rating ?? 9) - (b.complexity_rating ?? 9) },
  heavy: { label: 'Heaviest first', cmp: (a, b) => (b.complexity_rating ?? -1) - (a.complexity_rating ?? -1) },
  year: { label: 'Newest published', cmp: (a, b) => (b.year_published ?? 0) - (a.year_published ?? 0) },
}

const searchText = g => [
  g.name, g.description, g.objective, g.publisher, g.designer,
  ...(g.game_types || []), ...(g.game_mechanics || []),
].filter(Boolean).join(' ').toLowerCase()

// A missing max means "no upper limit" (shown as 3+ on the card).
const playsWith = (g, n) => g.min_players != null && g.min_players <= n && n <= (g.max_players ?? Infinity)

function applyFilters(games, { q, players, weight, type, sort }) {
  const words = q.toLowerCase().split(/\s+/).filter(Boolean)
  return games
    .filter(g => words.every(w => searchText(g).includes(w)))
    .filter(g => !players || playsWith(g, Number(players)))
    .filter(g => !weight || (g.complexity_rating != null && WEIGHTS[weight]?.test(g.complexity_rating)))
    .filter(g => !type || (g.game_types || []).includes(type))
    .sort((SORTS[sort] || SORTS.added).cmp)
}

export default function GamesPage() {
  const [games, setGames] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [params, setParams] = useSearchParams()
  const filters = {
    q: params.get('q') || '',
    players: params.get('players') || '',
    weight: params.get('weight') || '',
    type: params.get('type') || '',
    sort: params.get('sort') || 'added',
  }
  const setFilter = (key, value) => {
    const next = new URLSearchParams(params)
    if (value && !(key === 'sort' && value === 'added')) next.set(key, value)
    else next.delete(key)
    setParams(next, { replace: true })
  }
  // Clearing keeps the chosen sort order.
  const clearFilters = () => setParams(filters.sort === 'added' ? {} : { sort: filters.sort }, { replace: true })
  const active = filters.q || filters.players || filters.weight || filters.type
  const shown = useMemo(() => applyFilters(games, filters), [games, params])
  const types = useMemo(
    () => [...new Set(games.flatMap(g => g.game_types || []))].sort(),
    [games],
  )

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
        <p style={{ fontSize: 'var(--text-sm)' }}><Link to="/upload" style={{ color: 'var(--primary)' }}>Add your first game</Link> from BoardGameGeek or a rulebook PDF.</p>
      </div>
    </div>
  )

  return (
    <div>
      <div className="lib-head">
        <h1>Game Library</h1>
        <span className="lib-count" aria-live="polite">
          {active ? `${shown.length} of ${games.length}` : games.length} game{games.length !== 1 ? 's' : ''}
        </span>
      </div>

      <Toolbar filters={filters} setFilter={setFilter} types={types} active={active} onClear={clearFilters} />

      {shown.length === 0 ? (
        <div className="lib-empty">
          <p><strong>No games match.</strong></p>
          <p>Try fewer words or loosen a filter.</p>
          <button className="lib-clear" onClick={clearFilters}>Clear search and filters</button>
        </div>
      ) : (
        <div className="lib-grid">
          {shown.map(g => <GameCard key={g.id} game={g} onDelete={handleDelete} />)}
        </div>
      )}
    </div>
  )
}

function Toolbar({ filters, setFilter, types, active, onClear }) {
  const inputRef = useRef(null)
  // "/" jumps to the search box, as on most sites with search.
  useEffect(() => {
    const onKey = e => {
      if (e.key !== '/' || e.target.closest('input, textarea, select')) return
      e.preventDefault(); inputRef.current?.focus()
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [])

  return (
    <div className="lib-toolbar" role="search">
      <label className="lib-search">
        <span className="sr-only">Search games</span>
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" aria-hidden="true">
          <circle cx="11" cy="11" r="7" /><path d="m20 20-3.5-3.5" />
        </svg>
        <input
          ref={inputRef}
          type="search"
          value={filters.q}
          onChange={e => setFilter('q', e.target.value)}
          placeholder="Search by name, type or mechanic"
          autoComplete="off"
        />
        <kbd aria-hidden="true">/</kbd>
      </label>

      <div className="lib-controls">
        <Select label="Players" value={filters.players} onChange={v => setFilter('players', v)}>
          <option value="">Any</option>
          {[1, 2, 3, 4, 5, 6, 7, 8].map(n => <option key={n} value={n}>{n === 1 ? 'Solo' : `${n} players`}</option>)}
        </Select>
        <Select label="Complexity" value={filters.weight} onChange={v => setFilter('weight', v)}>
          <option value="">Any</option>
          {Object.entries(WEIGHTS).map(([k, w]) => <option key={k} value={k}>{w.label}</option>)}
        </Select>
        {types.length > 0 && (
          <Select label="Type" value={filters.type} onChange={v => setFilter('type', v)}>
            <option value="">Any</option>
            {types.map(t => <option key={t} value={t}>{t}</option>)}
          </Select>
        )}
        <Select label="Sort" value={filters.sort} onChange={v => setFilter('sort', v)}>
          {Object.entries(SORTS).map(([k, s]) => <option key={k} value={k}>{s.label}</option>)}
        </Select>
        {active && <button className="lib-clear" onClick={onClear}>Clear</button>}
      </div>
    </div>
  )
}

function Select({ label, value, onChange, children }) {
  return (
    <label className={`lib-select${value && value !== 'added' ? ' set' : ''}`}>
      <span>{label}</span>
      <select value={value} onChange={e => onChange(e.target.value)}>{children}</select>
    </label>
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
