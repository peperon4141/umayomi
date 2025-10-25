# Umayomi Horse Racing Prediction Service Makefile

.PHONY: dev dev-build format e2e quality-check pre-commit build kill test scrape-jra scrape-jra-manual test-hello

install:
	pnpm install

# Start all services in development mode (without build)
# - hosting: Vite dev server (http://127.0.0.1:3000)
# - firebase: Firebase emulators (http://127.0.0.1:3100)
dev: install
	pnpm turbo dev

# Start all services in development mode with build watch
# - hosting: Vite build watch (outputs to dist/)
# - firebase: Firebase emulators (http://127.0.0.1:3100)
dev-build: install
	pnpm turbo dev-build

# Format and fix linting issues for all repositories
format: install
	pnpm turbo lint:fix
	pnpm -F functions lint:fix

# Run e2e tests
e2e:
	pnpm -F e2e test

# Run unit tests using Turbo
test:
	pnpm turbo test

serve:
	pnpm -F hosting dev:serve

# Build all projects using Turbo
build:
	pnpm turbo build

# 🚀 統合品質チェック（必須）
quality-check:
	make build
	make format
	make e2e

# JRAスクレイピング
scrape-jra:
	@curl -X POST \
		-H "Content-Type: application/json" \
		http://127.0.0.1:5101/umayomi-fbb2b/us-central1/scrapeJRAData \
		--max-time 300 \
		--connect-timeout 10 \
		--retry 3 \
		--retry-delay 1 \
		--show-error \
		--fail-with-body

# 手動JRAスクレイピング
scrape-jra-manual:
	@curl -X POST \
		-H "Content-Type: application/json" \
		-H "Authorization: Bearer admin-token" \
		http://127.0.0.1:5101/umayomi-fbb2b/us-central1/manualJraScraping \
		--max-time 300 \
		--connect-timeout 10 \
		--retry 3 \
		--retry-delay 1 \
		--show-error \
		--fail-with-body

# HelloWorld関数テスト
test-hello:
	@curl -X GET \
		http://127.0.0.1:5101/umayomi-fbb2b/us-central1/helloWorld \
		--max-time 30 \
		--connect-timeout 10 \
		--show-error \
		--fail-with-body
