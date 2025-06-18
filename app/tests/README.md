# KomuniTech Testing Guide

This guide provides comprehensive information about testing the KomuniTech application.

## Table of Contents
- [Setup](#setup)
- [Running Tests](#running-tests)
- [Test Structure](#test-structure)
- [Writing Tests](#writing-tests)
- [Coverage](#coverage)
- [Continuous Integration](#continuous-integration)

## Setup

### 1. Install Test Dependencies

```bash
pip install -r requirements.txt
pip install -r test-requirements.txt
```

### 2. Set Up Test Database

The test suite uses an in-memory SQLite database by default. For PostgreSQL testing:

```bash
# Create test database
createdb komunitech_test

# Set environment variable
export TEST_DATABASE_URL=postgresql://user:password@localhost/komunitech_test
```

### 3. Configure Test Environment

Create a `.env.test` file:

```env
FLASK_ENV=testing
SECRET_KEY=test-secret-key
DATABASE_URL=sqlite:///:memory:
WTF_CSRF_ENABLED=false
```

## Running Tests

### Run All Tests

```bash
# Basic test run
pytest

# With verbose output
pytest -v

# With coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/unit/test_models.py

# Run specific test class
pytest tests/unit/test_models.py::TestPenggunaModel

# Run specific test method
pytest tests/unit/test_models.py::TestPenggunaModel::test_create_user
```

### Run Tests by Type

```bash
# Unit tests only
pytest tests/unit/

# Integration tests only
pytest tests/integration/

# Functional tests only
pytest tests/functional/
```

### Run Tests in Parallel

```bash
# Install pytest-xdist
pip install pytest-xdist

# Run tests in parallel
pytest -n auto
```

## Test Structure

```
tests/
├── conftest.py          # Shared fixtures and configuration
├── unit/                # Unit tests for individual components
│   ├── test_models.py
│   ├── test_forms.py
│   ├── test_services/
│   └── test_utils/
├── integration/         # Integration tests for routes and APIs
│   ├── test_auth_routes.py
│   ├── test_project_routes.py
│   └── test_api_routes.py
└── functional/          # End-to-end functional tests
    └── test_user_flows.py
```

## Writing Tests

### 1. Unit Tests

Test individual components in isolation:

```python
def test_user_password_hashing(db):
    """Test password hashing functionality."""
    user = Pengguna(username='test', email='test@example.com', nama='Test')
    user.set_password('mypassword')
    
    assert user.password_hash != 'mypassword'
    assert user.check_password('mypassword') is True
    assert user.check_password('wrongpassword') is False
```

### 2. Integration Tests

Test how components work together:

```python
def test_project_creation_flow(client, auth_client, categories):
    """Test complete project creation flow."""
    response = auth_client.post('/project/create', data={
        'judul': 'Test Project',
        'deskripsi': 'Test Description',
        'kategori': categories[0].id
    }, follow_redirects=True)
    
    assert response.status_code == 200
    assert b'Project created successfully' in response.data
```

### 3. Functional Tests

Test complete user workflows:

```python
def test_user_journey_create_and_support_kebutuhan(client, db):
    """Test complete user journey from registration to supporting kebutuhan."""
    # Register user
    # Create project
    # Submit kebutuhan
    # Another user supports kebutuhan
    # Verify support count
```

## Fixtures

Common fixtures available in `conftest.py`:

- `app`: Flask application instance
- `client`: Test client
- `db`: Database session
- `user`: Test user
- `admin_user`: Admin user
- `auth_client`: Authenticated client
- `project`: Test project
- `kebutuhan`: Test kebutuhan
- `categories`: Test categories

## Coverage

### Generate Coverage Report

```bash
# Terminal report
pytest --cov=app --cov-report=term-missing

# HTML report
pytest --cov=app --cov-report=html
# Open htmlcov/index.html in browser

# XML report (for CI)
pytest --cov=app --cov-report=xml
```

### Coverage Goals

- Minimum overall coverage: 80%
- Critical paths coverage: 95%
- New code coverage: 90%

### Exclude from Coverage

Add to `.coveragerc`:

```ini
[run]
omit = 
    */tests/*
    */migrations/*
    */venv/*
    */config.py
    */__init__.py
```

## Best Practices

### 1. Test Naming

Use descriptive test names:
```python
# Good
def test_user_cannot_support_own_kebutuhan():
    pass

# Bad
def test_support():
    pass
```

### 2. Arrange-Act-Assert

Structure tests clearly:
```python
def test_something():
    # Arrange - set up test data
    user = create_test_user()
    
    # Act - perform the action
    result = user.do_something()
    
    # Assert - verify the result
    assert result == expected_value
```

### 3. Use Fixtures

Don't repeat setup code:
```python
# Good - use fixture
def test_with_user(user):
    assert user.username == 'testuser'

# Bad - repeat setup
def test_without_fixture():
    user = Pengguna(username='testuser', ...)
    db.session.add(user)
    db.session.commit()
    assert user.username == 'testuser'
```

### 4. Test Edge Cases

```python
def test_kebutuhan_with_empty_description(client, auth_client):
    """Test kebutuhan creation with empty description."""
    response = auth_client.post('/kebutuhan/create', data={
        'judul': 'Test',
        'deskripsi': '',  # Empty
        'kategori': 1
    })
    assert b'Deskripsi kebutuhan harus diisi' in response.data
```

### 5. Mock External Services

```python
@patch('app.services.email_service.send_email')
def test_email_notification(mock_send_email, user):
    """Test email notification is sent."""
    # Test code
    mock_send_email.assert_called_once_with(
        to=user.email,
        subject='Expected Subject'
    )
```

## Continuous Integration

Tests run automatically on:
- Every push to `main` and `develop`
- Every pull request
- Scheduled weekly dependency updates

See `.github/workflows/ci.yml` for configuration.

## Debugging Tests

### Run with debugging

```bash
# Drop into debugger on failure
pytest --pdb

# Show print statements
pytest -s

# Show local variables on failure
pytest -l
```

### VS Code Configuration

Add to `.vscode/launch.json`:

```json
{
    "name": "Python: Pytest",
    "type": "python",
    "request": "launch",
    "module": "pytest",
    "args": ["-v", "${file}"],
    "console": "integratedTerminal"
}
```

## Performance Testing

For load testing, use `locust`:

```bash
pip install locust

# Create locustfile.py
# Run load tests
locust -f locustfile.py --host=http://localhost:5000
```

## Security Testing

```bash
# Run security checks
safety check
bandit -r app/

# Check for SQL injection vulnerabilities
sqlmap -u "http://localhost:5000/search?q=test"
```

## Troubleshooting

### Common Issues

1. **Database not found**: Ensure test database exists
2. **Import errors**: Check PYTHONPATH includes project root
3. **Fixture not found**: Verify fixture is in conftest.py or imported
4. **Tests hanging**: Check for uncommitted transactions

### Clean Test State

```bash
# Remove test artifacts
rm -rf .pytest_cache/
rm -rf htmlcov/
rm .coverage
find . -type d -name __pycache__ -exec rm -rf {} +
```