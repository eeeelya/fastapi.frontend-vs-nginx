# frontend

React + Vite page: a mock nginx vs FastAPI comparison. nginx and FastAPI images
build it themselves; locally:

```bash
npm install
npm run dev     # http://localhost:5173
npm run build   # -> dist/
```

## Benchmark URLs

File names have no content hash, so these URLs are the same after every build:

| URL | file | size |
|---|---|---|
| `/` | `index.html` | ~0.5 KB |
| `/any/deep/link` | `index.html` (SPA fallback) | ~0.5 KB |
| `/favicon.svg` | SVG icon | ~0.2 KB |
| `/assets/index.css` | styles | ~2 KB |
| `/assets/index.js` | app code | ~4 KB |
| `/assets/vendor.js` | React | ~220 KB |
| `/assets/hero.webp` | hero image | ~215 KB |

Note: without a hash in the name, browsers can't cache these forever, so this
is for benchmarking, not production.
