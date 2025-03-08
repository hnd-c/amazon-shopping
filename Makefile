.PHONY: all format lint test tests test_watch integration_tests docker_tests help extended_tests install setup install-browsers test-amazon test-amazon-all test-main

# Default target executed when no arguments are given to make.
all: help


# Installation targets
install:
	pip install -e ".[dev]"

install-browsers:
	playwright install

setup: install install-browsers
	@echo "Setup complete! Amazon shopping assistant is ready to use."

# Amazon tool testing
test-amazon:
	python -m src.react_agent.amazon_connection.test_tool --test search_basic

test-amazon-all:
	python -m src.react_agent.amazon_connection.test_tool --all

# Test files in tests directory
test-tool:
	python -m tests.test_tool --test search_basic

test-tool-all:
	python -m tests.test_tool --all
######################
# LINTING AND FORMATTING
######################

# Define a variable for Python and notebook files.
PYTHON_FILES=src/
MYPY_CACHE=.mypy_cache
lint format: PYTHON_FILES=.
lint_diff format_diff: PYTHON_FILES=$(shell git diff --name-only --diff-filter=d main | grep -E '\.py$$|\.ipynb$$')
lint_package: PYTHON_FILES=src
lint_tests: PYTHON_FILES=tests
lint_tests: MYPY_CACHE=.mypy_cache_test

lint lint_diff lint_package lint_tests:
	python -m ruff check .
	[ "$(PYTHON_FILES)" = "" ] || python -m ruff format $(PYTHON_FILES) --diff
	[ "$(PYTHON_FILES)" = "" ] || python -m ruff check --select I $(PYTHON_FILES)
	[ "$(PYTHON_FILES)" = "" ] || python -m mypy --strict $(PYTHON_FILES)
	[ "$(PYTHON_FILES)" = "" ] || mkdir -p $(MYPY_CACHE) && python -m mypy --strict $(PYTHON_FILES) --cache-dir $(MYPY_CACHE)

format format_diff:
	ruff format $(PYTHON_FILES)
	ruff check --select I --fix $(PYTHON_FILES)

spell_check:
	codespell --toml pyproject.toml

spell_fix:
	codespell --toml pyproject.toml -w

######################
# HELP
######################

help:
	@echo '----'
	@echo 'setup                        - install package and Playwright browsers'
	@echo 'install                      - install package in development mode'
	@echo 'install-browsers             - install Playwright browsers'
	@echo 'test-amazon                  - run basic Amazon tool test (from src)'
	@echo 'test-amazon-all              - run all Amazon tool tests (from src)'
	@echo 'test-tool                    - run basic tool test (from tests dir)'
	@echo 'test-tool-all                - run all tool tests (from tests dir)'
	@echo 'test-main                    - run basic main test (from tests dir)'
	@echo 'test-main-all                - run all main tests (from tests dir)'
	@echo 'format                       - run code formatters'
	@echo 'lint                         - run linters'
	@echo 'test                         - run unit tests'
	@echo 'tests                        - run unit tests'
	@echo 'test TEST_FILE=<test_file>   - run all tests in file'
	@echo 'test_watch                   - run unit tests in watch mode'

