import { useState, useRef, useEffect } from 'react'
import ReactMarkdown from 'react-markdown'


export default function GameJudgeChat({ game_id }) {
  const [open, setOpen] = useState(false)
  const [visible, setVisible] = useState(false)  // controls mount/unmount after animation
  const [messages, setMessages] = useState([
    {
      role: 'assistant',
      text: 'Ask me anything about the rules of this game!',
    },
  ])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const bottomRef = useRef(null)
  const inputRef = useRef(null)


  // Mount before animating in; unmount after animating out
  useEffect(() => {
    if (open) {
      setVisible(true)
    } else {
      const t = setTimeout(() => setVisible(false), 220)
      return () => clearTimeout(t)
    }
  }, [open])


  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])


  useEffect(() => {
    if (open) setTimeout(() => inputRef.current?.focus(), 230)
  }, [open])


  async function sendMessage(e) {
    e.preventDefault()
    const question = input.trim()
    if (!question || loading) return


    setInput('')
    setMessages(prev => [...prev, { role: 'user', text: question }])
    setLoading(true)


    try {
      const res = await fetch(`/api/games/${game_id}/ask`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question }),
      })
      if (!res.ok) throw new Error('Judge error')
      const { answer } = await res.json()


      setMessages(prev => [...prev, { role: 'assistant', text: answer.trim() }])
    } catch {
      setMessages(prev => [
        ...prev,
        { role: 'assistant', text: 'Sorry, the judge is unavailable right now. Try again shortly.' },
      ])
    } finally {
      setLoading(false)
    }
  }


  return (
    <>
      <style>{`
        @keyframes judgeSlideIn {
          from { opacity: 0; transform: translateY(16px) scale(0.96); }
          to   { opacity: 1; transform: translateY(0)    scale(1); }
        }
        @keyframes judgeSlideOut {
          from { opacity: 1; transform: translateY(0)    scale(1); }
          to   { opacity: 0; transform: translateY(16px) scale(0.96); }
        }
        @keyframes judgeFabOpen {
          0%   { transform: scale(1); }
          40%  { transform: scale(0.88); }
          100% { transform: scale(1); }
        }
        @keyframes judgeFabClose {
          0%   { transform: scale(1); }
          40%  { transform: scale(0.88); }
          100% { transform: scale(1); }
        }
        @keyframes judgeTyping {
          0%, 80%, 100% { opacity: 0.3; transform: translateY(0); }
          40%           { opacity: 1;   transform: translateY(-4px); }
        }
      `}</style>


      {/* ── floating chat window ── */}
      {visible && (
        <div style={{
          position: 'fixed',
          bottom: 'calc(56px + var(--space-4) + var(--space-3))',
          right: 'var(--space-6)',
          width: '360px',
          maxWidth: 'calc(100vw - var(--space-8))',
          height: '420px',
          display: 'flex',
          flexDirection: 'column',
          border: '1px solid var(--divider)',
          borderRadius: 'var(--radius-lg)',
          overflow: 'hidden',
          background: 'var(--surface)',
          boxShadow: '0 8px 32px oklch(0 0 0 / 0.16)',
          zIndex: 50,
          transformOrigin: 'bottom right',
          animation: `${open ? 'judgeSlideIn' : 'judgeSlideOut'} 220ms cubic-bezier(0.16, 1, 0.3, 1) both`,
        }}>
          {/* header */}
          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: 'var(--space-2)',
            padding: 'var(--space-3) var(--space-4)',
            borderBottom: '1px solid var(--divider)',
            background: 'var(--surface)',
            flexShrink: 0,
          }}>
            <span style={{
              width: '8px', height: '8px',
              borderRadius: '999px',
              background: 'var(--primary)',
              flexShrink: 0,
            }} />
            <span style={{ fontSize: 'var(--text-sm)', fontWeight: 600 }}>Ask the Judge</span>
            <span style={{ fontSize: 'var(--text-xs)', color: 'var(--text-muted)', marginLeft: 'auto' }}>
              AI rules assistant
            </span>
            <button
              onClick={() => setOpen(false)}
              aria-label="Close chat"
              style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                width: '24px', height: '24px',
                borderRadius: 'var(--radius-sm)',
                color: 'var(--text-muted)',
                flexShrink: 0,
              }}
            >
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M18 6L6 18M6 6l12 12" />
              </svg>
            </button>
          </div>


          {/* message list */}
          <div style={{
            flex: 1,
            overflowY: 'auto',
            padding: 'var(--space-4)',
            display: 'flex',
            flexDirection: 'column',
            gap: 'var(--space-3)',
            background: 'var(--surface-offset)',
          }}>
            {messages.map((msg, i) => (
              <div
                key={i}
                style={{
                  display: 'flex',
                  justifyContent: msg.role === 'user' ? 'flex-end' : 'flex-start',
                }}
              >
                <div
                  className={msg.role === 'assistant' ? 'judge-md' : undefined}
                  style={{
                    maxWidth: '80%',
                    padding: 'var(--space-2) var(--space-3)',
                    borderRadius: msg.role === 'user'
                      ? 'var(--radius-lg) var(--radius-lg) var(--radius-sm) var(--radius-lg)'
                      : 'var(--radius-lg) var(--radius-lg) var(--radius-lg) var(--radius-sm)',
                    background: msg.role === 'user' ? 'var(--primary)' : 'var(--surface)',
                    color: msg.role === 'user' ? '#fff' : 'var(--text)',
                    fontSize: 'var(--text-sm)',
                    lineHeight: 1.6,
                    border: msg.role === 'assistant' ? '1px solid var(--divider)' : 'none',
                  }}
                >
                  {msg.role === 'assistant' ? (
                    <ReactMarkdown>{msg.text}</ReactMarkdown>
                  ) : (
                    msg.text
                  )}
                </div>
              </div>
            ))}


            {loading && (
              <div style={{ display: 'flex', justifyContent: 'flex-start' }}>
                <div style={{
                  padding: 'var(--space-2) var(--space-3)',
                  borderRadius: 'var(--radius-lg) var(--radius-lg) var(--radius-lg) var(--radius-sm)',
                  background: 'var(--surface)',
                  border: '1px solid var(--divider)',
                  display: 'flex',
                  gap: 'var(--space-1)',
                  alignItems: 'center',
                }}>
                  {[0, 1, 2].map(n => (
                    <span key={n} style={{
                      width: '6px', height: '6px',
                      borderRadius: '999px',
                      background: 'var(--text-muted)',
                      animation: `judgeTyping 1.2s ease-in-out ${n * 0.2}s infinite`,
                      display: 'inline-block',
                    }} />
                  ))}
                </div>
              </div>
            )}


            <div ref={bottomRef} />
          </div>


          {/* input bar */}
          <form
            onSubmit={sendMessage}
            style={{
              display: 'flex',
              gap: 'var(--space-2)',
              padding: 'var(--space-3) var(--space-4)',
              borderTop: '1px solid var(--divider)',
              background: 'var(--surface)',
              flexShrink: 0,
            }}
          >
            <input
              ref={inputRef}
              type="text"
              value={input}
              onChange={e => setInput(e.target.value)}
              placeholder="Ask a rules question…"
              disabled={loading}
              style={{
                flex: 1,
                fontSize: 'var(--text-sm)',
                padding: 'var(--space-2) var(--space-3)',
                border: '1px solid var(--divider)',
                borderRadius: 'var(--radius-md)',
                background: 'var(--surface-offset)',
                color: 'var(--text)',
                outline: 'none',
              }}
            />
            <button
              type="submit"
              disabled={loading || !input.trim()}
              aria-label="Send question"
              style={{
                flexShrink: 0,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                width: '36px', height: '36px',
                borderRadius: 'var(--radius-md)',
                background: input.trim() && !loading ? 'var(--primary)' : 'var(--surface-offset)',
                color: input.trim() && !loading ? '#fff' : 'var(--text-muted)',
                border: '1px solid var(--divider)',
                cursor: input.trim() && !loading ? 'pointer' : 'not-allowed',
                transition: 'background 180ms ease, color 180ms ease',
              }}
            >
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M22 2L11 13M22 2L15 22l-4-9-9-4 20-7z" />
              </svg>
            </button>
          </form>
        </div>
      )}


      {/* ── FAB trigger button ── */}
      <button
        onClick={() => setOpen(o => !o)}
        aria-label={open ? 'Close judge chat' : 'Ask the judge'}
        style={{
          position: 'fixed',
          bottom: 'var(--space-6)',
          right: 'var(--space-6)',
          width: '56px', height: '56px',
          borderRadius: '999px',
          background: 'var(--primary)',
          color: '#fff',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          boxShadow: '0 4px 16px oklch(0 0 0 / 0.2)',
          zIndex: 51,
          animation: `${open ? 'judgeFabOpen' : 'judgeFabClose'} 220ms cubic-bezier(0.16, 1, 0.3, 1) both`,
          transition: 'background 180ms ease, box-shadow 180ms ease',
        }}
        onMouseEnter={e => {
          e.currentTarget.style.background = 'var(--primary-hover, var(--primary))'
          e.currentTarget.style.boxShadow = '0 6px 24px oklch(0 0 0 / 0.28)'
        }}
        onMouseLeave={e => {
          e.currentTarget.style.background = 'var(--primary)'
          e.currentTarget.style.boxShadow = '0 4px 16px oklch(0 0 0 / 0.2)'
        }}
      >
        {/* Icon cross-fades between chat bubble and X */}
        <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"
          style={{
            position: 'absolute',
            transition: 'opacity 120ms ease',
            opacity: open ? 0 : 1,
          }}>
          <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
        </svg>
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"
          style={{
            position: 'absolute',
            transition: 'opacity 120ms ease',
            opacity: open ? 1 : 0,
          }}>
          <path d="M18 6L6 18M6 6l12 12" />
        </svg>
      </button>
    </>
  )
}
