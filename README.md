# 🎬 Sniffer - Video Processing and Transcription Tool

A comprehensive Python tool for processing video files to extract audio, frames, and generate transcriptions with precise word-level timestamps using OpenAI's Whisper API.

## ✨ Features

- **🎵 Audio Extraction**: Extract high-quality audio from MP4 videos
- **🖼️ Frame Extraction**:
  - Extract all frames with millisecond timestamps
  - Extract frames at specific positions per second (start, middle, end, random)
- **🎙️ AI Transcription**: Generate transcriptions with word-level timestamps using OpenAI Whisper
- **📁 Batch Processing**: Process single videos or entire directories
- **🔄 Frame-Audio Synchronization**: Align transcript words with extracted frames
- **🎨 Beautiful CLI**: Rich terminal interface with progress tracking and tables
- **🧪 Comprehensive Testing**: Full test suite with pytest
- **📊 Structured Logging**: Professional logging system

## 🚀 Quick Start

### System Requirements

SunDogs requires **FFmpeg** for video processing. Install it first:

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
sniffer setup

# Process a single video with transcription
sniffer process video.mp4 --frames middle --transcribe

# Batch process a folder of videos
sniffer process ./videos --frames random

# Get information about videos without processing
sniffer info ./videos
```

## 📖 CLI Commands

### `process` - Main Processing Command

Process video files to extract audio, frames, and generate transcriptions.

```bash
sniffer process INPUT_PATH [OPTIONS]
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
sniffer process video.mp4 --frames middle --transcribe

# Batch process folder with audio only
sniffer process ./videos --no-frames

# Extract all frames without audio
sniffer process video.mp4 --all-frames --no-audio
```

### `info` - Video Information

Show information about video files without processing them.

```bash
sniffer info INPUT_PATH
```

### `setup` - Environment Setup

Setup required directories and check dependencies.

```bash
sniffer setup
```

## 🐍 Python API

Use SunDogs programmatically in your Python applications:

```python
from sniffer import VideoProcessor, AudioTranscriber

# Initialize processor
processor = VideoProcessor("path/to/video.mp4")

# Extract audio
audio_path = processor.extract_audio()

# Extract frames at middle position per second
frames = processor.extract_frames_by_position("middle")

# Transcribe audio with timestamps
transcriber = AudioTranscriber()
transcript = transcriber.transcribe_with_timestamps(audio_path)

# Synchronize frames with speech
frame_times = [1.0, 2.0, 3.0]  # seconds
sync_data = transcriber.synchronize_with_frames(transcript, frame_times)
```

### Batch Processing

```python
from pathlib import Path

# Process entire directory
processor = VideoProcessor("./videos")
results = processor.process_all(
    extract_audio=True,
    frame_position="middle"
)

# Batch transcription
audio_paths = results["audio_paths"]
transcriber = AudioTranscriber()
transcripts = transcriber.transcribe_batch(audio_paths)
```

## 🗺️ Architecture & Call Flow

### System Overview

```mermaid
graph TB
    CLI[CLI Entry Point<br/>main.py] --> |setup| SETUP[setup_directories]
    CLI --> |process| PROCESS[process command]
    CLI --> |info| INFO[info command]

    PROCESS --> VP[VideoProcessor]
    PROCESS --> AT[AudioTranscriber]

    VP --> |extract_audio| AUDIO[Audio Extraction]
    VP --> |extract_frames| FRAMES[Frame Extraction]
    VP --> |process_all| BATCH[Batch Processing]

    AUDIO --> |MoviePy| MP3[MP3 Files]
    FRAMES --> |OpenCV| PNG[PNG Files]

    AT --> |transcribe_batch| WHISPER[OpenAI Whisper API]
    WHISPER --> JSON[JSON Transcripts]

    VP --> UTILS[Utils Layer]
    AT --> UTILS

    UTILS --> FILE[File Operations]
    UTILS --> DIR[Directory Management]
    UTILS --> LOG[Logging System]
```

### Core Component Flow

#### 1. CLI Entry Points (`main.py`)

```python
# Command flow
app.command("process") → process() → {
    VideoProcessor(input_path)
    ├── extract_audio() → list[str]
    ├── extract_frames_by_position() → dict[str, dict[int, str]]
    └── extract_all_frames() → dict[str, list[str]]

    AudioTranscriber() → {
        ├── transcribe_batch() → dict[str, dict]
        └── synchronize_with_frames() → list[dict]
    }
}
```

#### 2. VideoProcessor Class (`video_processor.py`)

```python
VideoProcessor(video_input) → {
    __init__() → {
        ├── _get_video_files() → list[Path]
        ├── ensure_directory() → utils.directory
        └── get_logger() → utils.logging
    }

    # Public Methods
    ├── extract_audio() → _extract_single_audio() → MoviePy
    ├── extract_all_frames() → _extract_all_frames_single() → OpenCV
    ├── extract_frames_by_position() → {
    │   ├── _extract_frames_by_position_single()
    │   ├── _calculate_timestamps_per_second()
    │   └── _fetch_frames_by_timestamp() → OpenCV
    │   }
    └── process_all() → Orchestrates all operations
}
```

#### 3. AudioTranscriber Class (`transcription.py`)

```python
AudioTranscriber(api_key) → {
    __init__() → OpenAI(api_key)

    # Core Methods
    ├── transcribe_with_timestamps() → OpenAI.audio.transcriptions.create()
    ├── transcribe_batch() → {
    │   ├── transcribe_with_timestamps() (per file)
    │   └── save_transcripts → JSON files
    │   }

    # Analysis Methods
    ├── extract_word_timestamps() → list[dict]
    ├── extract_segments() → list[dict]
    ├── get_text_at_timestamp() → str | None
    └── synchronize_with_frames() → list[dict]
}
```

#### 4. Utils Layer

```python
utils/ → {
    file.py → {
        ├── extract_filename_from_path()
        ├── is_video_file() / is_audio_file()
        ├── get_file_size() / format_file_size()
        └── ensure_file_exists()
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
        └── ProgressLogger → {
            ├── start_operation()
            ├── progress_update()
            ├── complete_operation()
            └── operation_error()
        }
    }
}
```

### Data Flow Examples

#### Complete Processing Pipeline

```python
# CLI Command: uv run sniffer process video.mp4 --frames middle --transcribe

main.process() → {
    1. VideoProcessor("video.mp4") → {
        ├── _get_video_files() → [Path("video.mp4")]
        └── setup directories
    }

    2. processor.process_all() → {
        ├── extract_audio() → ["data/audio/video.mp3"]
        └── extract_frames_by_position("middle") → {
            "video.mp4": {0: "frame_s0_500ms.png", 1: "frame_s1_1500ms.png"}
        }
    }

    3. AudioTranscriber() → {
        ├── transcribe_batch(["data/audio/video.mp3"]) → {
        │   "video.mp3": {
        │       "text": "transcript...",
        │       "words": [{"word": "hello", "start": 0.0, "end": 0.5}]
        │   }
        │   }
        └── save transcripts → "data/transcripts/video_transcript.json"
    }

    4. show_results_summary() → Rich table display
}
```

#### Batch Processing Flow

```python
# CLI Command: uv run sniffer process ./videos --frames random

VideoProcessor("./videos") → {
    _get_video_files() → [
        Path("videos/video1.mp4"),
        Path("videos/video2.mp4"),
        Path("videos/video3.mp4")
    ]

    process_all() → {
        # Parallel processing for each video
        for video_file in video_files:
            ├── _extract_single_audio(video_file)
            └── _extract_frames_by_position_single(video_file, "random")
    }
}
```

### External Dependencies Integration

```python
# System Integration Points
{
    "FFmpeg": "Required by MoviePy for video processing",
    "OpenCV": "Direct integration for frame extraction",
    "OpenAI API": "Whisper model for transcription",
    "File System": "utils.directory & utils.file for I/O operations"
}
```

## 📁 Output Structure

SunDogs organizes output files in a clean directory structure:

```
data/
├── audio/                  # Extracted audio files (.mp3)
├── video_frames/          # Extracted frames (.png)
│   └── video_name/        # Frames grouped by video
├── transcripts/           # Transcription files (.json)
└── video/                 # Original video files
```

### Frame Naming Convention

- **All frames**: `frame_ts_00001234.png` (timestamp in milliseconds)
- **Position frames**: `frame_s2_1500ms.png` (second 2, at 1500ms)

### Transcript Format

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

### Project Structure

```
sniffer/
├── __init__.py                 # Package exports
├── main.py                     # CLI entry point
├── video_processor.py          # Video processing core
├── transcription.py            # Audio transcription
├── config/                     # Configuration
│   ├── __init__.py            # Config package exports
│   └── constants.py           # Application constants
└── utils/                      # Utility functions
    ├── __init__.py            # Utils package exports
    ├── file.py                # File operations
    ├── directory.py           # Directory management
    └── logging.py             # Logging system
```

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

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 🐛 Troubleshooting

### Common Issues

**"No module named 'ffmpeg'" or video processing errors**
- Install FFmpeg system-wide (see System Requirements section)
- Verify FFmpeg is in your PATH: `ffmpeg -version`
- Restart your terminal after installation

**"No MP4 files found"**
- Ensure your video files have the `.mp4` extension
- Check that the directory path is correct

**"OpenAI API key is required"**
- Create a `.env` file and set `OPENAI_API_KEY=your-key-here`
- Or set the environment variable: `export OPENAI_API_KEY='your-key'`
- Verify your API key is valid and has credits

**"Could not open video file"**
- Verify the video file is not corrupted
- Ensure FFmpeg is properly installed
- Check that OpenCV can read the video format

### Getting Help

- Check the [Issues](https://github.com/erictt/sniffer/issues) page
- Create a new issue with detailed information about your problem
- Include log files when reporting bugs (use `--verbose` flag)

---

Made with ❤️ for video processing and AI transcription
