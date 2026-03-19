# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

- **Language**: Python 3.10 (configured in `.idea/misc.xml`)
- **Project type**: AI agents learning project (likely focused on building and testing AI agents)
- **Structure**: Currently minimal, with a `chapter1/` directory suggesting tutorial/learning progression
- **IDE**: PyCharm/IntelliJ project (`.idea/` configuration present)
- **Version control**: Git repository with remote origin

## Setup and Environment

### Virtual Environment
This project uses Python's built-in `venv` for dependency isolation. Create and activate a virtual environment:

```bash
python -m venv venv

# On Windows:
venv\Scripts\activate

# On macOS/Linux:
source venv/bin/activate
```

### Dependencies
No `requirements.txt` or `pyproject.toml` exists yet. When dependencies are added, install them with:

```bash
pip install -r requirements.txt
```

For development dependencies (testing, linting, formatting), consider creating a `requirements-dev.txt`.

## Common Development Tasks

### Running Python Code
Execute Python scripts from the project root:

```bash
python chapter1/FirstAgentTest.py
```

### Testing
When tests are added (likely in `tests/` directory), run them with:

```bash
# Using pytest (recommended)
pytest

# Run specific test file
pytest tests/test_agent.py

# Run with verbose output
pytest -v
```

### Code Quality
For consistent code style, consider adding:

- **Black** for code formatting: `black .`
- **isort** for import sorting: `isort .`
- **Flake8** or **pylint** for linting
- **mypy** for type checking (if type hints are used)

### Flask Development
The `.idea/workspace.xml` suggests Flask may be used. If Flask applications are present:

```bash
# Set Flask environment variables
export FLASK_APP=app.py  # or the appropriate entry point
export FLASK_ENV=development

# Run Flask development server
flask run
```

## Project Structure

The repository currently has minimal structure:

```
hello-agents/
├── chapter1/
│   └── FirstAgentTest.py    # Placeholder for first agent tests
├── .idea/                   # PyCharm project configuration
└── CLAUDE.md               # This file
```

As the project evolves, expect:
- Additional `chapterN/` directories for progressive learning
- `agents/` or `src/` directory for agent implementations
- `tests/` directory for unit and integration tests
- `requirements.txt` for dependencies
- Configuration files for linting, formatting, and testing

## Development Notes

- **Git workflow**: The repository uses `master` as the main branch. Create feature branches for new work.
- **Commit messages**: Follow conventional commit style or keep descriptive messages in English/Chinese (as seen in initial commit).
- **IDE integration**: The project is configured for PyCharm with Python 3.10 SDK. Consider syncing virtual environment with IDE.

## Future Considerations

When implementing AI agents:
- Consider using popular agent frameworks (LangChain, AutoGen, CrewAI) if appropriate
- Keep agent logic modular and testable
- Document agent capabilities and interfaces
- Add examples and usage documentation

This CLAUDE.md should be updated as the project matures and more structure emerges.