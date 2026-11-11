import { Link } from 'react-router-dom'

export default function GameCard({ game, onDelete }) {
  const coverUrl = game.cover_path ? `/api/games/${game.id}/cover` : null

  return (
    <article style={{
      background: 'var(--surface)',
      border: '1px solid oklch(from var(--text, #28251d) 0.28 0.01 80 / 0.1)',
      borderRadius: 'var(--radius-xl)',
      boxShadow: 'var(--shadow-sm)',
      display: 'flex', flexDirection: 'column',
      overflow: 'hidden',                          // clips the image to card radius
      transition: 'box-shadow var(--transition)',
    }}
    onMouseEnter={e => e.currentTarget.style.boxShadow = 'var(--shadow-md)'}
    onMouseLeave={e => e.currentTarget.style.boxShadow = 'var(--shadow-sm)'}
    >
      {/* Cover image */}
      {coverUrl ? (
        <div style={{ width: '100%', aspectRatio: '4/3', overflow: 'hidden', background: 'var(--surface-offset)' }}>
          <img
            src={coverUrl}
            alt={`${game.name} box art`}
            width={400}
            height={300}
            loading="lazy"
            style={{ width: '100%', height: '100%', objectFit: 'cover', display: 'block' }}
          />
        </div>
      ) : (
        <div style={{
          width: '100%', aspectRatio: '4/3',
          background: 'var(--surface-offset)',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          color: 'var(--text-faint)',
        }}>
          <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
            <rect x="2" y="2" width="24" height="24" rx="4" /><circle cx="8.5" cy="8.5" r="1.5" />
            <polyline points="21 15 16 10 5 21" />
          </svg>
        </div>
      )}

      {/* Card body */}
      <div style={{ padding: 'var(--space-6)', display: 'flex', flexDirection: 'column', gap: 'var(--space-3)', flex: 1 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: 'var(--space-3)' }}>
          <h2 style={{ fontSize: 'var(--text-lg)', fontWeight: 700, color: 'var(--text)', lineHeight: 1.2 }}>
            {game.name}
          </h2>
          <button
            onClick={() => onDelete(game.id)}
            aria-label={`Delete ${game.name}`}
            style={{ color: 'var(--text-faint)', padding: 'var(--space-1)', borderRadius: 'var(--radius-sm)', flexShrink: 0, transition: 'color var(--transition)' }}
            onMouseEnter={e => e.currentTarget.style.color = 'var(--error)'}
            onMouseLeave={e => e.currentTarget.style.color = 'var(--text-faint)'}
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <polyline points="3 6 5 6 21 6" /><path d="M19 6l-1 14H6L5 6" /><path d="M10 11v6M14 11v6" /><path d="M9 6V4h6v2" />
            </svg>
          </button>
        </div>

        <p style={{ fontSize: 'var(--text-sm)', color: 'var(--text-muted)', lineHeight: 1.5 }}>
          {game.objective}
        </p>

        <div style={{ display: 'flex', gap: 'var(--space-3)', flexWrap: 'wrap', marginTop: 'var(--space-2)' }}>
          {game.min_players && (
            <Chip label={`${game.min_players}${game.max_players ? `–${game.max_players}` : '+'} players`} />
          )}
          {game.min_playtime_minutes && <Chip label={`${game.min_playtime_minutes}${game.max_playtime_minutes && game.max_playtime_minutes !== game.min_playtime_minutes ? `–${game.max_playtime_minutes}` : ''} min`} />}
          {game.min_age && <Chip label={`Age ${game.min_age}+`} />}
          {game.status === 'processing' && <Chip label="Processing…" />}
          {game.status === 'failed' && <Chip label="Failed" />}
        </div>

        <Link
          to={`/games/${game.id}`}
          style={{
            marginTop: 'auto', paddingTop: 'var(--space-3)',
            fontSize: 'var(--text-sm)', fontWeight: 500,
            color: 'var(--primary)', display: 'flex', alignItems: 'center', gap: 'var(--space-1)'
          }}
        >
          View full rules
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M5 12h14M12 5l7 7-7 7" /></svg>
        </Link>
      </div>
    </article>
  )
}

function Chip({ label }) {
  return (
    <span style={{
      fontSize: 'var(--text-xs)', fontWeight: 500,
      background: 'var(--primary-hl)', color: 'var(--primary)',
      padding: '2px var(--space-2)', borderRadius: '999px',
    }}>
      {label}
    </span>
  )
}
