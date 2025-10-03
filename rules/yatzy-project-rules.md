# Yatzy Project Development Rules

## Project Overview
This is a Yatzy (Yahtzee) game implementation in Python. The project contains scoring logic for various Yatzy categories and follows clean code principles.

## Code Quality Standards

### General Principles
- Follow Python PEP 8 style guidelines
- Write clean, readable, and maintainable code
- Prefer static methods for pure functions (no side effects)
- Use descriptive variable and function names
- Add docstrings to all public methods
- Keep methods small and focused on single responsibility

### Yatzy-Specific Rules
- All scoring methods should accept a list of dice values as input for consistency
- Use constants for magic numbers (e.g., YATZY_SCORE = 50)
- Implement helper methods to reduce code duplication
- Ensure all scoring logic follows the official Yatzy rules as documented in README.md

## Refactoring Guidelines

### When Refactoring Code:
1. **Maintain API Compatibility**: Ensure existing tests continue to pass
2. **Reduce Duplication**: Extract common patterns into helper methods
3. **Improve Readability**: Use clear variable names and add comments where needed
4. **Follow Single Responsibility**: Each method should do one thing well
5. **Use Constants**: Replace magic numbers with named constants

### Preferred Patterns:
- Use `@staticmethod` for pure scoring functions
- Create helper methods like `_get_dice_counts()` for common operations
- Use list comprehensions and built-in functions when appropriate
- Prefer `sum()` over manual accumulation loops

## Testing Requirements

### Test Standards:
- All scoring methods must have comprehensive test coverage
- Tests should cover edge cases and invalid inputs
- Use descriptive test method names
- Test both valid and invalid scoring scenarios
- Ensure tests are independent and repeatable

### Test Data:
- Use realistic dice combinations
- Test boundary conditions (all same, all different, etc.)
- Include edge cases like empty lists or invalid dice values

## Code Structure

### Class Organization:
```python
class Yatzy:
    # Constants first
    YATZY_SCORE = 50
    SMALL_STRAIGHT_SCORE = 15
    LARGE_STRAIGHT_SCORE = 20
    
    # Helper methods (private)
    @staticmethod
    def _get_dice_counts(dice):
        """Helper method to count frequency of each dice value."""
        
    # Public scoring methods
    @staticmethod
    def chance(dice):
        """Sum of all dice values."""
```

### Method Naming:
- Use descriptive names: `score_pair()`, `two_pair()`, `full_house()`
- Follow Python naming conventions (snake_case)
- Make method names self-documenting

## Error Handling

### Input Validation:
- Validate that dice lists contain exactly 5 elements
- Ensure dice values are integers between 1 and 6
- Handle edge cases gracefully (return 0 for invalid combinations)

### Defensive Programming:
- Don't assume input is valid
- Use type hints where appropriate
- Add input validation for public methods

## Documentation Standards

### Docstrings:
- Use clear, concise descriptions
- Include examples for complex scoring rules
- Document return values and edge cases
- Follow Google or NumPy docstring format

### Comments:
- Explain complex algorithms
- Document business logic that might not be obvious
- Use comments sparingly - prefer self-documenting code

## Yatzy Game Rules Compliance

### Scoring Categories:
- **Chance**: Sum of all dice
- **Yatzy**: 50 points if all dice are the same
- **Ones-Sixes**: Sum of dice showing that number
- **Pair**: Sum of highest pair (exactly 2 of same number)
- **Two Pair**: Sum of two pairs (exactly 2 of each number)
- **Three of a Kind**: Sum of three dice of same number
- **Four of a Kind**: Sum of four dice of same number
- **Small Straight**: 15 points for 1,2,3,4,5
- **Large Straight**: 20 points for 2,3,4,5,6
- **Full House**: Sum of three of a kind plus pair

### Important Rules:
- Pairs must be exactly 2 dice, not 3 or more
- Two pairs must be exactly 2 dice each, not 3+2
- Straights must contain exactly the specified numbers
- Full house must be exactly 3+2, not 4+1 or 5+0

## Agent Behavior

### When Asked to Refactor:
1. Analyze current code for duplication and complexity
2. Propose improvements that maintain functionality
3. Update both implementation and tests
4. Ensure all existing tests continue to pass
5. Document the changes made

### When Asked to Add Features:
1. Follow existing code patterns and style
2. Add comprehensive tests for new functionality
3. Update documentation as needed
4. Consider impact on existing code

### When Asked to Debug:
1. Run tests to reproduce the issue
2. Analyze the failing code
3. Propose fixes that address the root cause
4. Verify fixes with tests
5. Consider if the issue indicates a broader problem

Remember: The goal is to maintain a clean, maintainable, and well-tested codebase that accurately implements the Yatzy game rules.
description:
globs:
alwaysApply: false
---
