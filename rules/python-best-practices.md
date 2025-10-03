# Python Best Practices

## Code Style and Formatting

### PEP 8 Compliance
- Use 4 spaces for indentation (no tabs)
- Maximum line length of 88 characters (Black default)
- Use snake_case for variables and functions
- Use PascalCase for classes
- Use UPPER_CASE for constants

### Import Organization
```python
# Standard library imports
import os
import sys
from typing import List, Optional

# Third-party imports
import pytest

# Local application imports
from src.yatzy import Yatzy
```

## Type Hints and Documentation

### Type Annotations
- Use type hints for all function parameters and return values
- Use `Optional[Type]` for parameters that can be None
- Use `List[Type]` for list parameters

### Docstrings
- Use Google or NumPy docstring format
- Include parameter types and descriptions
- Document return values and exceptions
- Provide examples for complex functions

## Error Handling

### Exception Handling
- Use specific exception types when possible
- Don't catch bare exceptions unless necessary
- Provide meaningful error messages
- Use context managers for resource management

### Input Validation
- Validate inputs at function boundaries
- Use type checking and value validation
- Return appropriate default values for invalid inputs
- Document expected input formats

## Performance and Optimization

### Efficient Patterns
- Use list comprehensions over explicit loops when appropriate
- Prefer built-in functions (sum, max, min) over manual loops
- Use sets for membership testing
- Avoid unnecessary object creation

### Memory Management
- Use generators for large datasets
- Avoid creating unnecessary intermediate lists
- Use `__slots__` for classes with many instances

## Testing Best Practices

### Test Structure
- Use descriptive test method names
- Follow AAA pattern (Arrange, Act, Assert)
- Test both positive and negative cases
- Use fixtures for common test data

### Test Coverage
- Aim for high test coverage (90%+)
- Test edge cases and boundary conditions
- Test error conditions and exceptions
- Use parameterized tests for multiple scenarios

## Code Organization

### Function Design
- Keep functions small and focused
- Use meaningful parameter names
- Limit the number of parameters (max 5)
- Use default arguments for optional parameters

### Class Design
- Follow single responsibility principle
- Use composition over inheritance
- Keep methods small and focused
- Use properties for computed attributes

## Security Considerations

### Input Sanitization
- Validate and sanitize all user inputs
- Use parameterized queries for database operations
- Avoid eval() and exec() with user input
- Use secure random number generators

## Maintainability

### Code Comments
- Write self-documenting code
- Use comments to explain "why" not "what"
- Keep comments up to date with code changes
- Use TODO comments for future improvements

### Refactoring Guidelines
- Extract common patterns into helper functions
- Remove code duplication
- Improve readability without changing functionality
- Maintain backward compatibility when possible
description:
globs:
alwaysApply: false
---
