# AccessiClock

A fully accessible cross-platform desktop clock application with sound pack support, built with Python and BeeWare Toga.

## 🎯 Project Vision

AccessiClock is designed with accessibility as a core feature, providing an inclusive clock experience for users with different needs. The application combines traditional timekeeping with customizable audio feedback and sound packs to create a rich, accessible user experience.

## ✨ Features

- **Cross-Platform**: Runs on Windows, macOS, Linux, iOS, Android, and Web
- **Accessibility-First Design**: Built with screen readers and assistive technologies in mind
- **Sound Pack Support**: Customizable audio themes and chime sounds
- **Text-to-Speech Integration**: Both cloud-based (ElevenLabs) and local (pyttsx3) TTS support
- **Robust Error Handling**: Graceful fallbacks and comprehensive logging
- **Modern Architecture**: Clean, modular codebase with comprehensive testing

## 🚀 Quick Start

### Prerequisites

- Python 3.12+
- Git

### Installation

1. Clone the repository:
```bash
git clone https://github.com/Orinks/accessiclock.git
cd accessiclock
```

2. Create and activate a virtual environment:
```bash
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS/Linux
source .venv/bin/activate
```

3. Install dependencies and run in development mode:
```bash
briefcase dev
```

### Running Tests

```bash
# Set the test backend (for headless testing)
set TOGA_BACKEND=dummy  # Windows
export TOGA_BACKEND=dummy  # macOS/Linux

# Run the full test suite
briefcase dev --test

# Or run specific tests
pytest tests/ -v
```

## 🏗️ Architecture

The project follows a clean, modular architecture:

```
src/accessiclock/
├── managers/          # Business logic managers
├── models/           # Data models and configurations
├── ui/              # User interface components
├── utils/           # Utility functions and helpers
│   ├── logging_config.py    # Centralized logging
│   └── error_handler.py     # Error handling framework
└── app.py           # Main application class
```

## 🛠️ Development

### Project Structure

- **Framework**: BeeWare Toga (~0.5.0) for cross-platform GUI
- **Build System**: Briefcase for packaging and deployment
- **Testing**: pytest with comprehensive test coverage
- **Code Quality**: mypy for type checking, comprehensive error handling

### Key Dependencies

- `elevenlabs` - AI-powered text-to-speech
- `pyttsx3` - Local text-to-speech fallback
- `pygame` - Audio playback and mixing
- `requests` & `aiohttp` - HTTP client functionality

### Development Commands

```bash
# Run in development mode
briefcase dev

# Create application package
briefcase create

# Build for distribution
briefcase build

# Package for specific platforms
briefcase build windows
briefcase build macOS
briefcase build linux
```

## 🧪 Testing

The project includes comprehensive testing with:

- Unit tests for core functionality
- Integration tests for cross-platform compatibility
- Error handling and logging verification
- Accessibility compliance testing

Current test coverage: **9/9 tests passing** ✅

## 📋 Development Status

This project is currently in active development. The foundation has been established with:

- ✅ Core project structure and dependencies
- ✅ Logging configuration and error handling framework
- ✅ Cross-platform compatibility setup
- ✅ Comprehensive test suite
- 🚧 Clock display and timing functionality (in progress)
- 🚧 Sound pack management system (planned)
- 🚧 Accessibility features implementation (planned)
- 🚧 Text-to-speech integration (planned)

## 🤝 Contributing

Contributions are welcome! Please feel free to submit issues, feature requests, or pull requests.

### Development Setup

1. Fork the repository
2. Create a feature branch
3. Make your changes with tests
4. Ensure all tests pass
5. Submit a pull request

## 📄 License

This project is licensed under the BSD 3-Clause License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Built with [BeeWare Toga](https://toga.readthedocs.io/) for cross-platform GUI development
- Uses [ElevenLabs](https://elevenlabs.io/) for high-quality text-to-speech
- Inspired by the need for truly accessible desktop applications

---

**AccessiClock** - Making time accessible for everyone 🕐♿