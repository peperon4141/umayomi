# Umayomi Horse Racing Prediction Service Makefile

.PHONY: dev dev-build format e2e quality-check pre-commit build kill

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
	pnpm -F umayomi-e2e test

# Run unit tests
test:
	pnpm -F hosting test:run

serve:
	pnpm -F hosting dev:serve

# Build hosting app
build:
	pnpm -F hosting build

# 🚀 統合品質チェック（必須）
quality-check:
	make build
	make format
	make e2e
