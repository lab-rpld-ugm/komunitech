# Unit Tests Structure for KomuniTech

## Test Directory Structure
```
tests/
├── __init__.py
├── conftest.py                 # Pytest configuration and fixtures
├── test_config.py             # Test configuration
├── unit/
│   ├── __init__.py
│   ├── test_models.py         # Model tests
│   ├── test_forms.py          # Form validation tests
│   ├── test_services/
│   │   ├── __init__.py
│   │   ├── test_auth_service.py
│   │   ├── test_project_service.py
│   │   ├── test_kebutuhan_service.py
│   │   ├── test_comment_service.py
│   │   ├── test_support_service.py
│   │   └── test_file_service.py
│   └── test_utils/
│       ├── __init__.py
│       ├── test_decorators.py
│       ├── test_helpers.py
│       └── test_file_utils.py
├── integration/
│   ├── __init__.py
│   ├── test_auth_routes.py
│   ├── test_project_routes.py
│   ├── test_kebutuhan_routes.py
│   ├── test_admin_routes.py
│   └── test_api_routes.py
└── functional/
    ├── __init__.py
    └── test_user_flows.py     # End-to-end user journey tests
```

## Test Requirements (test-requirements.txt)
```
pytest==7.4.3
pytest-flask==1.3.0
pytest-cov==4.1.0
pytest-mock==3.12.0
factory-boy==3.3.0
faker==20.1.0
coverage==7.3.2
```