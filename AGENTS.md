# AGENTS.md - Coding Guidelines for nr-wg-mtu-finder

## Build/Lint/Test Commands
- **Install dependencies**: `poetry install`
- **Format code**: `black .`
- **Sort imports**: `isort .`
- **Lint and format**: `black . && isort .`
- **No test framework configured** - run scripts manually for testing

## Code Style Guidelines

### Formatting
- **Line length**: 88 characters (Black default)
- **Formatter**: Black
- **Import sorter**: isort with black profile

### Imports
- Standard library imports first
- Third-party imports second
- Local imports last
- One import per line
- Use absolute imports for local modules

### Types
- Use type hints extensively
- Use Pydantic models for configuration/validation
- Use `StrictStr`, `StrictInt` for strict typing
- Use `Literal` for enumerated string values

### Naming Conventions
- **Variables/Functions**: snake_case
- **Classes**: PascalCase
- **Constants**: UPPER_CASE
- **Modules**: snake_case

### Error Handling
- Create custom exception classes when needed
- Use try/except blocks for subprocess calls
- Log errors appropriately
- Skip known errors in peer mode when configured

### Code Structure
- Use classes for main functionality
- Include docstrings for public methods
- Use descriptive variable names
- Separate concerns (MTU finding, plotting, server sync)

### Security
- Avoid running in production environments
- Use subprocess carefully with shell commands
- Validate all inputs through Pydantic models