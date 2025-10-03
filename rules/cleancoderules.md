---
description: Clean Code Rules and Coding Style Guidelines
globs: ["src/**/*.py", "tests/**/*.py"]
alwaysApply: true
---

# Clean Code Rules and Coding Style Guidelines

## Object Calisthenics (9 Rules for Better Design)

### 1. One Level of Indentation Per Method
- Keep methods simple and readable
- Avoid deeply nested code structures
- Extract complex logic into separate methods
- Maximum indentation level: 2-3 levels

### 2. Don't Use the ELSE Keyword
- Use early returns to reduce complexity
- Prefer guard clauses over if-else chains
- Use polymorphism instead of conditional logic
- Makes code more readable and maintainable

### 3. Wrap All Primitives and Strings
- Create value objects for domain concepts
- Encapsulate primitive values with meaningful types
- Add validation and behavior to value objects
- Improves type safety and expressiveness

### 4. First Class Collections
- Wrap collections in dedicated classes
- Add domain-specific methods to collection classes
- Encapsulate collection behavior and invariants
- Makes collection usage more explicit

### 5. One Dot Per Line
- Avoid method chaining across object boundaries
- Follow the Law of Demeter
- Reduce coupling between objects
- Makes dependencies more explicit

### 6. Don't Abbreviate
- Use full, descriptive names for variables and methods
- Prefer clarity over brevity
- Make code self-documenting
- Avoid cryptic abbreviations

### 7. Keep All Entities Small
- Classes should have a single responsibility
- Methods should be short and focused
- Files should be manageable in size
- Modules should have clear boundaries

### 8. No Classes with More Than Two Instance Variables
- Prefer composition over large objects
- Split complex classes into smaller ones
- Use value objects for related data
- Improves cohesion and reduces complexity

### 9. No Getters/Setters/Properties (Tell, Don't Ask)
- Objects should encapsulate behavior, not just data
- Tell objects what to do, don't ask for their state
- Prefer methods that perform actions
- Reduces coupling and improves encapsulation

## Python-Specific Style Guidelines

### PEP 8 Compliance
- Use 4 spaces for indentation (never tabs)
- Maximum line length: 88 characters (Black default)
- Use snake_case for variables and functions
- Use PascalCase for classes
- Use UPPER_CASE for constants

### Naming Conventions
```python
# Good examples
class YatzyScorer:
    MAXIMUM_DICE_VALUE = 6
    
    def calculate_score(self, dice_values):
        return sum(dice_values)
    
    def _validate_dice(self, dice_values):
        # Private method with underscore prefix
        pass
```

### Function Design
- Keep functions small (max 20-30 lines)
- Use descriptive parameter names
- Limit number of parameters (max 5)
- Use type hints for clarity
- Return early when possible

### Error Handling
- Use specific exception types
- Provide meaningful error messages
- Fail fast with clear feedback
- Use context managers for resource management

### Documentation
- Write docstrings for public methods
- Use clear, concise descriptions
- Include examples for complex functions
- Document edge cases and assumptions

## Code Organization Principles

### SOLID Principles

#### Single Responsibility Principle (SRP)
- Each class should have only one reason to change
- Separate concerns into different classes
- Keep methods focused on a single task

#### Open/Closed Principle (OCP)
- Open for extension, closed for modification
- Use inheritance and composition
- Prefer configuration over code changes

#### Liskov Substitution Principle (LSP)
- Subtypes must be substitutable for base types
- Honor the contract of the base class
- Don't strengthen preconditions or weaken postconditions

#### Interface Segregation Principle (ISP)
- Many specific interfaces are better than one general-purpose interface
- Don't force clients to depend on methods they don't use
- Keep interfaces focused and cohesive

#### Dependency Inversion Principle (DIP)
- Depend on abstractions, not concretions
- High-level modules should not depend on low-level modules
- Use dependency injection where appropriate

### Clean Architecture Concepts

#### Separation of Concerns
- Business logic separate from infrastructure
- Domain models independent of frameworks
- Clear boundaries between layers

#### Dependency Direction
- Dependencies should point inward
- Core business logic has no external dependencies
- Infrastructure depends on domain, not vice versa

## Code Quality Metrics

### Complexity Management
- Keep cyclomatic complexity low (< 10)
- Reduce cognitive load
- Use meaningful abstractions
- Break down complex problems

### Readability Guidelines
- Code should read like well-written prose
- Use intention-revealing names
- Prefer explicit over implicit
- Write code for humans, not just computers

### Testing Integration
- Write testable code
- Use dependency injection for testability
- Keep business logic pure and side-effect free
- Design with testing in mind

## Refactoring Guidelines

### When to Refactor
- Before adding new features
- When code smells are detected
- During code reviews
- When fixing bugs

### Refactoring Techniques
- Extract methods for complex logic
- Extract classes for related functionality
- Rename for clarity
- Remove duplication
- Simplify conditional expressions

### Code Smells to Avoid
- Long methods (> 30 lines)
- Large classes (> 200 lines)
- Duplicate code
- Long parameter lists
- Dead code
- Magic numbers
- Comments that explain what code does (code should be self-explanatory)

## Performance Considerations

### Premature Optimization
- Don't optimize without measuring
- Focus on algorithmic efficiency over micro-optimizations
- Profile before optimizing
- Maintain readability while optimizing

### Efficient Python Patterns
- Use list comprehensions appropriately
- Prefer built-in functions (sum, max, min)
- Use generators for large datasets
- Avoid unnecessary object creation

## Team Collaboration

### Code Reviews
- Review for design, not just bugs
- Check for adherence to style guidelines
- Ensure tests are comprehensive
- Verify documentation is adequate

### Consistency
- Follow project conventions
- Use automated formatting tools (Black)
- Maintain consistent naming patterns
- Apply rules uniformly across codebase

Remember: Clean code is not just about following rules - it's about writing code that clearly expresses intent and is easy to understand, modify, and maintain.
