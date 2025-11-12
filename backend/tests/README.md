# Testing

## Running Tests

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/general/test_auth_jwt.py

# Run with coverage
pytest --cov=. --cov-report=html

# Run with verbose output
pytest -v
```

## Test Structure

- `tests/general/` - General API tests (auth, submissions, user meta, lottery)
- `tests/admin/` - Admin API tests (warn, suspend, ban, soft delete, permissions)

## CI/CD

Tests are automatically run on GitHub Actions for:
- Code quality (ruff, black, isort)
- Type checking (mypy)
- Unit tests (pytest)

See `.github/workflows/test.yml` for details.

