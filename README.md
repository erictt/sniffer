# 🎬 Sniffer - Video Processing and Transcription Tool

A comprehensive Python tool for processing video files to extract audio, frames, and generate transcriptions with precise word-level timestamps using OpenAI's Whisper API.

## ✨ Features

- **🎵 Audio Extraction**: Extract high-quality audio from MP4 videos
- **🖼️ Frame Extraction**:
  - Extract all frames with millisecond timestamps
  - Extract frames at specific positions per second (start, middle, end, random)
- **🎙️ AI Transcription**: Generate transcriptions with word-level timestamps using OpenAI Whisper
- **⏱️ Second-Aligned Words**: Map words to exact seconds for perfect frame-transcript synchronization
- **📁 Batch Processing**: Process single videos or entire directories
- **🔄 Advanced Frame-Audio Sync**: Align transcript words with extracted frames with speech coverage analysis
- **🎨 Beautiful CLI**: Rich terminal interface with progress tracking and tables
- **🧪 Comprehensive Testing**: Full test suite with pytest
- **📊 Structured Logging**: Professional logging system

## 🔧 Requirements

### System Dependencies
- **FFmpeg**: Required for video processing (see installation instructions above)

### Python Dependencies
- **Python**: 3.13+ (uses modern syntax features)
- **OpenCV**: Video and image processing
- **MoviePy**: Video file manipulation (requires FFmpeg)
- **OpenAI**: Whisper API for transcription
- **Loguru**: Modern logging library
- **python-dotenv**: Environment variable management
- **Typer + Rich**: Beautiful CLI interface

### Project Structure

```
sniffer/
├── __init__.py                 # Package exports
├── main.py                     # CLI entry point
├── video_processor.py          # Video processing orchestrator
├── transcription.py            # Audio transcription
├── types.py                    # TypedDict definitions and type aliases
├── cli/                        # CLI layer
│   ├── __init__.py            # CLI package exports
│   ├── process_handler.py     # Video processing workflow
│   └── display.py             # Rich console output management
├── services/                   # Service layer
│   ├── __init__.py            # Services package exports
│   ├── video_metadata.py      # Video metadata extraction
│   ├── frame_extraction.py    # Frame extraction operations
│   ├── video_capture.py       # Resource-managed video capture
│   ├── results_service.py     # Processing results output
│   └── sync_service.py        # Frame-transcript synchronization
├── config/                     # Configuration
│   ├── __init__.py            # Config package exports
│   └── constants.py           # Application constants
└── utils/                      # Utility functions
    ├── __init__.py            # Utils package exports
    ├── file.py                # File operations and video file discovery
    ├── directory.py           # Directory management
    └── logging.py             # Logging system
```

## 🚀 Quick Start

### System Requirements

Sniffer requires **FFmpeg** for video processing. Install it first:

**macOS (with Homebrew):**
```bash
brew install ffmpeg
```

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install ffmpeg
```

**Windows:**
- Download from [FFmpeg official website](https://ffmpeg.org/download.html)
- Or use [Chocolatey](https://chocolatey.org/): `choco install ffmpeg`

**Verify installation:**
```bash
ffmpeg -version
```

### Installation

```bash
cd sniffer

# Install with uv (recommended)
uv sync
```

### Environment Setup

Create a `.env` file in the project root for configuration:

```bash
# Copy the example file
cp .env.example .env

# Edit the .env file with your settings
# At minimum, set your OpenAI API key for transcription features
OPENAI_API_KEY=your-api-key-here
```

The `.env` file supports the following configuration options:

**Required:**
- `OPENAI_API_KEY` - Your OpenAI API key for transcription features

**Optional (Logging):**
- `LOG_LEVEL` - Logging level (DEBUG, INFO, WARNING, ERROR) [default: INFO]
- `LOG_FILE` - Path to log file [default: logs/sniffer.log]
- `LOG_ROTATION` - Log rotation setting [default: 10 MB]
- `LOG_RETENTION` - Log retention period [default: 10 days]
- `LOG_COLORIZE` - Enable colored console output [default: true]

### Basic Usage

```bash
# Setup directories and check dependencies
uv run sniffer setup

# Process a single video with transcription
uv run sniffer process video.mp4 --frames middle --transcribe

# Batch process a folder of videos
uv run sniffer process ./videos --frames random

# Get information about videos without processing
uv run sniffer info ./videos
```

## 📖 CLI Commands

### `process` - Main Processing Command

Process video files to extract audio, frames, and generate transcriptions.

```bash
uv run sniffer process INPUT_PATH [OPTIONS]
```

**Options:**
- `--audio/--no-audio`: Extract audio (default: enabled)
- `--frames [start|middle|end|random]`: Extract frames by position per second
- `--all-frames`: Extract ALL frames (⚠️ large output!)
- `--transcribe`: Transcribe audio with word-level timestamps
- `--verbose, -v`: Verbose output with detailed configuration

**Examples:**
```bash
# Process with middle frames and transcription
uv run sniffer process video.mp4 --frames middle --transcribe

# Batch process folder with audio only
uv run sniffer process ./videos

# Extract all frames without audio
uv run sniffer process video.mp4 --all-frames --no-audio
```

### `info` - Video Information

Show information about video files without processing them.

```bash
uv run sniffer info INPUT_PATH
```

### `setup` - Environment Setup

Setup required directories and check dependencies.

```bash
uv run sniffer setup
```

## 🗺️ Architecture & Call Flow

### System Overview

```mermaid
graph TB
    CLI[CLI Entry Point<br/>main.py] --> |setup| SETUP[ensure_directories]
    CLI --> |process| PROCESS[ProcessHandler]
    CLI --> |info| INFO[DisplayManager]

    PROCESS --> VP[VideoProcessor]
    PROCESS --> AT[AudioTranscriber]

    VP --> |services| MS[VideoMetadataService]
    VP --> |services| FS[FrameExtractionService]
    VP --> |extract_audio| AUDIO[Audio Extraction]

    FS --> |context manager| VC[VideoCapture]
    MS --> VC
    VC --> |OpenCV| CV[cv2.VideoCapture]

    AUDIO --> |MoviePy| MP3[MP3 Files]
    FS --> |OpenCV| PNG[PNG Files]

    AT --> |transcribe| WHISPER[OpenAI Whisper API]
    WHISPER --> JSON[JSON Transcripts]

    VP --> UTILS[Utils Layer]
    AT --> UTILS
    MS --> UTILS
    FS --> UTILS

    UTILS --> FILE[File Operations]
    UTILS --> DIR[Directory Management]
    UTILS --> LOG[Logging System]
```

### Core Component Flow

#### VideoProcessor Class

```python
VideoProcessor(video_file) → {
    __init__() → {
        ├── VideoMetadataService() → metadata operations
        ├── FrameExtractionService() → frame operations
        ├── ensure_directory() → utils.directory
        └── get_logger() → utils.logging
    }

    # Public Methods
    ├── extract_audio() → _extract_single_audio() → MoviePy
    ├── extract_all_frames() → FrameExtractionService.extract_all_frames()
    ├── extract_frames_by_position() → FrameExtractionService.extract_frames_by_position()
    ├── get_video_metadata() → VideoMetadataService.extract_metadata()
    └── process_all() → Orchestrates all operations
}
```

#### AudioTranscriber Class

```python
AudioTranscriber(audio_file, api_key) → {
    __init__() → OpenAI(api_key)

    # Core Methods
    ├── transcribe() → OpenAI.audio.transcriptions.create()
    ├── extract_word_timestamps() → list[WordTimestamp]
    ├── extract_segments() → list[SegmentData]
    ├── get_text_at_timestamp() → str | None
    └── synchronize_with_frames() → list[FrameSyncData]
}
```

#### Service Layer

```python
services/ → {
    video_metadata.py → VideoMetadataService()
    frame_extraction.py → FrameExtractionService() + FrameExtractionConfig()
    video_capture.py → VideoCapture() context manager
    results_service.py → ResultsService()
    sync_service.py → SyncService()
}
```

#### Utils Layer

```python
utils/ → {
    file.py → {
        ├── extract_filename_from_path()
        ├── get_file_extension()
        ├── is_video_file() / is_audio_file()
        ├── ensure_file_exists()
        ├── get_file_size() / format_file_size()
        └── get_video_files()
    }

    directory.py → {
        ├── ensure_directory() / ensure_directories()
        ├── is_directory_empty()
        ├── list_files_in_directory()
        └── clean_directory()
    }

    logging.py → {
        ├── setup_default_logging()
        ├── get_logger() → Loguru instance
        └── ProgressLogger
    }
}
```

## 📁 Output Structure

Sniffer organizes output files in a clean directory structure:

```
data/
├── audio/                  # Extracted audio files (.mp3)
├── video_frames/          # Extracted frames (.png)
│   └── video_name/        # Frames grouped by video
├── transcripts/           # Transcription files (.json)
└── results/               # Processing summaries (.json)
```

### Frame Naming Convention

- **All frames**: `frame_ts_00001234.png` (timestamp in milliseconds)
- **Position frames**: `frame_s2_1500ms.png` (second 2, at 1500ms)

### Transcript Format

**Original OpenAI Whisper Format:**
```json
{
  "text": "Full transcript text",
  "words": [
    {
      "word": "Hello",
      "start": 0.0,
      "end": 0.5
    }
  ],
  "segments": [
    {
      "text": "Hello world",
      "start": 0.0,
      "end": 1.0,
      "words": [...]
    }
  ]
}
```

**Enhanced Format with TypedDict Structures:**

*WordTimestamp format:*
```json
{
  "word": "Hello",
  "start": 0.0,
  "end": 0.5,
  "second": 0
}
```

*FrameSyncData format:*
```json
{
  "frame_timestamp": 0.0,
  "spoken_word": "Hello",
  "has_speech": true
}
```

## ⚙️ Configuration

### Environment Variables

- `OPENAI_API_KEY`: Your OpenAI API key for transcription features

### Video Support

Currently supports **MP4 files only**. Additional formats can be added by extending the `VideoProcessor` class.

### Frame Positions

- **start**: First frame of each second
- **middle**: Middle frame of each second
- **end**: Last frame of each second
- **random**: Random frame within each second

## 🧪 Development

### Running Tests

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=sniffer

# Run specific test file
uv run pytest tests/test_video_processor.py -v
```

### Code Quality

```bash
# Format code
uv run ruff format .

# Lint code
uv run ruff check .

# Type checking
uv run mypy sniffer/

# Full CI pipeline
make ci
```

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

---

Made with ❤️ for video processing and AI transcription