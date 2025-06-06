# Development Safety MCP Server - Makefile
# Common development tasks

.PHONY: help install test clean example server

help:
	@echo "Development Safety MCP Server"
	@echo "=============================="
	@echo ""
	@echo "Available commands:"
	@echo "  make install  - Install dependencies and initialize"
	@echo "  make test     - Run all tests"
	@echo "  make example  - Run the example workflow"
	@echo "  make server   - Start the MCP server"
	@echo "  make clean    - Clean up temporary files"
	@echo "  make help     - Show this help message"

install:
	@echo "🚀 Initializing Development Safety MCP Server..."
	python init.py

test:
	@echo "🧪 Running tests..."
	python -m pytest tests/ -v

example:
	@echo "📖 Running example workflow..."
	python examples/basic_workflow_example.py

server:
	@echo "🌐 Starting MCP server..."
	python cli.py server

clean:
	@echo "🧹 Cleaning up..."
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf build/ dist/
	@echo "✅ Cleanup completed"

# Development tasks
lint:
	@echo "🔍 Running linting..."
	python -m flake8 src/ tests/ examples/

format:
	@echo "💅 Formatting code..."
	python -m black src/ tests/ examples/

# Package building
build:
	@echo "📦 Building package..."
	python setup.py sdist bdist_wheel

# Quick development setup
dev-setup: install test example
	@echo "✅ Development setup completed!"