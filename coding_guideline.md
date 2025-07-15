# Coding Guidelines for LightRAG

## Python Style Guide
This project follows the [Google Python Style Guide](https://google.github.io/styleguide/pyguide.html) with modern Python conventions.

## Key Points from Google Style Guide

### General
- Use 4 spaces for indentation (never tabs)
- Maximum line length: 80 characters
- Use UTF-8 encoding

### Naming Conventions
- `module_name`, `package_name`
- `ClassName`
- `method_name`, `function_name`
- `GLOBAL_CONSTANT_NAME`
- `_private_function`, `_private_variable`

### Imports
- Use absolute imports
- Group imports: standard library, third-party, local
- One import per line

### Documentation
- Use docstrings for all public modules, functions, classes, and methods
- Follow Google docstring format:
```python
def function_name(param1: str, param2: int) -> bool:
    """Brief description of function.

    Args:
        param1: Description of param1.
        param2: Description of param2.

    Returns:
        Description of return value.

    Raises:
        ValueError: Description of when this error is raised.
    """
```

### Type Annotations (Modern Python Style)
- Use built-in types: `list`, `dict`, `set`, `tuple`
- Use `|` for unions instead of `Optional` or `Union`
- Example:
```python
def process_data(items: list[str], config: dict[str, int] | None = None) -> dict[str, int]:
    ...

async def get_user(user_id: int) -> User | None:
    ...
```

## Project-Specific Guidelines

### Async/Await
- Use async/await for all database operations
- Prefix async functions with appropriate verbs (get_, fetch_, create_, update_, delete_)

### Error Handling
- Use specific exception types
- Always include meaningful error messages
- Log errors appropriately

### PydanticAI Agents
- Document all prompts clearly
- Keep agents focused on single responsibilities
- Use dependency injection for agent dependencies

### API Endpoints
- Follow RESTful conventions
- Use proper HTTP status codes
- Validate all inputs with Pydantic models

### Database
- Use asyncpg for PostgreSQL connections
- Always use parameterized queries
- Include proper indexes for performance
- Use connection pooling for efficiency

### Testing
- Minimum 80% code coverage
- Use pytest fixtures for setup
- Mock external dependencies
- Test both success and failure cases