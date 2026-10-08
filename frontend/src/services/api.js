// All backend calls live here. The frontend never sees any API key:
// Gemini and Tavily keys stay in backend/.env.
const BASE = import.meta.env.VITE_API_URL || '/api'
const SESSION_KEY = 'legit-ai-session-id'

function getSessionId() {
  let sessionId = window.sessionStorage.getItem(SESSION_KEY)
  if (!sessionId) {
    sessionId = window.crypto.randomUUID()
    window.sessionStorage.setItem(SESSION_KEY, sessionId)
  }
  return sessionId
}

export class ApiError extends Error {
  constructor(message, status, body) {
    super(message)
    this.status = status
    this.body = body
  }
}

async function request(path, options) {
  let res
  try {
    const headers = new Headers(options?.headers)
    headers.set('X-Session-ID', getSessionId())
    res = await fetch(`${BASE}${path}`, { ...options, headers })
  } catch {
    throw new ApiError('Unable to access this browser session or reach the backend. Check browser storage and start the backend with: uvicorn main:app --port 8000', 0, null)
  }
  const body = await res.json().catch(() => null)
  if (!res.ok) throw new ApiError(body?.message || `Request failed (${res.status})`, res.status, body)
  return body
}

export const getHealth = () => request('/health')
export const getDemos = () => request('/demo')
export const getCases = () => request('/cases')
export const getCase = (id) => request(`/case/${encodeURIComponent(id)}`)
export const runDemo = (id) => request(`/demo/${id}`)

// Every live analysis is a multipart form so the same code path handles text, documents,
// media and optional reference evidence. Keys stay on the backend.
// opts: { text, file, transcript, referenceText, referenceFiles }
export const analyze = (kind, opts) => {
  const form = new FormData()
  if (opts.file) form.append('file', opts.file)
  if (kind === 'text') form.append('text', opts.text || '')
  if (kind === 'image' && opts.transcript) form.append('caption', opts.transcript)
  if ((kind === 'audio' || kind === 'video') && opts.transcript) form.append('transcript', opts.transcript)
  if (opts.referenceText) form.append('reference_text', opts.referenceText)
  ;(opts.referenceFiles || []).forEach((f) => form.append('references', f))
  return request(`/analyze/${kind}`, { method: 'POST', body: form })
}
