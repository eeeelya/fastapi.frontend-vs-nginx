# nginx

nginx 1.29 serving the React build from `frontend/` as a SPA
(`try_files $uri $uri/ /index.html`, `/api/*` returns 404).

One Dockerfile, two variants picked by the `EXTRA` build arg:

| service | `EXTRA` | adds |
|---|---|---|
| `nginx` | `extra-none` | nothing, plain config from `nginx.conf` |
| `nginx-tuned` | `extra-tuned` | `open_file_cache` + `gzip_static` (serves the `.gz` files made at build time) |

Files in `extra-*/` are included into the `http {}` block of `nginx.conf`.

## Run

From the repo root:

```bash
docker compose up --build nginx nginx-tuned
```

nginx: http://localhost:8080, nginx-tuned: http://localhost:8082
