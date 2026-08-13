APP_ARGS ?=
COMMIT_MESSAGE ?=
OS ?= $(shell echo %OS%)

ifeq ($(OS),Windows_NT)
	VCPKG_SETUP_SCRIPT := bundle_builder\vcpkg\bootstrap-vcpkg.bat
else
	VCPKG_SETUP_SCRIPT := bundle_builder/vcpkg/bootstrap-vcpkg.sh
endif

.PHONY: setup check format build-package build-image build-bundle build-installer build run

setup:
	@echo "Installing pipx..."
	pip install --user pipx
	pipx ensurepath
	@echo "Installing uv..."
	pipx install uv
	@echo "Installing project..."
	uv sync --frozen
	@echo "Installing git hooks..."
	uv run prek install
	@echo "Cloning submodules..."
	git submodule update --init --recursive
	@echo "Installing vcpkg binary..."
	${VCPKG_SETUP_SCRIPT}
check:
	@echo "Running static type checker..."
	uv run basedpyright
	@echo "Running linter..."
	uv run ruff check
	@echo "Running formatting checker..."
	uv run ruff format --check
format:
	@echo "Running linting fixer..."
	uv run ruff check --fix
	@echo "Running formatter..."
	uv run ruff format
build-package:
	@echo "Building app package..."
	uv build
build-image:
	@echo "Building app image..."
	docker compose build
build-bundle:
	@echo "Building app bundle..."
	uv run python -m bundle_builder
build-installer:
	@echo "Building app installer."
	uv run python -m installer_builder
build: build-package build-image build-bundle build-installer
run:
	@echo "Running app..."
	docker compose run --rm app ${APP_ARGS}
