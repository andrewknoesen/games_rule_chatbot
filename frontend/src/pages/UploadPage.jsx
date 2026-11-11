import { useState, useRef } from 'react'
import { useNavigate } from 'react-router-dom'

export default function UploadPage() {
    const [dragging, setDragging] = useState(false)
    const [file, setFile] = useState(null)
    const [status, setStatus] = useState(null) // 'uploading' | 'error'
    const [error, setError] = useState(null)
    const inputRef = useRef(null)
    const navigate = useNavigate()

    const handleFile = (f) => {
        if (f?.type === 'application/pdf') {
            setFile(f)
            setStatus(null)
        }
    }

    const handleUpload = async () => {
        if (!file) return
        setStatus('uploading')
        const form = new FormData()
        form.append('file', file)
        try {
            const res = await fetch('/api/games/upload', { method: 'POST', body: form })
            const body = await res.json().catch(() => ({}))
            if (!res.ok) throw new Error(body.detail || `Upload failed (${res.status})`)
            // The detail page shows progress while the rulebook is processed.
            navigate(`/games/${body.id}`)
        } catch (e) {
            setError(e.message)
            setStatus('error')
        }
    }

    return (
        <div style={{ maxWidth: '600px' }}>
            <h1 style={{ fontSize: 'var(--text-xl)', fontWeight: 700, marginBottom: 'var(--space-6)' }}>
                Upload Rulebook
            </h1>

            {/* Drop zone */}
            <div
                onDragOver={e => { e.preventDefault(); setDragging(true) }}
                onDragLeave={() => setDragging(false)}
                onDrop={e => { e.preventDefault(); setDragging(false); handleFile(e.dataTransfer.files[0]) }}
                onClick={() => inputRef.current?.click()}
                style={{
                    border: `2px dashed ${dragging ? 'var(--primary)' : 'var(--border)'}`,
                    borderRadius: 'var(--radius-xl)',
                    padding: 'var(--space-16) var(--space-8)',
                    textAlign: 'center',
                    cursor: 'pointer',
                    background: dragging ? 'var(--primary-hl)' : 'var(--surface)',
                    transition: 'all var(--transition)',
                    marginBottom: 'var(--space-6)',
                }}
            >
                <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="var(--text-faint)" strokeWidth="1.5" style={{ margin: '0 auto var(--space-3)' }}>
                    <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
                    <polyline points="14 2 14 8 20 8" />
                    <line x1="12" y1="18" x2="12" y2="12" />
                    <line x1="9" y1="15" x2="15" y2="15" />
                </svg>
                <p style={{ fontWeight: 500, marginBottom: 'var(--space-1)' }}>
                    {file ? file.name : 'Drop a PDF here or click to browse'}
                </p>
                <p style={{ fontSize: 'var(--text-xs)', color: 'var(--text-muted)' }}>PDF files only</p>
                <input
                    ref={inputRef}
                    type="file"
                    accept="application/pdf"
                    style={{ display: 'none' }}
                    onChange={e => handleFile(e.target.files[0])}
                />
            </div>

            {/* Upload button — visible when a file is selected and not yet done */}
            {file && (
                <button
                    onClick={handleUpload}
                    disabled={status === 'uploading'}
                    style={{
                        background: 'var(--primary)', color: 'white',
                        padding: 'var(--space-3) var(--space-6)',
                        borderRadius: 'var(--radius-md)', fontWeight: 600,
                        fontSize: 'var(--text-sm)', width: '100%',
                        opacity: status === 'uploading' ? 0.6 : 1,
                    }}
                >
                    {status === 'uploading' ? 'Uploading…' : 'Add game'}
                </button>
            )}

            {/* Error state */}
            {status === 'error' && (
                <p style={{ color: 'var(--error)', fontSize: 'var(--text-sm)' }}>{error}</p>
            )}
        </div>
    )
}
