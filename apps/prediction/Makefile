.PHONY: help venv init install dev test clean lint format upgrade-python kernel-list kernel-remove run-notebook

VENV = .venv
# Python 3.12以降を優先的に使用（なければシステムのpython3を使用）
PYTHON3 = $(shell which python3.12 python3.11 python3.10 python3 2>/dev/null | head -1)
PYTHON = $(VENV)/bin/python
PIP = $(VENV)/bin/pip

help:
	@echo "利用可能なコマンド:"
	@echo "  make venv         - 仮想環境を作成"
	@echo "  make init         - 仮想環境を作成して依存関係をインストール（初回セットアップ）"
	@echo "  make install      - 依存関係をインストール（仮想環境が必要）"
	@echo "  make dev          - Jupyter Labを起動（MCPサーバー用、認証なし）"
	@echo "  make test         - テストを実行"
	@echo "  make lint         - 型チェックを実行（pyright）"
	@echo "  make format       - コードフォーマットとリント修正（ruff）"
	@echo "  make upgrade-python - Python 3.12をインストール（Homebrew経由）"
	@echo "  make kernel-list    - 登録されているJupyterカーネル一覧を表示"
	@echo "  make kernel-remove - 登録されているpredictionカーネルを削除"
	@echo "  make run-notebook  - ノートブックをCLIで実行（例: make run-notebook NOTEBOOK=notebooks/train_rank_model.ipynb）"
	@echo "  make clean         - 一時ファイルと仮想環境を削除"

init: venv install

venv:
	@if [ -z "$(PYTHON3)" ]; then \
		echo "エラー: python3が見つかりません"; \
		exit 1; \
	fi
	$(PYTHON3) -m venv $(VENV)
	$(VENV)/bin/pip install --upgrade pip

install:
	@if [ ! -d "$(VENV)" ]; then \
		echo "エラー: 仮想環境が存在しません"; \
		exit 1; \
	fi
	$(PIP) install -r requirements.txt
	@if ! $(PYTHON) -c "import jupyter_collaboration" 2>/dev/null; then \
		echo "jupyter_collaborationをインストール中..."; \
		$(PIP) install jupyter_collaboration; \
	fi
	@PYTHON_VERSION=$$($(PYTHON) --version | cut -d' ' -f2 | cut -d'.' -f1,2); \
	KERNEL_NAME="prediction-py$$PYTHON_VERSION"; \
	DISPLAY_NAME="Python (prediction $$PYTHON_VERSION)"; \
	$(PYTHON) -m ipykernel install --user --name="$$KERNEL_NAME" --display-name="$$DISPLAY_NAME" || true

dev:
	@if [ ! -d "$(VENV)" ]; then \
		echo "エラー: 仮想環境が存在しません"; \
		exit 1; \
	fi
	@if ! $(PYTHON) -c "import jupyter_collaboration" 2>/dev/null; then \
		echo "jupyter_collaborationをインストール中..."; \
		$(PIP) install jupyter_collaboration; \
	fi
	@if lsof -ti :8888 > /dev/null 2>&1; then \
		echo "ポート8888は既に使用されています。既存のJupyterLabプロセスを停止します..."; \
		pkill -f "jupyter lab.*8888" 2>/dev/null || true; \
		sleep 2; \
	fi
	cd notebooks && ../$(PYTHON) -m jupyter lab --port 8888 --ip 127.0.0.1 --ServerApp.token='' --ServerApp.password='' --ServerApp.disable_check_xsrf=True

lint:
	@if ! command -v npx > /dev/null 2>&1; then \
		echo "エラー: npxが見つかりません"; \
		exit 1; \
	fi
	npx pyright src

test:
	@if [ ! -d "$(VENV)" ]; then \
		echo "エラー: 仮想環境が存在しません"; \
		exit 1; \
	fi
	$(PYTHON) -m pytest tests/ -v --tb=short

format:
	@if [ ! -d "$(VENV)" ]; then \
		echo "エラー: 仮想環境が存在しません"; \
		exit 1; \
	fi
	$(PYTHON) -m ruff check --fix --unsafe-fixes src/
	$(PYTHON) -m ruff format src/

run-notebook:
	@if [ ! -d "$(VENV)" ]; then \
		echo "エラー: 仮想環境が存在しません"; \
		exit 1; \
	fi
	@if [ -z "$(NOTEBOOK)" ]; then \
		echo "エラー: NOTEBOOKパラメータが必要です"; \
		exit 1; \
	fi
	@if [ ! -f "$(NOTEBOOK)" ]; then \
		echo "エラー: ファイルが見つかりません: $(NOTEBOOK)"; \
		exit 1; \
	fi
	cd notebooks && ../$(PYTHON) -m jupyter nbconvert --to notebook --execute --inplace --ExecutePreprocessor.timeout=3600 ../$(NOTEBOOK)

kernel-list:
	@if [ -d "$(VENV)" ] && [ -f "$(VENV)/bin/jupyter" ]; then \
		$(VENV)/bin/jupyter kernelspec list; \
	elif command -v jupyter > /dev/null 2>&1; then \
		jupyter kernelspec list; \
	else \
		echo "エラー: Jupyterがインストールされていません"; \
	fi

kernel-remove:
	@JUPYTER_CMD=""; \
	if [ -d "$(VENV)" ] && [ -f "$(VENV)/bin/jupyter" ]; then \
		JUPYTER_CMD="$(VENV)/bin/jupyter"; \
	elif command -v jupyter > /dev/null 2>&1; then \
		JUPYTER_CMD="jupyter"; \
	else \
		echo "エラー: Jupyterがインストールされていません"; \
		exit 1; \
	fi; \
	for kernel in $$($$JUPYTER_CMD kernelspec list 2>/dev/null | grep -E "prediction" | awk '{print $$1}'); do \
		$$JUPYTER_CMD kernelspec remove -f $$kernel || true; \
	done

upgrade-python:
	brew install python@3.12

clean:
	@find . -type d -name "__pycache__" -exec rm -r {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete
	@find . -type f -name "*.pyo" -delete
	@find . -type f -name ".DS_Store" -delete
	@rm -rf $(VENV)
