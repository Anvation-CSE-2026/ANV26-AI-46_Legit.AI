import { ArrowLeft, ArrowRight, Clock3, History as HistoryIcon } from 'lucide-react'

function formatDate(value) {
  const date = new Date(value)
  return Number.isNaN(date.getTime()) ? value : date.toLocaleString()
}

export default function History({ cases, loading, openingCaseId, onOpen, onNavigate }) {
  return (
    <section className="history-content">
      <a href="/" className="back-link" onClick={(event) => onNavigate(event, '/')}>
        <ArrowLeft size={15} aria-hidden /> Back to home
      </a>

      <header className="history-heading">
        <span className="hero-kicker"><HistoryIcon size={14} aria-hidden /> THIS BROWSER SESSION</span>
        <h1>Your analysis history</h1>
        <p>Reopen checks saved during this browser session. Your history is kept separate from other sessions on this device.</p>
      </header>

      {loading ? (
        <p className="history-empty" role="status">Loading your saved checks…</p>
      ) : cases.length === 0 ? (
        <div className="history-empty">
          <Clock3 size={22} aria-hidden />
          <strong>No saved checks yet</strong>
          <span>Completed analyses and sample checks will appear here.</span>
          <a href="/explore" className="history-action" onClick={(event) => onNavigate(event, '/explore')}>
            Start a check <ArrowRight size={15} aria-hidden />
          </a>
        </div>
      ) : (
        <div className="history-list">
          {cases.map((item) => (
            <button
              type="button"
              key={item.case_id}
              className="history-item"
              onClick={() => onOpen(item.case_id)}
              disabled={openingCaseId !== null}
            >
              <span className="history-item-main">
                <strong>{item.input_type} check</strong>
                <span><Clock3 size={13} aria-hidden /> {formatDate(item.created_at)}</span>
              </span>
              <span className="history-item-meta">
                <span className="history-decision">{item.decision}</span>
                <span>{item.mode}</span>
              </span>
              <span className="history-item-open">
                {openingCaseId === item.case_id ? 'Opening…' : 'Open'} <ArrowRight size={15} aria-hidden />
              </span>
            </button>
          ))}
        </div>
      )}
    </section>
  )
}
