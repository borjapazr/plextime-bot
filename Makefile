## Root directory
ROOT_DIR := $(shell dirname $(realpath $(lastword $(MAKEFILE_LIST))))

## CI environment
CI_ENVIRONMENT := $(or $(CI),false)

## Service
SERVICE := plextime_bot

## Set 'bash' as default shell
SHELL := $(shell which bash)

## Set 'help' target as the default goal
.DEFAULT_GOAL := help

## Binaries to use in the Makefile ##
DOCKER := DOCKER_BUILDKIT=1 $(shell command -v docker)
DOCKER_COMPOSE := COMPOSE_DOCKER_CLI_BUILD=1 DOCKER_BUILDKIT=1 $(shell command -v docker-compose)
DOCKER_COMPOSE_FILE := $(ROOT_DIR)/docker/docker-compose.yml
ifeq ($(CI_ENVIRONMENT), true)
POETRY := $(shell command -v poetry) -n
else
POETRY := $(shell command -v poetry)
endif

.PHONY: help
help: ## Show this help
	@egrep -h '^[a-zA-Z0-9_\/-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort -d | awk 'BEGIN {FS = ":.*?## "; printf "Usage: make \033[0;34mTARGET\033[0m \033[0;35m[ARGUMENTS]\033[0m\n\n"; printf "Targets:\n"}; {printf "  \033[33m%-25s\033[0m \033[0;32m%s\033[0m\n", $$1, $$2}'

.PHONY: requirements
requirements: ## Check if requirements are satisfied
ifndef DOCKER
	@echo "🐳 Docker is not available. Please install docker."
	@exit 1
endif
ifndef DOCKER_COMPOSE
	@echo "🐳🧩 docker-compose is not available. Please install docker-compose."
	@exit 1
endif
ifndef POETRY
	@echo "📦🧩 poetry is not available. Please install poetry."
	@exit 1
endif
	@echo "🆗 The necessary dependencies are already installed!"

.PHONY: env
env: ## Create .env file from .env.template
	@if [ ! -f .env ]; then cp .env.template .env; fi

.PHONY: install
install: requirements ## Install the poetry environment and install the pre-commit hooks
	@echo "🍿 Installing dependencies and creating virtual environment using pyenv and poetry..."
	@$(POETRY) install
ifneq ($(CI_ENVIRONMENT), true)
	@echo "🚀 Installing pre-commit hooks..."
	@$(POETRY) run pre-commit install
	@$(POETRY) run pre-commit install --hook-type commit-msg --hook-type pre-push
	@$(POETRY) shell
endif

.PHONY: start
start: ## Start the service
	@echo "🚀 Running plextime_bot..."
	@$(POETRY) run plextime_bot

.PHONY: start/docker
start/docker: ## Start the service in a Docker container
	@echo "🚀 Running plextime_bot in a Docker container..."
	@$(DOCKER_COMPOSE) -f $(DOCKER_COMPOSE_FILE) --env-file .env up -d --build

.PHONY: start/docker
stop/docker: ## Stop the service running in a Docker container
	@echo "🛑 Stopping plextime_bot running in a Docker container..."
	@$(DOCKER_COMPOSE) -f $(DOCKER_COMPOSE_FILE) --env-file .env down

.PHONY: build
build: ## Build wheel file using poetry
	@echo "🛞 Creating wheel file"
	@rm -rf dist
	@$(POETRY) build

.PHONY: test
test: ## Test code with PyTest
	@echo "🧪 Testing code..."
	@$(POETRY) run pytest --doctest-modules

.PHONY: types
types: ## Run type checks
	@echo "🖍️ Running static type checking..."
	@$(POETRY) run mypy

.PHONY: format
format: ## Run code formatting
	@echo "💅 Running code formatting..."
	@$(POETRY) run black .

.PHONY: lint
lint: ## Run code linting
	@echo "🤖 Running code linting..."
	@$(POETRY) run ruff check --fix .

.PHONY: dependencies
dependencies: ## Check Poetry lock file consistency and for obsolete dependencies
	@echo "👀 Checking Poetry lock file consistency with 'pyproject.toml'..."
	@$(POETRY) check --lock
	@echo "🚔 Checking for obsolete dependencies..."
	@$(POETRY) run deptry .

.PHONY: logs
logs: ## Show logs for all or c=<name> containers
	@$(DOCKER_COMPOSE) -f $(DOCKER_COMPOSE_FILE) --env-file .env logs --tail=100 -f $(c)

.PHONY: commit
commit: ## Commit changes using conventional commits
	@echo "📝 Committing changes..."
	@$(POETRY) run cz commit

.PHONY: version
version: ## Create a new version and update changelog file
	@echo "📦 Creating a new version..."
	@$(POETRY) run cz bump --changelog
