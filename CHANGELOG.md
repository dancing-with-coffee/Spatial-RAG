# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Initial release of Spatial-RAG
- Hybrid spatial-semantic retrieval system
- FastAPI backend with PostGIS + pgvector integration
- Next.js frontend with Leaflet map visualization
- BGE local embeddings support
- OpenAI LLM integration with streaming support
- Synthetic data generator for testing
- Docker Compose setup for easy deployment
- Comprehensive documentation

### Changed

- Upgraded OpenAI library from 1.12.0 to 2.8.1 to fix compatibility issues

### Fixed

- Fixed OpenAI client initialization error with proxies parameter
- Fixed Next.js font loading issue (Geist -> Inter/JetBrains Mono)
- Improved error handling and logging in API endpoints

## [1.0.0] - 2024-12-02

### Added

- Initial release

[Unreleased]: https://github.com/AdnanSattar/Spatial-RAG/compare/v1.0.0...HEAD
[1.0.0]: https://github.com/AdnanSattar/Spatial-RAG/releases/tag/v1.0.0
