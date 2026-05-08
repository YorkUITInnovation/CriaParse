import sys
import os
import importlib
import pytest

@pytest.fixture
def mock_env_file():
    """Fixture for creating a mock environment file."""
    test_env_dir = '/tmp/test_env'
    test_env_file = f'{test_env_dir}/docker.env'
    os.makedirs(test_env_dir, exist_ok=True)

    with open(test_env_file, 'w') as f:
        f.write("""# Test environment file
APP_API_MODE=TESTING
APP_API_PORT=25574
API_KEY=test-key-for-docker
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_USERNAME=
REDIS_PASSWORD=
CRIADEX_API_BASE=https://api.example.com
CRIADEX_API_KEY=your-criadex-api-key
""")

    original_env_path = os.environ.get('ENV_PATH')
    original_app_api_mode = os.environ.get('APP_API_MODE')
    original_app_api_port = os.environ.get('APP_API_PORT')
    original_api_key = os.environ.get('API_KEY')

    os.environ['ENV_PATH'] = test_env_file
    os.environ['APP_API_MODE'] = 'TESTING'
    os.environ['APP_API_PORT'] = '25574'
    os.environ['API_KEY'] = 'test-key-for-docker'

    yield

    if original_env_path is None:
        os.environ.pop('ENV_PATH', None)
    else:
        os.environ['ENV_PATH'] = original_env_path

    if original_app_api_mode is None:
        os.environ.pop('APP_API_MODE', None)
    else:
        os.environ['APP_API_MODE'] = original_app_api_mode

    if original_app_api_port is None:
        os.environ.pop('APP_API_PORT', None)
    else:
        os.environ['APP_API_PORT'] = original_app_api_port

    if original_api_key is None:
        os.environ.pop('API_KEY', None)
    else:
        os.environ['API_KEY'] = original_api_key

    if os.path.exists(test_env_file):
        os.remove(test_env_file)
    if os.path.exists(test_env_dir):
        os.rmdir(test_env_dir)

def test_docker_environment_setup(mock_env_file):
    """Test to validate the Docker environment setup with the correct ENV_PATH"""
    assert "ENV_PATH" in os.environ
    assert os.path.isfile(os.environ['ENV_PATH'])

    from app.core import config as config_module
    config = importlib.reload(config_module)
    import app.__main__

    assert config.APP_MODE.name == "TESTING"
    assert config.APP_PORT == 25574
    assert config.API_KEY == "test-key-for-docker"