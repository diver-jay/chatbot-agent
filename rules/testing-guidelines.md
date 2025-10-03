# Testing Guidelines for Yatzy Project

## Test Structure and Organization

### Test File Naming
- Test files should be named `test_*.py`
- Test files should mirror the structure of the source code
- Use descriptive names that indicate what is being tested

### Test Method Naming
- Use descriptive test method names that explain the scenario
- Follow pattern: `test_[method_name]_[scenario]`
- Examples:
  - `test_chance_scores_sum_of_all_dice()`
  - `test_yatzy_scores_50_when_all_dice_same()`
  - `test_pair_returns_0_when_no_pair_exists()`

## Test Data and Scenarios

### Dice Combinations to Test
- **Valid combinations**: Standard dice rolls (1-6 values)
- **Edge cases**: All same numbers, all different numbers
- **Boundary conditions**: Minimum and maximum values
- **Invalid inputs**: Empty lists, wrong number of dice, invalid values

### Test Categories
1. **Happy Path Tests**: Normal, expected scenarios
2. **Edge Case Tests**: Boundary conditions and limits
3. **Error Case Tests**: Invalid inputs and error conditions
4. **Regression Tests**: Previously fixed bugs

## Test Implementation

### Test Structure (AAA Pattern)
```python
def test_example():
    # Arrange - Set up test data
    dice = [1, 2, 3, 4, 5]
    
    # Act - Execute the method being tested
    result = Yatzy.chance(dice)
    
    # Assert - Verify the result
    assert result == 15
```

### Assertion Best Practices
- Use specific assertions (assertEqual, assertTrue, etc.)
- Provide meaningful failure messages
- Test one concept per test method
- Use descriptive variable names

### Test Data Setup
```python
# Good: Clear, descriptive test data
def test_yatzy_with_five_ones():
    dice = [1, 1, 1, 1, 1]
    assert Yatzy.yatzy(dice) == 50

# Good: Test multiple scenarios
def test_chance_scores_sum_of_all_dice():
    assert Yatzy.chance([2, 3, 4, 5, 1]) == 15
    assert Yatzy.chance([3, 3, 4, 5, 1]) == 16
    assert Yatzy.chance([3, 3, 1, 6, 1]) == 14
```

## Yatzy-Specific Test Scenarios

### Chance Category
- Test with various dice combinations
- Verify sum calculation is correct
- Test with all same numbers
- Test with all different numbers

### Yatzy Category
- Test with all five dice the same (should score 50)
- Test with four same, one different (should score 0)
- Test with all different numbers (should score 0)

### Number Categories (Ones through Sixes)
- Test with multiple dice of the target number
- Test with no dice of the target number
- Test with all dice of the target number
- Test with mixed combinations

### Pair Category
- Test with exactly two of the same number
- Test with three of the same number (should not score)
- Test with no pairs
- Test with multiple pairs (should return highest)

### Two Pair Category
- Test with exactly two pairs
- Test with three of a kind + two of a kind (should not score)
- Test with no pairs
- Test with only one pair

### Three of a Kind Category
- Test with exactly three of the same number
- Test with four of the same number (should still score)
- Test with no three of a kind
- Test with multiple three of a kinds (should return highest)

### Four of a Kind Category
- Test with exactly four of the same number
- Test with five of the same number (should still score)
- Test with no four of a kind

### Small Straight Category
- Test with [1,2,3,4,5] in any order
- Test with [2,3,4,5,6] (should not score)
- Test with missing numbers
- Test with duplicates

### Large Straight Category
- Test with [2,3,4,5,6] in any order
- Test with [1,2,3,4,5] (should not score)
- Test with missing numbers
- Test with duplicates

### Full House Category
- Test with exactly three of one number and two of another
- Test with four of one number and one of another (should not score)
- Test with all five the same (should not score)
- Test with no full house

## Test Coverage Requirements

### Minimum Coverage
- All public methods must have test coverage
- All scoring categories must be tested
- Edge cases must be covered
- Error conditions must be tested

### Coverage Goals
- Aim for 100% line coverage
- Aim for 100% branch coverage
- Test all possible dice combinations for each category
- Test invalid inputs and error conditions

## Test Maintenance

### Keeping Tests Updated
- Update tests when changing method signatures
- Add tests for new features
- Remove obsolete tests
- Refactor tests to improve readability

### Test Documentation
- Use clear test method names
- Add comments for complex test scenarios
- Document test data choices
- Explain the reasoning behind test cases

## Performance Considerations

### Test Execution Speed
- Keep tests fast and focused
- Avoid unnecessary setup and teardown
- Use efficient test data structures
- Minimize I/O operations in tests

### Test Independence
- Each test should be independent
- Tests should not depend on each other
- Tests should be able to run in any order
- Tests should clean up after themselves
description:
globs:
alwaysApply: false
---
