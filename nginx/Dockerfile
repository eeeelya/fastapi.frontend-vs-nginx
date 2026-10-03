# Build the React app from the repo root's frontend/ (build context = repo root).
FROM node:22-alpine AS frontend
WORKDIR /frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
# Precompressed .gz files are used only by nginx-tuned (gzip_static on).
RUN npm run build && \
    find dist -type f \( -name '*.html' -o -name '*.js' -o -name '*.css' -o -name '*.svg' \) \
        -exec gzip -k -9 {} +

FROM nginx:1.29-alpine
# extra-none = plain nginx, extra-tuned = + open_file_cache and gzip_static
ARG EXTRA=extra-none
COPY nginx/nginx.conf /etc/nginx/nginx.conf
COPY nginx/${EXTRA}/ /etc/nginx/extra/
# Files live in the container's own filesystem (overlayfs), not a macOS bind
# mount, so open()/stat() cost what it would on a Linux server.
COPY --from=frontend /frontend/dist /srv/dist
