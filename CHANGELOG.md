# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

# 

## [0.2.0] - 2026-02-23

### Added

- Smart API key reuse: When adding models with same endpoint, automatically reuse existing key if not provided
- New pipe commands for Unix-style pipeline processing:
  - `webmdai fetch pipe` - Fetch URLs from stdin
  - `webmdai llm pipe` - Process content from stdin with LLM
  - `webmdai deal pipe` - Replace text in stdin content
- Environment variable support via `.env` files (python-dotenv)
- Comprehensive documentation:
  - `docs/零基础完全指南.md` - Complete beginner's guide
  - `docs/管道使用指南.md` - Pipe usage guide
  - `docs/TODO修复和功能计划.md` - Development roadmap
  - `docs/修复完成报告.md` - Fix completion report

### Fixed

- Windows console encoding error in workflow engine (replaced Unicode symbols `✓` `✗` with ASCII `[OK]` `[FAIL]`)
- Improved network timeout handling with better retry messages and exponential backoff

### Changed

- Updated `requirements.txt` to include `python-dotenv>=1.0.0`
- Enhanced error messages for fetch operations

## [0.1.0] - 2026-02-23

### Added

- Initial release of WebMDAI
- Web content fetching with multiple readers (jina, firecrawl, direct)
- Text processing with regex and plain text replacement
- LLM processing with OpenAI-compatible APIs
- Model management system
- Workflow automation with YAML configuration
- Git integration for automatic backups
- Interactive and batch modes for all commands

### Features

- **Fetch Module**: Download web pages and save as Markdown
  
  - Support for Jina Reader, Firecrawl, and direct fetching
  - Batch and interactive modes
  - Task file support (TASK.md)
  - Separate/together output modes

- **Deal Module**: Text processing and cleaning
  
  - Regex and plain text replacement
  - Preview mode
  - Git automatic backup

- **LLM Module**: AI-powered content processing
  
  - Preset tasks: translate, summarize, explain, abstract
  - Custom prompt support
  - Batch and merge processing modes

- **Workflow Module**: Multi-stage automation
  
  - Stage types: fetch, clean, llm, replace, merge, command, script
  - Variable interpolation
  - Error handling strategies (stop/skip/ignore)
