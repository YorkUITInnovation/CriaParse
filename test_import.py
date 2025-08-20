#!/usr/bin/env python3
"""
Test script to validate the Docker environment setup with the correct ENV_PATH
"""
import sys
import os

print("🔍 Testing Docker environment setup...")
print(f"Python version: {sys.version}")
print(f"Current working directory: {os.getcwd()}")

# Simulate the Docker environment
os.environ['ENV_PATH'] = '/home/cria/env/docker.env'

# Create a mock environment file for testing
test_env_dir = '/tmp/test_env'
test_env_file = f'{test_env_dir}/docker.env'
os.makedirs(test_env_dir, exist_ok=True)

# Create a minimal test environment file
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

# Update ENV_PATH to point to our test file
os.environ['ENV_PATH'] = test_env_file

try:
    print(f"\n📁 Testing with ENV_PATH: {os.environ['ENV_PATH']}")
    print(f"📁 File exists: {os.path.isfile(test_env_file)}")

    print("\n📦 Testing app.core import...")
    from app.core import config
    print("✅ Successfully imported app.core.config")

    print("\n📦 Testing app.__main__ import...")
    import app.__main__
    print("✅ Successfully imported app.__main__")

    print("\n🎉 All imports successful! Docker setup should work.")

except ImportError as e:
    print(f"❌ Import failed: {e}")
    print("\n🔧 Troubleshooting:")
    print("- Check that your docker.env file contains all required variables")
    print("- Verify the volume mount path in docker-compose.yml")
    sys.exit(1)

finally:
    # Clean up
    if os.path.exists(test_env_file):
        os.remove(test_env_file)
    if os.path.exists(test_env_dir):
        os.rmdir(test_env_dir)
