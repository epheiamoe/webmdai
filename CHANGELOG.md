# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

# 

## [0.3.0] - 2026-02-24

### Added

- **Workflow Wizard Mode** - Interactive guided setup for beginners
  - `webmdai workflow wizard` command for step-by-step configuration
  - Automatically creates TASK.md and workflow.yaml
  - Supports translation, summarization, and custom workflow scenarios

- **Configuration Validation** - Robust workflow config validation
  - Validates required fields: `name`, `stages`
  - Validates each stage has required `type` and `name` fields
  - Checks stage type validity and error handling strategies
  - Clear error messages for configuration issues

- **Smart Error Suggestions** - Intelligent workflow file detection
  - When workflow file not found, suggests available workflow files
  - Searches current directory and subdirectories for workflow*.yaml files
  - Provides actionable hints to run the correct command

- **5-Minute Quick Start Guide** - `QUICKSTART.md` for zero-experience users
  - Scenario-based tutorials (single URL, multiple URLs, existing projects)
  - Common commands cheat sheet
  - FAQ section for first-time users

### Changed

- **Simplified Path Logic** - Auto-detect working directory
  - `workflow run <file>` automatically sets working directory to file's location
  - `--directory` changed to `--working-dir` with clearer semantics
  - No need to specify paths twice when running project workflows
  - Override with `-d` only when needed for custom output directories

### Improved

- Better CLI help messages with usage examples
- Enhanced workflow run command documentation
- README.md updated with wizard mode and path logic explanations

## [0.2.0] - 2026-02-23

### Added

- Custom prompt support via YAML files in `prompts/` directory
  - Load custom tasks from `prompts/*.yaml`
  - Override built-in tasks via YAML
  - Support LLM parameters: temperature, top_p, max_tokens, presence_penalty, frequency_penalty
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
