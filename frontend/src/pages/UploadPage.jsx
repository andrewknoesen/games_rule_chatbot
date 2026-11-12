import { useState, useRef, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import './UploadPage.css'

// Two ways to add a game: find it on BoardGameGeek (the server then looks
// for the official rulebook PDF online), or upload a PDF directly.

async function api(path, options) {
  const res = await fetch(`/api${path}`, options)
  const body = await res.json().catch(() => ({}))
  if (!res.ok) throw new Error(body.detail || `Request failed (${res.status})`)
  return body
}

const mb = bytes => `${(bytes / 1024 / 1024).toFixed(1)} MB`

export default function UploadPage() {
  const [tab, setTab] = useState('bgg')
  const tabs = [
    { id: 'bgg', label: 'Find on BoardGameGeek' },
    { id: 'pdf', label: 'Upload a PDF' },
  ]
  const onKey = e => {
    if (e.key !== 'ArrowRight' && e.key !== 'ArrowLeft') return
    const next = tabs[(tabs.findIndex(t => t.id === tab) + 1) % tabs.length].id
    setTab(next)
    document.getElementById(`add-tab-${next}`)?.focus()
  }

  return (
    <div className="add">
      <h1 className="add-title">Add a game</h1>
      <p className="add-lede">Pick a game on BoardGameGeek and we'll look for its official rulebook, or upload the PDF yourself.</p>

      <div className="add-tabs" role="tablist" aria-label="How to add a game" onKeyDown={onKey}>
        {tabs.map(t => (
          <button
            key={t.id}
            id={`add-tab-${t.id}`}
            role="tab"
            aria-selected={tab === t.id}
            aria-controls={`add-panel-${t.id}`}
            tabIndex={tab === t.id ? 0 : -1}
            onClick={() => setTab(t.id)}
          >
            {t.label}
          </button>
        ))}
      </div>

      <div id={`add-panel-${tab}`} role="tabpanel" aria-labelledby={`add-tab-${tab}`} className="add-panel">
        {tab === 'bgg' ? <FindOnBgg /> : <DropZone />}
      </div>
    </div>
  )
}

// ─── BoardGameGeek flow: search → pick → find rulebook → confirm ────────────

function FindOnBgg() {
  const navigate = useNavigate()
  const [query, setQuery] = useState('')
  const [results, setResults] = useState(null)
  const [searching, setSearching] = useState(false)
  const [picked, setPicked] = useState(null)
  const [stage, setStage] = useState('search') // search | finding | found | missing
  const [candidate, setCandidate] = useState(null)
  const [adding, setAdding] = useState(false)
  const [error, setError] = useState(null)
  const abortRef = useRef(null)

  useEffect(() => () => abortRef.current?.abort(), [])

  const search = async e => {
    e.preventDefault()
    if (query.trim().length < 2) { setError('Type at least two letters.'); return }
    setError(null); setSearching(true)
    try {
      setResults(await api(`/bgg/search?q=${encodeURIComponent(query.trim())}`))
    } catch (err) {
      setError(err.message)
    } finally {
      setSearching(false)
    }
  }

  const pick = async game => {
    setPicked(game); setStage('finding'); setError(null); setCandidate(null)
    const ctrl = new AbortController()
    abortRef.current = ctrl
    try {
      const body = await api(`/bgg/${game.id}/rulebook`, { method: 'POST', signal: ctrl.signal })
      setCandidate(body.candidate)
      setStage(body.candidate ? 'found' : 'missing')
    } catch (err) {
      if (err.name === 'AbortError') return
      setError(err.message)
      setStage('missing')
    }
  }

  const backToResults = () => {
    abortRef.current?.abort()
    setStage('search'); setPicked(null); setCandidate(null); setError(null)
  }

  const useCandidate = async () => {
    setAdding(true); setError(null)
    try {
      const body = await api('/games/from-bgg', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ bgg_id: picked.id, candidate_id: candidate.id }),
      })
      navigate(`/games/${body.id}`)
    } catch (err) {
      setError(err.message); setAdding(false)
    }
  }

  if (stage !== 'search') {
    return (
      <div className="add-flow">
        <button className="add-back" onClick={backToResults}>
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true"><path d="M19 12H5M12 19l-7-7 7-7" /></svg>
          Back to results
        </button>
        <PickedGame game={picked} />

        {stage === 'finding' && (
          <div className="add-finding" role="status">
            <div className="add-progress" aria-hidden="true"><span /></div>
            <p><strong>Looking for the official rulebook…</strong></p>
            <p className="add-soft">Searching the publisher's site and other hosts, then checking the PDF. This usually takes 20 to 60 seconds.</p>
          </div>
        )}

        {stage === 'found' && candidate && (
          <div className="add-candidate">
            <img src={`/api/candidates/${candidate.id}/preview`} alt={`Page 1 of ${candidate.file_name}`} />
            <div>
              <h2>Is this the right rulebook?</h2>
              <dl className="add-meta">
                <div><dt>From</dt><dd>{candidate.host}</dd></div>
                <div><dt>File</dt><dd className="add-file">{candidate.file_name}</dd></div>
                <div><dt>Size</dt><dd>{candidate.pages} {candidate.pages === 1 ? 'page' : 'pages'} · {mb(candidate.size_bytes)}</dd></div>
              </dl>
              <a className="add-link" href={candidate.source_url} target="_blank" rel="noreferrer">Open the PDF to check</a>
              <div className="add-actions">
                <button className="add-btn" onClick={useCandidate} disabled={adding}>
                  {adding ? 'Adding…' : 'Use this rulebook'}
                </button>
                <button className="add-btn ghost" onClick={() => setStage('missing')} disabled={adding}>
                  Not this one
                </button>
              </div>
              {error && <p role="alert" className="add-error">{error}</p>}
            </div>
          </div>
        )}

        {stage === 'missing' && (
          <div className="add-missing">
            <p>
              <strong>{candidate ? 'Upload the right rulebook instead.' : "Couldn't find an official rulebook online."}</strong>{' '}
              {error && <span className="add-error">{error} </span>}
              You can download one from{' '}
              <a className="add-link" href={`https://boardgamegeek.com/boardgame/${picked.id}/x/files`} target="_blank" rel="noreferrer">
                this game's Files page on BoardGameGeek
              </a>{' '}
              and drop it here. The game keeps its BoardGameGeek name and box art.
            </p>
            <DropZone bggId={picked.id} />
          </div>
        )}
      </div>
    )
  }

  return (
    <div>
      <form className="add-search" onSubmit={search} role="search">
        <label htmlFor="bgg-q" className="sr-only">Game name</label>
        <input
          id="bgg-q"
          type="search"
          value={query}
          onChange={e => { setQuery(e.target.value); setError(null) }}
          placeholder="Search for a game, e.g. Catan"
          autoComplete="off"
          autoFocus
        />
        <button className="add-btn" type="submit" disabled={searching}>
          {searching ? 'Searching…' : 'Search'}
        </button>
      </form>
      {error && <p role="alert" className="add-error">{error}</p>}

      {results && results.length === 0 && (
        <p className="add-soft add-empty">No board games on BoardGameGeek match “{query}”. Check the spelling, or upload the PDF instead.</p>
      )}
      {results && results.length > 0 && (
        <ul className="add-results" aria-label="Search results">
          {results.map(g => (
            <li key={g.id}>
              <button onClick={() => pick(g)}>
                {g.thumbnail
                  ? <img src={g.thumbnail} alt="" loading="lazy" />
                  : <span className="add-thumb-empty" aria-hidden="true" />}
                <span className="add-result-text">
                  <strong>{g.name}</strong>
                  <span className="add-soft">{[g.year, g.publishers?.[0]].filter(Boolean).join(' · ')}</span>
                </span>
              </button>
            </li>
          ))}
        </ul>
      )}
      <p className="add-credit">
        Search <a href="https://boardgamegeek.com" target="_blank" rel="noreferrer">powered by BGG</a>
      </p>
    </div>
  )
}

function PickedGame({ game }) {
  return (
    <div className="add-picked">
      {game.thumbnail && <img src={game.thumbnail} alt="" />}
      <div>
        <strong>{game.name}</strong>
        <span className="add-soft">{[game.year, game.publishers?.[0]].filter(Boolean).join(' · ')}</span>
      </div>
    </div>
  )
}

// ─── PDF upload (also the fallback for a picked BGG game) ──────────────────

function DropZone({ bggId }) {
  const [dragging, setDragging] = useState(false)
  const [file, setFile] = useState(null)
  const [uploading, setUploading] = useState(false)
  const [error, setError] = useState(null)
  const inputRef = useRef(null)
  const navigate = useNavigate()

  const handleFile = f => {
    if (!f) return
    if (f.type !== 'application/pdf') { setError('That file isn’t a PDF. Choose the rulebook PDF.'); return }
    setFile(f); setError(null)
  }

  const upload = async () => {
    setUploading(true); setError(null)
    const form = new FormData()
    form.append('file', file)
    if (bggId) form.append('bgg_id', bggId)
    try {
      const body = await api('/games/upload', { method: 'POST', body: form })
      navigate(`/games/${body.id}`) // the game page shows progress
    } catch (err) {
      setError(err.message); setUploading(false)
    }
  }

  return (
    <div>
      <button
        type="button"
        className={`add-drop${dragging ? ' over' : ''}${file ? ' has-file' : ''}`}
        onDragOver={e => { e.preventDefault(); setDragging(true) }}
        onDragLeave={() => setDragging(false)}
        onDrop={e => { e.preventDefault(); setDragging(false); handleFile(e.dataTransfer.files[0]) }}
        onClick={() => inputRef.current?.click()}
      >
        <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" aria-hidden="true">
          <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" /><path d="M14 2v6h6M12 18v-6M9 15l3-3 3 3" />
        </svg>
        <strong>{file ? file.name : 'Drop the rulebook PDF here, or click to choose it'}</strong>
        <span className="add-soft">{file ? mb(file.size) : 'PDF only, up to 50 MB'}</span>
      </button>
      <input ref={inputRef} type="file" accept="application/pdf" hidden onChange={e => handleFile(e.target.files[0])} />
      {file && (
        <button className="add-btn wide" onClick={upload} disabled={uploading}>
          {uploading ? 'Uploading…' : 'Add game'}
        </button>
      )}
      {error && <p role="alert" className="add-error">{error}</p>}
    </div>
  )
}
