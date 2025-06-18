@echo off
echo Creating KomuniTech project structure...

REM Create test directories
echo Creating test directories...
mkdir tests
mkdir tests\unit
mkdir tests\unit\test_services
mkdir tests\unit\test_utils
mkdir tests\integration
mkdir tests\functional

REM Create test files
echo Creating test files...
type nul > tests\__init__.py
type nul > tests\conftest.py
type nul > tests\test_config.py
type nul > tests\README.md

REM Unit tests
type nul > tests\unit\__init__.py
type nul > tests\unit\test_models.py
type nul > tests\unit\test_forms.py

REM Unit test services
type nul > tests\unit\test_services\__init__.py
type nul > tests\unit\test_services\test_auth_service.py
type nul > tests\unit\test_services\test_project_service.py
type nul > tests\unit\test_services\test_kebutuhan_service.py
type nul > tests\unit\test_services\test_comment_service.py
type nul > tests\unit\test_services\test_support_service.py
type nul > tests\unit\test_services\test_file_service.py
type nul > tests\unit\test_services\test_category_service.py
type nul > tests\unit\test_services\test_search_service.py
type nul > tests\unit\test_services\test_notification_service.py
type nul > tests\unit\test_services\test_user_service.py

REM Unit test utils
type nul > tests\unit\test_utils\__init__.py
type nul > tests\unit\test_utils\test_decorators.py
type nul > tests\unit\test_utils\test_helpers.py
type nul > tests\unit\test_utils\test_file_utils.py
type nul > tests\unit\test_utils\test_auth_utils.py
type nul > tests\unit\test_utils\test_pagination.py

REM Integration tests
type nul > tests\integration\__init__.py
type nul > tests\integration\test_auth_routes.py
type nul > tests\integration\test_project_routes.py
type nul > tests\integration\test_kebutuhan_routes.py
type nul > tests\integration\test_admin_routes.py
type nul > tests\integration\test_api_routes.py
type nul > tests\integration\test_comment_routes.py
type nul > tests\integration\test_support_routes.py
type nul > tests\integration\test_user_routes.py
type nul > tests\integration\test_search_routes.py
type nul > tests\integration\test_main_routes.py

REM Functional tests
type nul > tests\functional\__init__.py
type nul > tests\functional\test_user_flows.py
type nul > tests\functional\test_project_lifecycle.py
type nul > tests\functional\test_kebutuhan_workflow.py
type nul > tests\functional\test_admin_workflows.py

REM Create GitHub Actions directories
echo Creating GitHub Actions workflows...
mkdir .github
mkdir .github\workflows

REM Create GitHub Actions files
type nul > .github\workflows\ci.yml
type nul > .github\workflows\cd.yml
type nul > .github\workflows\security.yml
type nul > .github\workflows\codeql.yml
type nul > .github\dependabot.yml

REM Create nginx directories and files
echo Creating nginx configuration...
mkdir nginx
mkdir nginx\conf.d
mkdir ssl

type nul > nginx\nginx.conf
type nul > nginx\conf.d\komunitech.conf

REM Create scripts directory
echo Creating scripts...
mkdir scripts
type nul > scripts\init.sql
type nul > scripts\backup.sh
type nul > scripts\deploy.sh
type nul > scripts\entrypoint.sh
type nul > scripts\wait-for-db.sh

REM Create documentation
echo Creating documentation...
mkdir docs
type nul > docs\API.md
type nul > docs\DEPLOYMENT.md
type nul > docs\CONTRIBUTING.md
type nul > docs\ARCHITECTURE.md

REM Create app missing directories
echo Creating app directories...
mkdir app\templates\errors
mkdir app\templates\email
mkdir app\templates\components
mkdir app\templates\search
mkdir app\static\uploads\projects
mkdir app\static\uploads\kebutuhan
mkdir app\static\uploads\comments
mkdir app\static\uploads\avatars
mkdir app\static\uploads\temp
mkdir logs
mkdir instance
mkdir backups

REM Create app missing template files
type nul > app\templates\errors\404.html
type nul > app\templates\errors\403.html
type nul > app\templates\errors\500.html
type nul > app\templates\errors\429.html

type nul > app\templates\search\results.html
type nul > app\templates\search\advanced.html

type nul > app\templates\admin\dashboard.html
type nul > app\templates\admin\users.html
type nul > app\templates\admin\edit_user.html
type nul > app\templates\admin\projects.html
type nul > app\templates\admin\kebutuhan.html
type nul > app\templates\admin\audit_logs.html
type nul > app\templates\admin\settings.html
type nul > app\templates\admin\update_status.html

type nul > app\templates\user\profile.html
type nul > app\templates\user\settings.html
type nul > app\templates\user\change_password.html
type nul > app\templates\user\reset_password_request.html
type nul > app\templates\user\reset_password.html
type nul > app\templates\user\notifications.html
type nul > app\templates\user\activity.html
type nul > app\templates\user\delete_account.html

type nul > app\templates\kebutuhan\edit.html
type nul > app\templates\kebutuhan\update_status.html

REM Create missing service files  
type nul > app\services\category_service.py
type nul > app\services\notification_service.py
type nul > app\services\user_service.py
type nul > app\services\audit_service.py

REM Create root configuration files
echo Creating configuration files...
type nul > .env
type nul > .env.template
type nul > .env.test
type nul > .dockerignore
type nul > .gitignore
type nul > test-requirements.txt
type nul > Makefile
type nul > locustfile.py
type nul > .coveragerc
type nul > .flake8
type nul > .pylintrc
type nul > pyproject.toml

REM Create VS Code configuration
mkdir .vscode
type nul > .vscode\launch.json
type nul > .vscode\tasks.json
type nul > .vscode\extensions.json

REM Create health check endpoint file
type nul > app\routes\health_routes.py

echo.
echo Project structure created successfully!
echo.
echo Next steps:
echo 1. Copy the content from the artifacts into the respective files
echo 2. Install dependencies: pip install -r requirements.txt
echo 3. Install test dependencies: pip install -r test-requirements.txt
echo 4. Run tests: pytest
echo.
pause