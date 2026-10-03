import { useState } from 'react'
import hero from './assets/hero.webp'

// Mock numbers, only for the design.
const SCENARIOS = {
  index: { label: 'index.html', nginx: { rps: 97400, p99: 1.9, cpu: 10 }, fastapi: { rps: 11800, p99: 14.2, cpu: 84 } },
  js_700k: { label: 'vendor.js 220 KB', nginx: { rps: 8900, p99: 18.4, cpu: 112 }, fastapi: { rps: 2100, p99: 61.0, cpu: 470 } },
  missing: { label: 'SPA fallback', nginx: { rps: 91200, p99: 2.1, cpu: 11 }, fastapi: { rps: 10300, p99: 15.8, cpu: 96 } },
}

const METRICS = [
  { key: 'rps', label: 'Requests / s', unit: '', better: 'high' },
  { key: 'p99', label: 'p99 latency', unit: ' ms', better: 'low' },
  { key: 'cpu', label: 'CPU per request', unit: ' µs', better: 'low' },
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

const fmt = (n) => n.toLocaleString('en-US')

function Bar({ value, max, color }) {
  return (
    <div className="bar">
      <div className="bar-fill" style={{ width: `${(value / max) * 100}%`, background: color }} />
    </div>
  )
}

export default function App() {
  const [scenario, setScenario] = useState('index')
  const data = SCENARIOS[scenario]

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
        <p className="sub">Static file serving benchmark · 1 CPU · 64 keep-alive connections · mock data</p>
      </header>

      <nav className="tabs">
        {Object.entries(SCENARIOS).map(([key, s]) => (
          <button key={key} className={key === scenario ? 'active' : ''} onClick={() => setScenario(key)}>
            {s.label}
          </button>
        ))}
      </nav>

      <section className="cards">
        {METRICS.map((m) => {
          const a = data.nginx[m.key]
          const b = data.fastapi[m.key]
          const max = Math.max(a, b)
          const nginxWins = m.better === 'high' ? a >= b : a <= b
          const ratio = (Math.max(a, b) / Math.min(a, b)).toFixed(1)
          return (
            <article key={m.key} className="card">
              <h2>{m.label}</h2>
              <div className="row">
                <NginxLogo size={22} />
                <Bar value={a} max={max} color="var(--nginx)" />
                <b>{fmt(a)}{m.unit}</b>
              </div>
              <div className="row">
                <FastApiLogo size={22} />
                <Bar value={b} max={max} color="var(--fastapi)" />
                <b>{fmt(b)}{m.unit}</b>
              </div>
              <p className="verdict">
                {nginxWins ? 'nginx' : 'FastAPI'} wins by <strong>{ratio}×</strong>
              </p>
            </article>
          )
        })}
      </section>

      <footer>
        Numbers are placeholders, not real benchmark results.
      </footer>
    </main>
  )
}
