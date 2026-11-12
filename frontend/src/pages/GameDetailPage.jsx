import { useState, useEffect, useRef } from 'react'
import { useParams, Link, useNavigate } from 'react-router-dom'
import GameJudgeChat from './GameJudgeChat'
import './GameDetailPage.css'

// ─── helpers ────────────────────────────────────────────────────────────────

const text = (v, ...keys) =>
  typeof v === 'string' ? v : keys.map(k => v?.[k]).find(Boolean) ?? ''

function groupBy(items, fallback) {
  return (items || []).reduce((acc, r) => {
    const key = r.category || fallback
      ; (acc[key] = acc[key] || []).push(r)
    return acc
  }, {})
}

function range(min, max, unit) {
  if (min == null) return null
  return `${min}${max && max !== min ? `–${max}` : ''} ${unit}`
}

const Icon = {
  players: (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" aria-hidden="true">
      <circle cx="9" cy="8" r="3.5" /><path d="M2.5 20a6.5 6.5 0 0 1 13 0" /><path d="M16 4.6a3.5 3.5 0 0 1 0 6.8M18 14a6.5 6.5 0 0 1 3.5 6" />
    </svg>
  ),
  time: (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" aria-hidden="true">
      <circle cx="12" cy="12" r="9" /><path d="M12 7v5l3 2" />
    </svg>
  ),
  age: (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" aria-hidden="true">
      <circle cx="12" cy="7" r="3.5" /><path d="M5 21v-2a7 7 0 0 1 14 0v2" />
    </svg>
  ),
  pdf: (
    <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" aria-hidden="true">
      <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" /><path d="M14 2v6h6M12 12v6M9 15l3 3 3-3" />
    </svg>
  ),
}

// Complexity (1–5) as dice pips, the same motif as the app's logo.
function Weight({ value }) {
  const filled = Math.round(value)
  return (
    <span className="gd-fact" aria-label={`Complexity ${value} out of 5`}>
      <span className="gd-pips" aria-hidden="true">
        {[1, 2, 3, 4, 5].map(n => <span key={n} className={`gd-pip${n <= filled ? ' on' : ''}`} />)}
      </span>
      <span aria-hidden="true">Complexity <span className="gd-num">{value.toFixed(1)}</span></span>
    </span>
  )
}

// Highlights the section in view in the side / top nav.
function useActiveSection(ids) {
  const [active, setActive] = useState(ids[0])
  const key = ids.join(',')
  useEffect(() => {
    if (!ids.length) return
    const seen = new Map()
    const io = new IntersectionObserver(entries => {
      entries.forEach(e => seen.set(e.target.id, e.isIntersecting))
      const first = ids.find(id => seen.get(id))
      if (first) setActive(first)
    }, { rootMargin: '-120px 0px -55% 0px' })
    ids.forEach(id => { const el = document.getElementById(id); if (el) io.observe(el) })
    return () => io.disconnect()
  }, [key])
  return active
}

function RefList({ items }) {
  return (
    <dl className="gd-ref">
      {items.map((r, i) => (
        <div key={i}>
          <dt>{r.title ?? r.name ?? r.term}</dt>
          <dd>
            {text(r, 'description', 'definition', 'rule', 'text')}
            {r.condition && <span className="gd-cond">When: {r.condition}</span>}
          </dd>
        </div>
      ))}
    </dl>
  )
}

function Grouped({ groups, alwaysHead }) {
  const entries = Object.entries(groups)
  return entries.map(([cat, items]) => (
    <div key={cat}>
      {(alwaysHead || entries.length > 1) && <h3>{cat}</h3>}
      <RefList items={items} />
    </div>
  ))
}

// ─── main component ──────────────────────────────────────────────────────────

export default function GameDetailPage() {
  const { id } = useParams()
  const navigate = useNavigate()
  const [game, setGame] = useState(null)
  const [loading, setLoading] = useState(true)

  // Poll while the rulebook is still being ingested.
  useEffect(() => {
    let timer
    const load = () =>
      fetch(`/api/games/${id}`)
        .then(r => { if (!r.ok) throw new Error('Not found'); return r.json() })
        .then(d => {
          setGame(d); setLoading(false)
          if (d.status === 'processing') timer = setTimeout(load, 3000)
        })
        .catch(() => navigate('/'))
    load()
    return () => clearTimeout(timer)
  }, [id])

  const g = game || {}
  const sections = [
    g.components?.length > 0 && {
      id: 'components', title: 'Components', body: (
        <ul className="gd-components">
          {g.components.map((c, i) => (
            <li key={i}>
              <span className="gd-qty">{c.quantity ?? '·'}</span>
              <div><strong>{c.name}</strong>{c.description && <p>{c.description}</p>}</div>
            </li>
          ))}
        </ul>
      ),
    },
    g.setup?.length > 0 && {
      id: 'setup', title: 'Setup', body: (
        <ol className="gd-steps">
          {g.setup.map((s, i) => <li key={i}>{text(s, 'instruction', 'text')}</li>)}
        </ol>
      ),
    },
    g.turn_structure?.length > 0 && {
      id: 'turn', title: 'On your turn', body: (
        <ol className="gd-turn">
          {g.turn_structure.map((t, i) => (
            <li key={i}>
              <span className="gd-turn-dot" aria-hidden="true">{i + 1}</span>
              <strong>{t.phase}</strong>
              <p>{t.description}</p>
            </li>
          ))}
        </ol>
      ),
    },
    g.rules?.length > 0 && {
      id: 'rules', title: 'Rules', body: <Grouped groups={groupBy(g.rules, 'General')} alwaysHead />,
    },
    g.special_rules?.length > 0 && {
      id: 'special', title: 'Special rules', body: <Grouped groups={groupBy(g.special_rules, 'General')} />,
    },
    g.glossary?.length > 0 && {
      id: 'glossary', title: 'Glossary', body: <RefList items={g.glossary} />,
    },
  ].filter(Boolean)

  const active = useActiveSection(sections.map(s => s.id))

  // The app header is sticky and its height changes with width; the section
  // nav sticks right under it.
  const pageRef = useRef(null)
  useEffect(() => {
    const header = document.querySelector('body > #root header')
    const page = pageRef.current
    if (!header || !page) return
    const ro = new ResizeObserver(() => page.style.setProperty('--gd-header', `${header.offsetHeight}px`))
    ro.observe(header)
    return () => ro.disconnect()
  }, [loading])

  if (loading) return (
    <div style={{ padding: 'var(--space-8)' }}>
      <SkeletonLoader />
    </div>
  )
  if (!game) return null

  const cover = game.cover_path ? `/api/games/${id}/cover` : null
  const credits = [game.year_published, game.publisher, game.designer].filter(Boolean).join(' · ')
  const players = range(game.min_players, game.max_players, 'players')
  const time = range(game.min_playtime_minutes, game.max_playtime_minutes, 'min')
  const tags = [...(game.game_types || []), ...(game.game_mechanics || [])]
  const wins = (game.win_conditions || []).map(w => text(w, 'condition', 'description')).filter(Boolean)

  return (
    <div className="gd" ref={pageRef}>
      <Link to="/" className="gd-back">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true">
          <path d="M19 12H5M12 19l-7-7 7-7" />
        </svg>
        All games
      </Link>

      {/* ── hero ── */}
      <header className={`gd-hero${cover ? ' has-cover' : ''}`}>
        {cover && <div className="gd-wash" style={{ backgroundImage: `url(${cover})` }} aria-hidden="true" />}
        {cover && <img className="gd-cover" src={cover} alt={`${game.name} box art`} />}
        <div>
          <h1 className="gd-title">{game.name}</h1>
          {credits && <p className="gd-credits">{credits}</p>}
          {game.description && <p className="gd-desc">{game.description}</p>}

          <div className="gd-facts">
            {players && <span className="gd-fact">{Icon.players}{players}</span>}
            {time && <span className="gd-fact">{Icon.time}{time}</span>}
            {game.min_age != null && <span className="gd-fact">{Icon.age}Ages {game.min_age}+</span>}
            {game.complexity_rating != null && <Weight value={game.complexity_rating} />}
          </div>

          {tags.length > 0 && (
            <ul className="gd-tags" aria-label="Game type and mechanics" style={{ listStyle: 'none' }}>
              {tags.map(t => <li key={t} className="gd-tag">{t}</li>)}
            </ul>
          )}

          <div className="gd-actions">
            <a className="gd-btn" href={`/api/games/${id}/rulebook`} target="_blank" rel="noreferrer">
              {Icon.pdf}Rulebook PDF
            </a>
            {game.bgg_id && (
              <a className="gd-link" href={`https://boardgamegeek.com/boardgame/${game.bgg_id}`} target="_blank" rel="noreferrer" title="Box art from BoardGameGeek">
                Powered by BGG
              </a>
            )}
          </div>

          {game.status === 'processing' && (
            <p role="status" className="gd-banner">
              Reading the rulebook: extracting rules, indexing pages and making a cover. This takes a minute or two.
            </p>
          )}
          {game.status === 'failed' && (
            <p role="alert" className="gd-banner error">
              Couldn't process this rulebook: {game.error || 'unknown error'}. Delete it and upload again.
            </p>
          )}
        </div>
      </header>

      {/* ── how to win ── */}
      {(game.objective || wins.length > 0) && (
        <section className="gd-goal" aria-labelledby="gd-goal-h">
          <div>
            <h2 id="gd-goal-h">How to win</h2>
            {game.objective && <p className="gd-goal-text">{game.objective}</p>}
          </div>
          {wins.length > 0 && (
            <ul aria-label="Win conditions">
              {wins.map((w, i) => <li key={i}>{w}</li>)}
            </ul>
          )}
        </section>
      )}

      {/* ── reference sections ── */}
      {sections.length > 0 && (
        <div className="gd-body">
          <nav className="gd-nav" aria-label="On this page">
            <ol>
              {sections.map(s => (
                <li key={s.id}>
                  <a href={`#${s.id}`} aria-current={active === s.id ? 'true' : undefined}>{s.title}</a>
                </li>
              ))}
            </ol>
          </nav>
          <div className="gd-sections">
            {sections.map(s => (
              <section key={s.id} id={s.id} className="gd-section">
                <h2>{s.title}</h2>
                {s.body}
              </section>
            ))}
            {game.created_at && (
              <p className="gd-added">
                Added {new Date(game.created_at).toLocaleDateString(undefined, { year: 'numeric', month: 'long', day: 'numeric' })}
              </p>
            )}
          </div>
        </div>
      )}

      {game.status === 'ready' && <GameJudgeChat game_id={id} />}
    </div>
  )
}

// ─── skeleton loader ─────────────────────────────────────────────────────────

function SkeletonLoader() {
  const pulse = {
    background: 'var(--surface-offset, #f0f0f0)',
    borderRadius: 'var(--radius-sm, 4px)',
    animation: 'pulse 1.5s ease-in-out infinite',
  }
  return (
    <>
      <style>{`
        @keyframes pulse {
          0%, 100% { opacity: 1; }
          50%       { opacity: 0.4; }
        }
      `}</style>
      <div style={{ ...pulse, height: '14px', width: '80px', marginBottom: 'var(--space-6)' }} />
      <div style={{ ...pulse, height: '32px', width: '60%', marginBottom: 'var(--space-3)' }} />
      <div style={{ display: 'flex', gap: 'var(--space-3)', marginBottom: 'var(--space-8)' }}>
        {[80, 70, 60].map(w => (
          <div key={w} style={{ ...pulse, height: '22px', width: `${w}px`, borderRadius: '999px' }} />
        ))}
      </div>
      {[1, 2, 3].map(i => (
        <div key={i} style={{ marginBottom: 'var(--space-10)' }}>
          <div style={{ ...pulse, height: '20px', width: '30%', marginBottom: 'var(--space-4)' }} />
          <div style={{ ...pulse, height: '14px', width: '100%', marginBottom: 'var(--space-2)' }} />
          <div style={{ ...pulse, height: '14px', width: '85%', marginBottom: 'var(--space-2)' }} />
          <div style={{ ...pulse, height: '14px', width: '70%' }} />
        </div>
      ))}
    </>
  )
}
