# Umayomi Horse Racing Prediction Service Makefile

.PHONY: dev dev-build format e2e quality-check pre-commit build kill kill-safe test scrape-jra scrape-jra-manual save-jra-html export-firestore export-firestore-force

install:
	pnpm install

# Start all services in development mode (without build)
# - hosting: Vite dev server (http://127.0.0.1:3000)
# - firebase: Firebase emulators (http://127.0.0.1:3100)
dev: install
	-pnpm turbo dev || true

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

# JRAカレンダーデータスクレイピング
scrape-jra-calendar:
	@if [ -z "$(YEAR)" ] || [ -z "$(MONTH)" ]; then \
		echo "Usage: make scrape-jra-calendar YEAR=2025 MONTH=10"; \
		exit 1; \
	fi
	@curl -X GET \
		"http://127.0.0.1:5101/umayomi-fbb2b/us-central1/scrapeJRACalendar?year=$(YEAR)&month=$(MONTH)" \
		--max-time 300 \
		--connect-timeout 10 \
		--retry 3 \
		--retry-delay 1 \
		--show-error \
		--fail-with-body

# JRAレース結果データスクレイピング
scrape-jra-race-result:
	@if [ -z "$(YEAR)" ] || [ -z "$(MONTH)" ] || [ -z "$(DAY)" ]; then \
		echo "Usage: make scrape-jra-race-result YEAR=2025 MONTH=10 DAY=13"; \
		exit 1; \
	fi
	@curl -X GET \
		"http://127.0.0.1:5101/umayomi-fbb2b/us-central1/scrapeJRARaceResult?year=$(YEAR)&month=$(MONTH)&day=$(DAY)" \
		--max-time 300 \
		--connect-timeout 10 \
		--retry 3 \
		--retry-delay 1 \
		--show-error \
		--fail-with-body

# JRAカレンダーとレース結果データ一括スクレイピング
scrape-jra-calendar-with-results:
	@if [ -z "$(YEAR)" ] || [ -z "$(MONTH)" ]; then \
		echo "Usage: make scrape-jra-calendar-with-results YEAR=2025 MONTH=10"; \
		exit 1; \
	fi
	@curl -X GET \
		"http://127.0.0.1:5101/umayomi-fbb2b/us-central1/scrapeJRACalendarWithRaceResults?year=$(YEAR)&month=$(MONTH)" \
		--max-time 600 \
		--connect-timeout 10 \
		--retry 3 \
		--retry-delay 1 \
		--show-error \
		--fail-with-body
