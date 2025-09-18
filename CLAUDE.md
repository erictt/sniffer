# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Running the Application
```bash
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
  - `video_processor.py` - Video processing orchestrator (delegates to services)
  - `transcription.py` - Audio transcription using OpenAI Whisper
  - `cli/` - CLI presentation layer
    - `process_handler.py` - Video processing workflow management
    - `display.py` - Rich console output and formatting
  - `services/` - Business logic service layer
    - `video_metadata.py` - Video metadata extraction service
    - `frame_extraction.py` - Frame extraction service with configuration
    - `video_capture.py` - Context-managed video capture for resource safety
  - `config/` - Configuration constants
  - `utils/` - Utility modules (logging, file, directory)
- `tests/` - Test suite with comprehensive coverage (70 tests, 84% coverage)
- `data/` - Output directory for processed files

## Coding Principles

- **Layered Architecture** - Clear separation between CLI, service, and utility layers
- **Single Responsibility** - One concern per component, high cohesion
- **Resource Management** - Proper cleanup with context managers (VideoCapture)
- **Service Composition** - VideoProcessor orchestrates specialized services
- **Maintainability** - Independent, modular components with clean interfaces
- **Readability** - Clean, self-documenting code with clear naming
- **Modern Python** - Type hints, TypedDict, context managers, match statements
- **Comprehensive Testing** - 70 tests with 84% coverage including service layer

## Testing

- **Run Tests** - `uv run pytest`
- **CI Pipeline** - `make ci` (includes linting, type checking, coverage)
- **Coverage** - CLI, video processing, transcription, utilities
- **Return Types** - Consistent data structures (dicts/lists)

## Code Review Checklist

1. **Architecture** - Proper layer separation (CLI → Service → Utils)
2. **Service Layer** - Business logic isolated in services with clear interfaces
3. **Resource Management** - Context managers used for external resources
4. **Dependency Injection** - Services composed rather than tightly coupled
5. **Testing** - Comprehensive coverage including service layer and mocking
6. **Type Safety** - Proper type hints and TypedDict usage
7. **Error Handling** - Graceful failure with resource cleanup
8. **Extensibility** - Plugin-ready architecture for new processing strategies

## Architecture Overview

The codebase follows a **layered architecture** with clear separation of concerns:

### Layer Structure

1. **CLI Layer** (`cli/`)
   - `ProcessHandler` - Orchestrates video processing workflows
   - `DisplayManager` - Handles all Rich console output and formatting
   - Separates user interface from business logic

2. **Service Layer** (`services/`)
   - `VideoMetadataService` - Extracts comprehensive video metadata
   - `FrameExtractionService` - Handles frame extraction with configurable strategies
   - `VideoCapture` - Context manager for safe resource management
   - Contains all business logic, easily testable in isolation

3. **Core Layer** (`video_processor.py`, `transcription.py`)
   - `VideoProcessor` - Orchestrates services for complete video processing
   - `AudioTranscriber` - Handles OpenAI Whisper API integration
   - Maintains public API while delegating to specialized services

4. **Utility Layer** (`utils/`)
   - File operations, directory management, logging
   - Shared functionality across all layers

### Key Architectural Benefits

- **Modularity** - Each service has a single, well-defined responsibility
- **Testability** - Services can be mocked and tested independently
- **Resource Safety** - Context managers ensure proper cleanup
- **Extensibility** - Easy to add new processing strategies or services
- **Maintainability** - Clear boundaries between layers

### Service Composition Pattern

```python
# VideoProcessor composes services rather than inheriting
class VideoProcessor:
    def __init__(self, video_file: Path):
        self.metadata_service = VideoMetadataService()
        self.frame_service = FrameExtractionService()

    def extract_all_frames(self) -> list[str]:
        config = FrameExtractionConfig(video_path=self.video_file, extract_all=True)
        return self.frame_service.extract_all_frames(config)
```

## Guidelines

- Do exactly what's requested, nothing more
- Edit existing files rather than creating new ones
- No proactive documentation unless explicitly requested
- When adding new functionality, follow the established layer patterns
- Use services for business logic, keep CLI layer focused on presentation
- Always use context managers for external resources (files, video capture, etc.)
