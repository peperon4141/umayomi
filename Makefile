# Umayomi Horse Racing Prediction Service Makefile

.PHONY: dev format e2e quality-check pre-commit build kill

install:
	pnpm install

# Start all services in development mode
dev: install
	pnpm turbo dev

dev-both:
	pnpm turbo dev
	make serve

# Format and fix linting issues
format: install
	pnpm turbo lint:fix

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

# Deploy commands removed to avoid affecting other Firebase projects

# # Kill all project processes
# kill:
# 	pkill -f "umayomi" || true
# 	pkill -f "firebase.*umayomi-dev" || true

# 🚀 統合品質チェック（必須）
quality-check:
	make build
	make format
	make e2e
