# Umayomi Horse Racing Prediction Service Makefile

.PHONY: dev format e2e check build test scrape-jra scrape-jra-manual save-jra-html export-firestore export-firestore-force

install:
	pnpm install

# Start all services in development mode (without build)
# - hosting: Vite dev server (http://127.0.0.1:3000)
# - firebase: Firebase emulators (http://127.0.0.1:3100)
dev: install
	pnpm turbo run dev &
	pnpm turbo run build:watch

# Format and fix linting issues for all repositories
format: install
	pnpm turbo lint:fix

# Run e2e tests (with service check)
e2e:
	pnpm turbo e2e

# Run unit tests using Turbo
test:
	pnpm turbo test

# Build all projects using Turbo (including functions, hosting, and shared)
build:
	pnpm turbo build

# 🚀 統合品質チェック（必須）
check:
	make build
	make format
	make test
	make e2e
	make deploy-dry-run

deploy-dry-run:
	pnpm turbo deploy:dry-run

deploy-functions:
	pnpm -F functions run build
	cd apps/functions && pnpm install --prod=false && pnpm exec playwright install chromium && cd ../..
	pnpm exec firebase deploy --config apps/firebase.json --only functions

deploy-firestore:
	pnpm exec firebase deploy --config apps/firebase.json --only firestore

deploy-hosting:
	pnpm -F hosting run build
	pnpm exec firebase deploy --config apps/firebase.json --only hosting

# Firebaseデプロイ
deploy:
	make deploy-functions
	make deploy-firestore
	make deploy-hosting

# JRAカレンダーデータスクレイピング（エミュレーター環境用）
scrape-jra-calendar:
	@if [ -z "$(YEAR)" ] || [ -z "$(MONTH)" ]; then \
		echo "Usage: make scrape-jra-calendar YEAR=2025 MONTH=10"; \
		exit 1; \
	fi
	@curl -X GET \
		"http://127.0.0.1:5101/umayomi-fbb2b/asia-northeast1/scrapeJRACalendar?year=$(YEAR)&month=$(MONTH)" \
		--max-time 300 \
		--connect-timeout 10 \
		--retry 3 \
		--retry-delay 1 \
		--show-error \
		--fail-with-body \
		|| (echo "Error: エミュレーターが起動していることを確認してください (make dev)" && exit 1)

# JRAレース結果データスクレイピング（エミュレーター環境用）
scrape-jra-race-result:
	@if [ -z "$(YEAR)" ] || [ -z "$(MONTH)" ] || [ -z "$(DAY)" ]; then \
		echo "Usage: make scrape-jra-race-result YEAR=2025 MONTH=10 DAY=13"; \
		exit 1; \
	fi
	@curl -X GET \
		"http://127.0.0.1:5101/umayomi-fbb2b/asia-northeast1/scrapeJRARaceResult?year=$(YEAR)&month=$(MONTH)&day=$(DAY)" \
		--max-time 300 \
		--connect-timeout 10 \
		--retry 3 \
		--retry-delay 1 \
		--show-error \
		--fail-with-body \
		|| (echo "Error: エミュレーターが起動していることを確認してください (make dev)" && exit 1)

# JRAカレンダーとレース結果データ一括スクレイピング（エミュレーター環境用）
scrape-jra-calendar-with-results:
	@if [ -z "$(YEAR)" ] || [ -z "$(MONTH)" ]; then \
		echo "Usage: make scrape-jra-calendar-with-results YEAR=2025 MONTH=10"; \
		exit 1; \
	fi
	@curl -X GET \
		"http://127.0.0.1:5101/umayomi-fbb2b/asia-northeast1/scrapeJRACalendarWithRaceResults?year=$(YEAR)&month=$(MONTH)" \
		--max-time 600 \
		--connect-timeout 10 \
		--retry 3 \
		--retry-delay 1 \
		--show-error \
		--fail-with-body \
		|| (echo "Error: エミュレーターが起動していることを確認してください (make dev)" && exit 1)
