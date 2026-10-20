SHELL := /bin/bash

.PHONY: help reference install lint

help:
	@echo "Milestone 1 targets:"
	@echo "  reference   Rebuild the 47-county GeoJSON and CSV from OCHA COD-AB"
	@echo "  install     Install local Python dependencies"
	@echo "  lint        Run ruff"

reference:
	uv run --with shapely python scripts/build_reference_data.py

install:
	uv sync --extra dev

lint:
	uv run ruff check .
