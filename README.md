# nginx vs FastAPI

The same React SPA served by nginx and by FastAPI `app.frontend()`.

| folder | what |
|---|---|
| [`frontend/`](frontend/README.md) | React + Vite page (mock nginx vs FastAPI comparison) |
| [`nginx/`](nginx/README.md) | nginx image, plain and tuned variants |
| [`fastapi-app/`](fastapi-app/README.md) | FastAPI app (Python 3.14, uv) |
| `bench/` | benchmark script + HTML report template |

Each image builds `frontend/` itself, no local build needed.

## Run

```bash
make up       # docker compose up -d --build
make check    # hit every benchmark URL on all three servers
make bench    # benchmark -> results/<time>/report.html
make down
make          # list all commands
```

| service | URL |
|---|---|
| `nginx` | http://localhost:8080 |
| `fastapi` | http://localhost:8081 |
| `nginx-tuned` | http://localhost:8082 |

All three get the same CPU and memory limits (`SERVER_CPUS`, default 1;
`SERVER_CPUSET`, default `0`).

## Frontend dev

```bash
cd frontend
npm install
npm run dev    # http://localhost:5173
```

## Benchmark

`make bench` runs [oha](https://github.com/hatoo/oha) in Docker against each
server, one at a time: 2s warm-up + 10s measured per URL, 64 connections.
It measures req/s, p99 latency, CPU and peak memory, and writes
`results/<time>/report.html`. Settings are constants at the top of
`bench/bench.py`.
