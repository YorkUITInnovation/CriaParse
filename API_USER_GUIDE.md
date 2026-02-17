# CriaParse API User Guide

This guide shows how to interact with the CriaParse HTTP API using `curl`. For each endpoint, you’ll see required headers, request examples, and sample responses.

## Prerequisites
- You must have a valid API key. Set it in `x-api-key` header.
- `HOST` and `PORT` point to your running service (default `http://localhost:25576`).

Example environment variables:
```bash
export HOST=http://localhost
export PORT=25576
export API_KEY=your_api_key_here
```

## Common Headers
```
Content-Type: application/json
x-api-key: ${API_KEY}
```

---

## 1. Parser

### 1.1 Queue a Parse Job
POST /parser/queue

Request:
```bash
curl -X POST "${HOST}:${PORT}/parser/queue?strategy=GENERIC&dataset_id=test-dataset" \
  -H "x-api-key: ${API_KEY}" \
  -F "file=@/path/to/your/file.txt"
```

Response (200 OK):
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

Request:
```bash
curl "${HOST}:${PORT}/parser/poll?job_id=b68ef5d9-023b-49ae-80d3-96e7aebb87ed" \
  -H "x-api-key: ${API_KEY}"
```

Response (200 OK):
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

Note: While the job is still running, the `message` field will be `"Currently parsing the document."` and `finished` will be `false`.

---

## 2. Health Check

### 2.1 Health Check
GET /health_check

Request:
```bash
curl "${HOST}:${PORT}/health_check"
```

Response (200 OK):
```
Pong!
```