# Project Structure

## Directory Layout
```
accessiclock/
├── .kiro/                    # Kiro IDE configuration and steering rules
├── src/                      # Source code
│   └── accessiclock/         # Main application package
│       ├── __init__.py       # Package initialization (empty)
│       ├── __main__.py       # Entry point for python -m execution
│       ├── app.py            # Main application class
│       └── resources/        # Static resources (icons, sounds, etc.)
├── tests/                    # Test suite
│   ├── __init__.py          # Test package initialization
│   ├── accessiclock.py      # Custom test runner
│   └── test_app.py          # Application tests
├── pyproject.toml           # Project configuration and dependencies
├── README.rst               # Project documentation
├── CHANGELOG                # Release notes
├── LICENSE                  # BSD 3-Clause license
└── .gitignore              # Git ignore patterns
```

## Code Organization

### Main Application (`src/accessiclock/`)
- **`app.py`**: Contains the main `AccessiClock` class inheriting from `toga.App`
- **`__main__.py`**: Entry point that imports and runs the main app
- **`resources/`**: Static assets like icons, sounds, and other media files

### Application Architecture
- **Single App Class**: `AccessiClock` extends `toga.App`
- **Startup Method**: Main UI construction happens in `startup()` method
- **Main Window**: Created as `toga.MainWindow` with app's formal name as title
- **Layout**: Uses Toga's Box layout system with Pack styling

### Testing Structure
- **Test Directory**: All tests in `tests/` directory
- **Custom Runner**: `tests/accessiclock.py` provides custom pytest execution
- **Test Naming**: Test files follow `test_*.py` pattern
- **Test Functions**: Test functions follow `test_*()` naming convention

## Naming Conventions
- **Package**: `accessiclock` (lowercase, no underscores)
- **Class**: `AccessiClock` (PascalCase)
- **Files**: snake_case for Python files
- **Tests**: `test_` prefix for test files and functions

## Configuration Files
- **`pyproject.toml`**: Central configuration for Briefcase, dependencies, and build settings
- **Platform-specific sections**: Separate configuration blocks for each target platform
- **Version**: Managed in pyproject.toml under `tool.briefcase.version`