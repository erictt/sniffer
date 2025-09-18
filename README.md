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
python main.py setup

# Process a single video with transcription
python main.py process video.mp4 --frames middle --transcribe

# Batch process a folder of videos
python main.py process ./videos --frames random

# Get information about videos without processing
python main.py info ./videos
```

## 📖 CLI Commands

### `process` - Main Processing Command

Process video files to extract audio, frames, and generate transcriptions.

```bash
python main.py process INPUT_PATH [OPTIONS]
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
python main.py process video.mp4 --frames middle --transcribe

# Batch process folder with audio only
python main.py process ./videos --no-frames

# Extract all frames without audio
python main.py process video.mp4 --all-frames --no-audio
```

### `info` - Video Information

Show information about video files without processing them.

```bash
python main.py info INPUT_PATH
```

### `setup` - Environment Setup

Setup required directories and check dependencies.

```bash
python main.py setup
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
python -m pytest

# Run with coverage
python -m pytest --cov=sniffer

# Run specific test file
python -m pytest tests/test_video_processor.py -v
```

### Code Quality

```bash
# Format code
ruff format .

# Lint code
ruff check .

# Type checking
mypy sniffer/
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
