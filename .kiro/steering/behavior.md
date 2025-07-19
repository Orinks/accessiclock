# Development Behavior Guidelines

## Virtual Environment Management
Always activate the virtual environment before running any commands:

**Windows (bash/Git Bash):**
```bash
source .venv/Scripts/activate
```

**Windows (cmd):**
```cmd
.venv\Scripts\activate
```

**Windows (PowerShell):**
```powershell
.venv\Scripts\Activate.ps1
```

**Unix/Linux/macOS:**
```bash
source .venv/bin/activate
```

## Command Execution Pattern
1. **Always activate .venv first** before running any Python-related commands
2. **Run commands from project root** after activation
3. **Deactivate when switching contexts** (optional but good practice)

## Testing Guidelines

### Test Execution Methods
```bash
# Activate environment first (Windows bash)
source .venv/Scripts/activate

# Method 1: Full test suite via Briefcase (preferred for integration testing)
briefcase dev --test

# Method 2: Direct pytest execution (for unit testing)
pytest tests/ -vv

# Method 3: Custom test runner
python tests/accessiclock.py
```

### Toga Testing Backend
When running tests, use the Toga dummy backend to avoid GUI dependencies:
```bash
# Set environment variable for headless testing (Windows bash)
export TOGA_BACKEND=dummy

# Then run tests
briefcase dev --test
```

### Windows-Specific Testing Commands
```bash
# For Windows with bash/Git Bash environment
source .venv/Scripts/activate && export TOGA_BACKEND=dummy && pytest tests/ -vv

# For running specific test files
source .venv/Scripts/activate && export TOGA_BACKEND=dummy && pytest tests/test_audio_manager.py -v
```

## Test-Driven Development (TDD) Approach

### TDD Workflow
1. **Write failing tests first** - Define expected behavior through tests
2. **Write minimal code** to make tests pass
3. **Refactor** while keeping tests green
4. **Repeat** for each new feature or bug fix

### Planning Tasks with TDD
When implementing new features:

1. **Start with test cases** - What should the feature do?
2. **Write test scenarios** - Cover happy path, edge cases, error conditions
3. **Implement incrementally** - Small, testable chunks
4. **Verify accessibility** - Ensure features work with assistive technologies

### Example TDD Workflow for AccessiClock
```bash
# 1. Activate environment (Windows bash)
source .venv/Scripts/activate

# 2. Write test for new clock feature
# Edit tests/test_clock_display.py

# 3. Run tests to see failure
export TOGA_BACKEND=dummy
briefcase dev --test

# 4. Implement minimal feature
# Edit src/accessiclock/app.py

# 5. Run tests again to verify
briefcase dev --test

# 6. Refactor if needed while keeping tests green
```

## Development Commands Checklist
Before running any of these commands, ensure `.venv` is activated:

- ✅ `briefcase dev` - Run app in development mode
- ✅ `briefcase dev --test` - Run full test suite
- ✅ `briefcase create` - Create app package
- ✅ `briefcase build` - Build the application
- ✅ `pytest tests/` - Run unit tests
- ✅ `python tests/accessiclock.py` - Custom test runner