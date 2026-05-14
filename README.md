# RFP Analysis System - Multi-Agent Architecture

A production-ready system that uses LangGraph and OpenAI to process Request for Proposal (RFP) documents, extract structured requirements, and map them to Equinix's infrastructure solutions.

## Architecture

### Two-Agent Pipeline
1. **Extraction Agent**: Parses RFP documents and structures them into:
   - Company information (name, industry, size)
   - Technical requirements (compute, storage, networking)
   - Security requirements (compliance, encryption, threat models)
   - Operational constraints (budget, timeline, SLAs)

2. **Solution Mapper Agent**: Maps extracted requirements to 6 Equinix solutions:
   - Hybrid Multicloud Enablement
   - Digital Infrastructure Expansion
   - Interconnection & Ecosystem
   - Edge & Low-Latency Deployment
   - Security & Resilience
   - AI / High-Performance Compute

### Project Structure
```
app/
├── models/
│   ├── rfp_extraction.py      # Pydantic models for extracted RFP data
│   └── solution_mapping.py     # Pydantic models for solution mappings
├── services/
│   ├── extraction_service.py   # Agent 1: RFP extraction logic
│   ├── mapping_service.py      # Agent 2: Solution mapping logic
│   ├── pdf_service.py          # PDF validation and conversion
│   └── graph_service.py        # LangGraph workflow orchestration
├── api/
│   ├── routes.py               # FastAPI endpoints
│   └── dependencies.py         # Dependency injection
├── utils/
│   └── prompts.py              # LLM prompts and solution definitions
└── main.py                     # FastAPI application
```

## Prerequisites

- Python 3.13+
- OpenAI API key (GPT-5 model access)
- `uv` package manager (or `pip`)

## Setup

### 1. Install Dependencies
```bash
# Using uv (recommended)
uv sync

# Or using pip (not recommended)
pip install -r requirements.txt
```

### 2. Set OpenAI API Key OR use the one provided in the .env file
```bash
# Linux/Mac
export OPENAI_API_KEY="your-api-key-here"

# Windows (PowerShell)
$env:OPENAI_API_KEY="your-api-key-here"

# Or edit the .env file
echo "OPENAI_API_KEY=your-api-key-here" > .env
```
OR use the one provided in the .env file 

   PS: I am sharing the .env file only to facilitate faster testing. I strongly do not recommend sharing credentials in the .env file as they are supposed to be confidential.

## Running the Application

### Start the API Server
```bash
# Using uvicorn directly
uvicorn main:app --host 0.0.0.0 --port 8000 --reload

# Or using Python
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### Endpoint : POST `/api/v1/analyze-pdf` (PDF Upload)

Analyze PDF RFP document with automatic text extraction and map to solutions.

**Features:**
- Accepts PDF files up to 10MB
- Validates PDF format and integrity
- Extracts text while preserving document layout
- Supports `text` and `markdown` output formats
- Maintains structure for accurate analysis

**Request (multipart/form-data):**
- `file`: PDF file (required)
- `format`: "text" or "markdown" (optional, defaults to "text")
- `rfp_id`: Unique identifier (optional, auto-generated if omitted)

**Interactive API test can be performed in the [/docs](http://localhost:8000/docs)**

**Example: Using Python**

```python
import requests

url = "http://localhost:8000/api/v1/analyze-pdf"

with open("rfp_document.pdf", "rb") as f:
    files = {"file": f}
    data = {
        "format": "markdown",
        "rfp_id": "my-rfp-001"
    }
    response = requests.post(url, files=files, data=data)
    result = response.json()
    print(result)
```

**Error Responses:**

```json
{
  "detail": "File must be a PDF. Got: document.txt"
}
```

```json
{
  "detail": "File exceeds 10MB limit. Got: 15.50MB"
}
```

```json
{
  "detail": "Invalid PDF file: file appears to be corrupted"
}
```

## Configuration

### LLM Settings
- **Model**: GPT-5 (configured in services)
- **Timeout**: Default OpenAI client timeout

## Key Design Decisions

1. **Sequential Agent Pipeline**: RFP extraction feeds directly into solution mapping for accuracy and context.

2. **Pydantic Models**: Strong type validation ensures structured output consistency.

3. **OpenAI GPT-5**: The model has a higher context window that supports large PDFs,hence no need for chunking. Chosen for superior reasoning and domain understanding of infrastructure requirements.

4. **LangGraph**: Provides clear orchestration and state management for multi-step workflows.

5. **FastAPI**: Modern, production-ready async framework with automatic OpenAPI documentation.

6. **Confidence Level**: The LLM provides a category based range such as (high/medium/low) over a numerical range. This would reduce chances of model hallucinations.

## Scaling Considerations

### Production Deployment - To be implemented
- Add request queuing for high volume
- Implement result caching (Redis)
- Add request rate limiting
- Use async task queue (Celery, RQ) for long-running analysis

### Multi-tenant Support
- Add tenant isolation in database
- Implement API key authentication
- Track usage per tenant

### Cost Optimization
- Batch process RFPs during off-peak hours
- Cache solution definitions
- Consider other lower parameter models for reducing cost.

## Troubleshooting

### "OpenAI API key not found"
Ensure `OPENAI_API_KEY` environment variable is set.

### "Could not parse JSON from LLM response"
Check that RFP text is detailed enough for accurate extraction. Minimum 100 characters recommended.

### "Timeout connecting to OpenAI"
Verify internet connection and OpenAI API status. Check rate limits if processing many RFPs.

## Testing

### Test with Sample RFP
See `Dataset/` folder for sample RFP documents. Extract text and test via the API.

### Unit Tests
```bash
python test_api.py
```

## Future Enhancements

- [ ] Batch processing endpoint
- [ ] Result caching layer
- [ ] Custom confidence score tuning
- [ ] Solution recommendation explanations
- [ ] Multi-language support
- [ ] Integration with CRM systems
- [ ] Support for additional file formats (DOCX, TXT)
- [ ] LLM output verification 
