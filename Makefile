.DEFAULT_GOAL := help
.PHONY: help up down build rebuild logs ps nginx nginx-tuned fastapi check bench bench-quick \
        install dev build-frontend fastapi-dev clean

URLS := / /any/deep/link /favicon.svg /assets/index.css /assets/index.js /assets/vendor.js /assets/hero.webp

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*## ' $(MAKEFILE_LIST) | awk -F':.*## ' '{printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

# --- Docker ---------------------------------------------------------------

up: ## Build and start all servers (nginx :8080, fastapi :8081, nginx-tuned :8082)
	docker compose up -d --build

down: ## Stop and remove all containers
	docker compose down

build: ## Build all images
	docker compose build

rebuild: ## Rebuild all images without cache
	docker compose build --no-cache

logs: ## Follow logs of all servers
	docker compose logs -f

ps: ## Show running servers
	docker compose ps

nginx: ## Start only nginx (:8080)
	docker compose up -d --build nginx

nginx-tuned: ## Start only nginx-tuned (:8082)
	docker compose up -d --build nginx-tuned

fastapi: ## Start only fastapi (:8081)
	docker compose up -d --build fastapi

check: ## Request every benchmark URL on every server (000 = server down)
	@for port in 8080 8081 8082; do \
		echo "== localhost:$$port"; \
		for url in $(URLS); do \
			curl -s -o /dev/null -H 'Accept: text/html,*/*;q=0.8' -H 'Accept-Encoding: gzip' \
				-w "  %{http_code}  %{size_download}B  $$url\n" "http://localhost:$$port$$url" || true; \
		done; \
	done

bench: up
	python3 bench/bench.py
