# CriaParse API Specification

## Base URL
All endpoints are rooted at:
```
http://localhost:25576/
```

Authentication: API key via HTTP header `x-api-key`.

---

## 1. Parser

### 1.1 Queue a Parse Job
POST /parser/queue
- Description: Queue a file parse job.
- Query Parameters:
  - `strategy` (string, required): The parsing strategy to use.
  - `llm_model_id` (int, optional): The ID of the LLM model to use.
  - `embedding_model_id` (int, optional): The ID of the embedding model to use.
  - `dataset_id` (string, optional): The ID of the dataset to associate with the parsed document.
  - `al_extension` (boolean, optional): Whether to use the al extension.
- Note: `group_by_h1` is automatically set to `true` for this endpoint.
- Request Body:
  - `file` (multipart/form-data): The file to parse.
- Response 200 OK (`ParserQueueResponse`):
  ```json
  {
    "status": 200,
    "message": "Successfully queued the parse job.",
    "timestamp": "<timestamp>",
    "code": "SUCCESS",
    "job": {
      "job_id": "b68ef5d9-023b-49ae-80d3-96e7aebb87ed",
      "step": null,
      "step_name": null,
      "steps": 9,
      "strategy": "GENERIC",
      "step_timings": {},
      "response": null,
      "finished": false
    }
  }
  ```

### 1.2 Poll a Parse Job
GET /parser/poll
- Description: Poll the results of a file parse job.
- Query Parameters:
  - `job_id` (string/UUID, required): The ID of the job to poll (must be valid UUID format).
- Response 200 OK (`ParserPollResponse`):
  ```json
  {
    "status": 200,
    "message": "Successfully parsed the document.",
    "timestamp": "<timestamp>",
    "code": "SUCCESS",
    "job": {
      "job_id": "b68ef5d9-023b-49ae-80d3-96e7aebb87ed",
      "step": 9,
      "step_name": "Remove Small Nodes",
      "steps": 9,
      "strategy": "GENERIC",
      "step_timings": {
        "1": {
          "step_name": "Unstructured Partition",
          "time_taken": 265.9,
          "timestamp_completed": 1763561129968.0
        },
        "2": {
          "step_name": "Metadata Parsing",
          "time_taken": 0.0,
          "timestamp_completed": 1763561129968.0
        },
        "3": {
          "step_name": "Table Parsing 1/2",
          "time_taken": 0.0,
          "timestamp_completed": 1763561129969.0
        },
        "4": {
          "step_name": "List Parsing",
          "time_taken": 0.0,
          "timestamp_completed": 1763561129969.0
        },
        "5": {
          "step_name": "Paragraph Parsing",
          "time_taken": 24.6,
          "timestamp_completed": 1763561129994.0
        },
        "6": {
          "step_name": "Table Parsing 2/2",
          "time_taken": 0.0,
          "timestamp_completed": 1763561129994.0
        },
        "7": {
          "step_name": "Image Captioning",
          "time_taken": 0.1,
          "timestamp_completed": 1763561129995.0
        },
        "8": {
          "step_name": "Window Combination",
          "time_taken": 0.0,
          "timestamp_completed": 1763561129995.0
        },
        "9": {
          "step_name": "Remove Small Nodes",
          "time_taken": 0.0,
          "timestamp_completed": 1763561129995.0
        }
      },
      "response": {
        "elements": [
          {
            "type": "Title",
            "text": "Preface\n\nThis is a test file for parsing.",
            "metadata": {
              "section_title": "Preface",
              "heading_level": 1,
              "title_metadata": {}
            },
            "element_id": "da151638-6f15-4451-b580-533c835904ec"
          }
        ],
        "assets": [],
        "timings": {
          "element_parse_time": 265.9,
          "metadata_parse_time": 0.0,
          "paragraph_parse_time": 24.6,
          "list_parse_time": 0.0,
          "table_parse_time_strategy_1": 0.0,
          "table_parse_time_strategy_2": 0.0,
          "combine_window_time": 0.0,
          "image_caption_time": 0.1
        }
      },
      "finished": true
    }
  }
  ```

### 1.3 Parse a File (Deprecated)
POST /parser/parse
- **Deprecated**: This endpoint is deprecated and may be removed in a future version. Use the queue and poll endpoints instead.
- Description: Parse a file synchronously.
- Query Parameters:
  - `strategy` (string, required): The parsing strategy to use.
  - `llm_model_id` (int, optional): The ID of the LLM model to use.
  - `embedding_model_id` (int, optional): The ID of the embedding model to use.
  - `al_extension` (boolean, optional): Whether to use the al extension.
  - `group_by_h1` (boolean, optional): Whether to group by H1 tags.
- Request Body:
  - `file`: The file to parse.
- Response 200 OK (`ParserParseResponse`):
  ```json
  {
    "status": 200,
    "message": "Successfully parsed the document.",
    "timestamp": "<timestamp>",
    "code": "SUCCESS",
    "nodes": [],
    "assets": []
  }
  ```

### 1.4 List Parsing Strategies (Deprecated)
GET /parser/strategies
- **Deprecated**: This endpoint is deprecated and may be removed in a future version.
- Description: List the available parsing strategies.
- Response 200 OK (`ParserStrategiesResponse`):
  ```json
  {
    "status": 200,
    "message": "Successfully parsed the document.",
    "timestamp": "<timestamp>",
    "code": "SUCCESS",
    "strategies": []
  }
  ```

---

## 2. Health Check

### 2.1 Health Check
GET /health_check
- Description: Check if the server is online (used for Docker health checks).
- Response 200 OK: Plain text
  ```
  Pong!
  ```