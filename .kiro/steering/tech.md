# Technology Stack

## Framework & Build System
- **Primary Framework**: BeeWare Toga (~0.5.0) - Python-native GUI framework
- **Build Tool**: Briefcase - Cross-platform app packaging and deployment
- **Python Version**: 3.12+ (based on mypy cache)
- **Project Management**: pyproject.toml configuration

## Platform-Specific Dependencies
- **Windows**: toga-winforms
- **macOS**: toga-cocoa, std-nslog
- **Linux**: toga-gtk, PyGObject, GTK3 system dependencies
- **iOS**: toga-iOS, std-nslog
- **Android**: toga-android, Material Components
- **Web**: toga-web, Shoelace v2.3 style framework

## Testing
- **Test Framework**: pytest
- **Test Runner**: Custom test runner in `tests/accessiclock.py`
- **Test Structure**: Tests located in `tests/` directory

## Common Commands

### Development
```bash
# Run the application in development mode
briefcase dev

# Run tests
python tests/accessiclock.py
# or directly with pytest
pytest tests/ -vv
```

### Building & Packaging
```bash
# Create application package
briefcase create

# Build the application
briefcase build

# Package for distribution
briefcase package

# Update application after code changes
briefcase update
```

### Platform-Specific Builds
```bash
# Build for specific platforms
briefcase build windows
briefcase build macOS
briefcase build linux
briefcase build android
briefcase build iOS
briefcase build web
```