# CriaParse

CriaParse is a backend service responsible for parsing and processing various document types as part of the Criadex RAG pipeline.

## Architecture & Dependencies

CriaParse is a backend service built with Python and FastAPI. Its primary role is to prepare documents for indexing.

- **SemanticDocumentParser**: Uses this library to intelligently parse and chunk various document formats (like `.docx` and `.pdf`) into a structured format suitable for RAG pipelines.
- **CriadexSDK**: Uses the `CriadexSDK` to communicate with the main `Criadex` service for tasks like authentication.
- **Redis**: Connects to a Redis server for caching or task queueing.

## Configuration

Configuration for the service is managed through a `.env` file in the root of the project. For local development, create this file with the following content, adjusting the values as needed.

```
# CriaParse API Settings
APP_API_MODE=TESTING
APP_API_PORT=25576

# Redis Credentials
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_USERNAME=default
REDIS_PASSWORD=password

# Criadex SDK Configuration
CRIADEX_SDK_IO_TIMEOUT=500
CRIADEX_API_BASE=http://localhost:25574
CRIADEX_API_KEY=password
```

## Local Development & Testing

1.  **Create a virtual environment:**
    ```sh
    python -m venv .venv
    source .venv/bin/activate
    ```

2.  **Install dependencies:**
    ```sh
    pip install -r requirements.txt
    ```

3.  **Run tests:**
    ```sh
    pytest
    ```

4.  **Run the development server:**
    ```sh
    python -m app
    ```
