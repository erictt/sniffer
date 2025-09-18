# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Running the Application
```bash
uv run python -m sniffer.main
# or
uv run sniffer
```

### Running Tests
```bash
uv run pytest
```

### CI Pipeline
```bash
make ci
```

### Python Environment
- Python version: 3.13+ (as specified in pyproject.toml)
- Uses `uv` for dependency management
- Dependencies include: moviepy, openai, opencv-python, rich, typer, loguru

## Project Structure

- `sniffer/` - Main package directory
  - `main.py` - CLI entry point with Typer commands
  - `video_processor.py` - Core video processing functionality
  - `transcription.py` - Audio transcription using OpenAI Whisper
  - `config/` - Configuration constants
  - `utils/` - Utility modules (logging, file, directory)
- `tests/` - Test suite with comprehensive coverage
- `data/` - Output directory for processed files

## Coding Principles

- **Single Responsibility** - One concern per component, high cohesion
- **Maintainability** - Independent, modular components
- **Readability** - Clean, self-documenting code with clear naming
- **Modern Python** - Use current language features and idioms
- **Focused Testing** - Core functionality and edge cases only

## Testing

- **Run Tests** - `uv run pytest`
- **CI Pipeline** - `make ci` (includes linting, type checking, coverage)
- **Coverage** - CLI, video processing, transcription, utilities
- **Return Types** - Consistent data structures (dicts/lists)

## Code Review Checklist

1. **Structure** - File organization and architecture
2. **Patterns** - Design patterns and dependencies
3. **Testing** - Coverage and test quality
4. **Documentation** - Code clarity and comments
5. **Reliability** - Error handling and performance
6. **Extensibility** - Future-proof design

## Guidelines

- Do exactly what's requested, nothing more
- Edit existing files rather than creating new ones
- No proactive documentation unless explicitly requested
