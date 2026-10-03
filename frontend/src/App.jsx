import { useEffect, useState } from 'react'
import hero from './assets/hero.webp'

const SERVERS = [
  { key: 'nginx', label: 'nginx', port: 8080, text: 'nginx 1.29 with sendfile and an SPA fallback (try_files).' },
  { key: 'fastapi', label: 'FastAPI', port: 8081, text: 'One line of Python: app.frontend("/", directory=...) on uvicorn.' },
  { key: 'nginx-tuned', label: 'nginx-tuned', port: 8082, text: 'nginx plus open_file_cache and precompressed .gz files.' },
]

function NginxLogo({ size = 64 }) {
  return (
    <svg width={size} height={size} viewBox="0 0 64 64" aria-label="nginx">
      <path d="M32 4 56 18v28L32 60 8 46V18z" fill="#009639" />
      <path d="M23 44V20l18 24V20" fill="none" stroke="#fff" strokeWidth="5" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  )
}

function FastApiLogo({ size = 64 }) {
  return (
    <svg width={size} height={size} viewBox="0 0 64 64" aria-label="FastAPI">
      <circle cx="32" cy="32" r="28" fill="#05998b" />
      <path d="M35 10 18 36h13l-3 18 18-27H33z" fill="#fff" />
    </svg>
  )
}

// Which server sent this page: "nginx/1.29.8" or "uvicorn" (FastAPI)
function useServer() {
  const [server, setServer] = useState(null)
  useEffect(() => {
    fetch('/', { method: 'HEAD', cache: 'no-store' })
      .then((r) => setServer(r.headers.get('server') || 'unknown'))
      .catch(() => setServer('unknown'))
  }, [])
  return server
}

export default function App() {
  const server = useServer()
  const [selected, setSelected] = useState(SERVERS[0])
  const [clicks, setClicks] = useState(0)

  return (
    <main>
      <header className="hero" style={{ backgroundImage: `url(${hero})` }}>
        <div className="versus">
          <div className="side">
            <NginxLogo size={88} />
            <span>nginx</span>
          </div>
          <div className="vs">vs</div>
          <div className="side">
            <FastApiLogo size={88} />
            <span>FastAPI</span>
          </div>
        </div>
        <h1>Who serves your SPA faster?</h1>
        <p className="sub">This page was served by <b>{server ?? '…'}</b></p>
      </header>

      <nav className="tabs">
        {SERVERS.map((s) => (
          <button key={s.key} className={s.key === selected.key ? 'active' : ''} onClick={() => setSelected(s)}>
            {s.label}
          </button>
        ))}
      </nav>

      <section className="card">
        <div className="card-head">
          {selected.key === 'fastapi' ? <FastApiLogo size={40} /> : <NginxLogo size={40} />}
          <h2>{selected.label}</h2>
        </div>
        <p>{selected.text}</p>
        <a className="open" href={`http://localhost:${selected.port}`}>Open on :{selected.port} →</a>
      </section>

      <section className="card counter">
        <p>A bit of React state, to prove the JS bundle loaded:</p>
        <button onClick={() => setClicks((c) => c + 1)}>Clicked {clicks} times</button>
      </section>

      <footer>
        Real numbers: run <code>make bench</code> and open the HTML report.
      </footer>
    </main>
  )
}
