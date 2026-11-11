import { useState, useEffect } from 'react'
import { useParams, Link, useNavigate } from 'react-router-dom'
import GameJudgeChat from './GameJudgeChat'

// ─── helpers ────────────────────────────────────────────────────────────────

function Section({ title, children }) {
  return (
    <section style={{ marginBottom: 'var(--space-10)' }}>
      <h2 style={{
        fontSize: 'var(--text-lg)',
        fontWeight: 700,
        marginBottom: 'var(--space-4)',
        paddingBottom: 'var(--space-3)',
        borderBottom: '1px solid var(--divider)',
      }}>
        {title}
      </h2>
      {children}
    </section>
  )
}

function Chip({ label, icon }) {
  return (
    <span style={{
      display: 'inline-flex',
      alignItems: 'center',
      gap: 'var(--space-1)',
      fontSize: 'var(--text-xs)',
      fontWeight: 500,
      background: 'var(--primary-hl)',
      color: 'var(--primary)',
      padding: '2px var(--space-2)',
      borderRadius: '999px',
    }}>
      {icon && <span aria-hidden="true">{icon}</span>}
      {label}
    </span>
  )
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

  if (loading) return (
    <div style={{ padding: 'var(--space-8)' }}>
      <SkeletonLoader />
    </div>
  )
  if (!game) return null

  const groupedRules = (game.rules || []).reduce((acc, r) => {
    ; (acc[r.category] = acc[r.category] || []).push(r)
    return acc
  }, {})

  const groupedSpecialRules = (game.special_rules || []).reduce((acc, r) => {
    const key = r.category || 'General'
      ; (acc[key] = acc[key] || []).push(r)
    return acc
  }, {})

  return (
    <div style={{ maxWidth: '800px' }}>

      {/* ── back link ── */}
      <Link
        to="/"
        style={{
          display: 'inline-flex',
          alignItems: 'center',
          gap: 'var(--space-2)',
          fontSize: 'var(--text-sm)',
          color: 'var(--text-muted)',
          marginBottom: 'var(--space-6)',
          textDecoration: 'none',
        }}
      >
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <path d="M19 12H5M12 19l-7-7 7-7" />
        </svg>
        All games
      </Link>

      {/* ── title row ── */}
      <div style={{
        display: 'flex',
        alignItems: 'flex-start',
        justifyContent: 'space-between',
        gap: 'var(--space-4)',
        marginBottom: 'var(--space-2)',
        flexWrap: 'wrap',
      }}>
        <h1 style={{ fontSize: 'var(--text-xl)', fontWeight: 700 }}>{game.name}</h1>
        <a
          href={`/api/games/${id}/rulebook`}
          target="_blank"
          rel="noreferrer"
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: 'var(--space-2)',
            fontSize: 'var(--text-sm)',
            color: 'var(--primary)',
            background: 'var(--primary-hl)',
            padding: 'var(--space-2) var(--space-3)',
            borderRadius: 'var(--radius-md)',
            textDecoration: 'none',
            flexShrink: 0,
          }}
        >
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
            <polyline points="14 2 14 8 20 8" />
          </svg>
          Rulebook PDF
        </a>
      </div>

      {game.status === 'processing' && (
        <p role="status" style={{ background: 'var(--surface-offset)', borderRadius: 'var(--radius-lg)', padding: 'var(--space-4)', marginBottom: 'var(--space-6)', fontSize: 'var(--text-sm)' }}>
          Reading the rulebook: extracting rules, indexing pages and making a cover. This takes a minute or two.
        </p>
      )}
      {game.status === 'failed' && (
        <p role="alert" style={{ color: 'var(--error)', background: 'var(--surface-offset)', borderRadius: 'var(--radius-lg)', padding: 'var(--space-4)', marginBottom: 'var(--space-6)', fontSize: 'var(--text-sm)' }}>
          Couldn't process this rulebook: {game.error || 'unknown error'}. Delete it and upload again.
        </p>
      )}

      {/* ── meta chips ── */}
      <div style={{
        display: 'flex',
        gap: 'var(--space-3)',
        flexWrap: 'wrap',
        marginBottom: 'var(--space-6)',
      }}>
        {game.min_players != null && (
          <Chip
            icon="👥"
            label={`${game.min_players}${game.max_players ? `–${game.max_players}` : '+'} players`}
          />
        )}
        {game.min_playtime_minutes != null && (
          <Chip
            icon="⏱"
            label={`${game.min_playtime_minutes}${game.max_playtime_minutes && game.max_playtime_minutes !== game.min_playtime_minutes ? `–${game.max_playtime_minutes}` : ''} min`}
          />
        )}
        {game.min_age != null && (
          <Chip icon="🎂" label={`Age ${game.min_age}+`} />
        )}
      </div>

      {/* ── objective ── */}
      {game.objective && (
        <Section title="Objective">
          <p style={{ color: 'var(--text-muted)', lineHeight: 1.7 }}>{game.objective}</p>
        </Section>
      )}

      {/* ── win conditions ── */}
      {game.win_conditions?.length > 0 && (
        <Section title="Win Conditions">
          <ul style={{ paddingLeft: 'var(--space-5)', display: 'flex', flexDirection: 'column', gap: 'var(--space-2)' }}>
            {game.win_conditions.map((w, i) => (
              <li key={i} style={{ color: 'var(--text-muted)' }}>
                {typeof w === 'string' ? w : w.condition ?? w.description ?? JSON.stringify(w)}
              </li>
            ))}
          </ul>
        </Section>
      )}

      {/* ── components ── */}
      {game.components?.length > 0 && (
        <Section title="Components">
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 'var(--text-sm)' }}>
            <thead>
              <tr style={{ borderBottom: '1px solid var(--divider)' }}>
                {['Component', 'Qty', 'Notes'].map(h => (
                  <th
                    key={h}
                    style={{
                      textAlign: 'left',
                      padding: 'var(--space-2) var(--space-3)',
                      color: 'var(--text-muted)',
                      fontWeight: 500,
                    }}
                  >
                    {h}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {game.components.map((c, i) => (
                <tr key={i} style={{ borderBottom: '1px solid var(--divider)' }}>
                  <td style={{ padding: 'var(--space-2) var(--space-3)', fontWeight: 500 }}>{c.name}</td>
                  <td style={{
                    padding: 'var(--space-2) var(--space-3)',
                    color: 'var(--text-muted)',
                    fontVariantNumeric: 'tabular-nums',
                  }}>
                    {c.quantity}
                  </td>
                  <td style={{ padding: 'var(--space-2) var(--space-3)', color: 'var(--text-muted)' }}>
                    {c.description ?? '—'}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </Section>
      )}

      {/* ── setup ── */}
      {game.setup?.length > 0 && (
        <Section title="Setup">
          <ol style={{ paddingLeft: 'var(--space-5)', display: 'flex', flexDirection: 'column', gap: 'var(--space-3)' }}>
            {game.setup.map((s, i) => (
              <li key={i} style={{ color: 'var(--text-muted)', lineHeight: 1.6 }}>
                {typeof s === 'string' ? s : s.instruction ?? s.text ?? JSON.stringify(s)}
              </li>
            ))}
          </ol>
        </Section>
      )}

      {/* ── turn structure ── */}
      {game.turn_structure?.length > 0 && (
        <Section title="Turn Structure">
          <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-3)' }}>
            {game.turn_structure.map((t, i) => (
              <div key={i} style={{ display: 'flex', gap: 'var(--space-4)', alignItems: 'flex-start' }}>
                <span style={{
                  flexShrink: 0,
                  width: '28px', height: '28px',
                  borderRadius: '999px',
                  background: 'var(--primary-hl)',
                  color: 'var(--primary)',
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                  fontSize: 'var(--text-xs)', fontWeight: 700,
                }}>
                  {i + 1}
                </span>
                <div>
                  <p style={{ fontWeight: 600, fontSize: 'var(--text-sm)', marginBottom: '2px' }}>{t.phase}</p>
                  <p style={{ color: 'var(--text-muted)', fontSize: 'var(--text-sm)', lineHeight: 1.6 }}>{t.description}</p>
                </div>
              </div>
            ))}
          </div>
        </Section>
      )}

      {/* ── rules ── */}
      {Object.keys(groupedRules).length > 0 && (
        <Section title="Rules">
          {Object.entries(groupedRules).map(([cat, rules]) => (
            <div key={cat} style={{ marginBottom: 'var(--space-6)' }}>
              <h3 style={{
                fontSize: 'var(--text-sm)',
                fontWeight: 600,
                textTransform: 'uppercase',
                letterSpacing: '0.06em',
                color: 'var(--primary)',
                marginBottom: 'var(--space-3)',
              }}>
                {cat}
              </h3>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-3)' }}>
                {rules.map((r, i) => (
                  <div
                    key={i}
                    style={{
                      background: 'var(--surface-offset)',
                      borderRadius: 'var(--radius-lg)',
                      padding: 'var(--space-4)',
                    }}
                  >
                    <p style={{ fontWeight: 600, marginBottom: 'var(--space-1)', fontSize: 'var(--text-sm)' }}>{r.title}</p>
                    <p style={{ color: 'var(--text-muted)', fontSize: 'var(--text-sm)', lineHeight: 1.6 }}>{r.description}</p>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </Section>
      )}

      {/* ── special rules ── */}
      {Object.keys(groupedSpecialRules).length > 0 && (
        <Section title="Special Rules">
          {Object.entries(groupedSpecialRules).map(([cat, srules]) => (
            <div key={cat} style={{ marginBottom: 'var(--space-6)' }}>
              {/* Only show category heading if there's more than one category */}
              {Object.keys(groupedSpecialRules).length > 1 && (
                <h3 style={{
                  fontSize: 'var(--text-sm)',
                  fontWeight: 600,
                  textTransform: 'uppercase',
                  letterSpacing: '0.06em',
                  color: 'var(--primary)',
                  marginBottom: 'var(--space-3)',
                }}>
                  {cat}
                </h3>
              )}
              <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-3)' }}>
                {srules.map((r, i) => (
                  <div
                    key={i}
                    style={{
                      background: 'var(--surface-offset)',
                      borderRadius: 'var(--radius-lg)',
                      padding: 'var(--space-4)',
                      borderLeft: 'none', // resist the temptation of colored side borders
                    }}
                  >
                    {/* title — may be stored as r.title, r.name, or be a plain string */}
                    {(r.title || r.name) && (
                      <p style={{ fontWeight: 600, marginBottom: 'var(--space-1)', fontSize: 'var(--text-sm)' }}>
                        {r.title ?? r.name}
                      </p>
                    )}
                    <p style={{ color: 'var(--text-muted)', fontSize: 'var(--text-sm)', lineHeight: 1.6 }}>
                      {typeof r === 'string' ? r : (r.description ?? r.rule ?? r.text ?? JSON.stringify(r))}
                    </p>
                    {/* optional "condition" sub-field (e.g. when the rule applies) */}
                    {r.condition && (
                      <p style={{
                        marginTop: 'var(--space-2)',
                        fontSize: 'var(--text-xs)',
                        color: 'var(--primary)',
                        fontWeight: 500,
                      }}>
                        Condition: {r.condition}
                      </p>
                    )}
                  </div>
                ))}
              </div>
            </div>
          ))}
        </Section>
      )}

      {/* ── glossary ── */}
      {game.glossary?.length > 0 && (
        <Section title="Glossary">
          <dl style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-3)' }}>
            {game.glossary.map((g, i) => (
              <div key={i}>
                <dt style={{
                  fontWeight: 600,
                  fontSize: 'var(--text-sm)',
                  color: 'var(--primary)',
                  marginBottom: '2px',
                }}>
                  {g.term}
                </dt>
                <dd style={{
                  color: 'var(--text-muted)',
                  fontSize: 'var(--text-sm)',
                  lineHeight: 1.6,
                  marginLeft: 0,
                }}>
                  {g.definition}
                </dd>
              </div>
            ))}
          </dl>
        </Section>
      )}

      {/* ── metadata footer ── */}
      {game.created_at && (
        <p style={{
          fontSize: 'var(--text-xs)',
          color: 'var(--text-faint, var(--text-muted))',
          marginTop: 'var(--space-4)',
          paddingTop: 'var(--space-4)',
          borderTop: '1px solid var(--divider)',
        }}>
          Added {new Date(game.created_at).toLocaleDateString(undefined, {
            year: 'numeric', month: 'long', day: 'numeric',
          })}
        </p>
      )}
      {/* ── judge chat ── */}
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
