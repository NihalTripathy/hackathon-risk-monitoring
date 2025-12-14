# Makefile for easy server management
# Usage: make start, make dev, make prod

.PHONY: start dev prod install help

help:
	@echo "Available commands:"
	@echo "  make install  - Install dependencies"
	@echo "  make start    - Start server (development mode)"
	@echo "  make dev      - Start server with auto-reload"
	@echo "  make prod     - Start server (production mode)"

install:
	pip install -r requirements.txt

start:
	python run.py

dev:
	RELOAD=true python run.py

prod:
	RELOAD=false HOST=0.0.0.0 python run.py

