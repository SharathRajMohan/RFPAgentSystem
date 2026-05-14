# RFP Multi-Agent Analysis System - Setup & Deployment Guide

## System Overview

A three-agent LangGraph pipeline integrated with FastAPI that processes PDF RFP documents and maps them to Equinix infrastructure solutions.

### Components Overview

#### 1. Extraction Agent (`app/services/extraction_service.py`)
- Calls the OpenAI Responses API (`client.responses.parse`) with a detailed system prompt
- Extracts a richly-typed `ExtractedRFP` including:
  - Administrative details (title, deadlines, contract term)
  - Company profile and issuer type
  - Typed domain sub-models: `PowerSpec`, `CoolingSpec`, `NetworkSpec`, `PhysicalSecuritySpec`, `ResiliencySpec`, `OperationsSpec`
  - Granular `Requirement` list (REQ-001, REQ-002, …) with theme, priority, quantitative value, and verbatim source excerpt
  - Evaluation criteria with weights; mandatory pass/fail items

#### 2. Solution Mapper Agent (`app/services/mapping_service.py`)
- Scores all 6 Equinix catalog plays in a single call:
  - Hybrid Multicloud Enablement
  - Digital Infrastructure Expansion
  - Interconnection & Ecosystem
  - Edge & Low-Latency Deployment
  - Security & Resilience
  - AI / High-Performance Compute
- Per play: signal assessments (MET/PARTIAL/NOT_MET), counter-evidence, confidence label, numeric score (0.0–1.0), and rationale
- Every play is scored (no filtering by threshold)

#### 3. Validation Node (`app/services/validation_service.py`)
- Deterministic, no LLM call
- Grounding check: every cited REQ-xxx ID must exist in the extraction
- Coverage check: every catalog play scored exactly once
- Returns a `ValidationReport` included in the final response

#### 4. LangGraph Orchestration (`app/services/graph_service.py`)
- Three sequential nodes: extract → map → validate
- Shared `RFPProcessState` TypedDict passed between nodes

#### 5. FastAPI REST API (`app/api/routes.py`)
- `POST /api/v1/analyze-pdf` — main analysis endpoint (PDF upload)
- `GET /api/v1/health` — health check
- Built-in Swagger UI at `/docs`

### Project Structure
```
Equinix_DSCodeAlong/
├── app/
│   ├── models/
│   │   ├── rfp_extraction.py       # Enums, sub-models, ExtractedRFP
│   │   └── solution_mapping.py     # SignalAssessment, SolutionMappingSet, ValidationReport
│   ├── services/
│   │   ├── extraction_service.py   # Agent 1: RFP extraction
│   │   ├── mapping_service.py      # Agent 2: Solution mapping
│   │   ├── validation_service.py   # Agent 3: Grounding & coverage (no LLM)
│   │   ├── pdf_service.py          # PDF validation & text extraction
│   │   └── graph_service.py        # LangGraph workflow (extract→map→validate)
│   ├── api/
│   │   ├── routes.py               # FastAPI endpoints
│   │   └── dependencies.py         # Dependency injection
│   └── utils/
│       └── prompts.py              # LLM prompts & catalog formatting
├── main.py                         # FastAPI app entry point
├── solutions.json                  # Equinix catalog (6 sales plays)
├── test_api.py                     # Test suite
├── pyproject.toml                  # Dependencies
├── uv.lock                         # Locked versions
└── README.md                       # Full documentation
```

## Quick Start

### Step 1: Set Your OpenAI API Key

**On Windows (PowerShell):**
```powershell
$env:OPENAI_API_KEY="sk-your-api-key-here"
```

**On Windows (Command Prompt):**
```cmd
set OPENAI_API_KEY=sk-your-api-key-here
```

**On Linux/Mac:**
```bash
export OPENAI_API_KEY="sk-your-api-key-here"
```

**Or create a .env file in the project root:**
```
OPENAI_API_KEY=sk-your-api-key-here
```

### Step 2: Install Dependencies

```bash
uv sync
```

### Step 3: Start the API Server

```bash
# Using uv (recommended)
uv run python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload

# Or directly with Python (if uv environment active)
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

You should see:
```
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Application startup complete
```

### Step 4: Test the API

**Option A: Using Swagger UI (Browser)**
1. Open http://localhost:8000/docs
2. Click "Try it out" on the `/api/v1/analyze-pdf` endpoint
3. Upload a PDF from the `Dataset/` folder
4. Click "Execute"

**Option B: Using Python**
```python
import requests

with open("Dataset/CCAC_RFP.pdf", "rb") as f:
    response = requests.post(
        "http://localhost:8000/api/v1/analyze-pdf",
        files={"file": f},
        data={"format": "markdown", "rfp_id": "ccac-001"}
    )
print(response.json())
```

**Option C: Run the test suite**
```bash
uv run python test_api.py
```

## Expected Output Shape

```json
{
  "extracted_data": {
    "rfp_id": "ccac-001",
    "company_info": { "name": "CCAC", "issuer_type": "higher_education" },
    "administrative": {
      "rfp_title": "Colocation Services RFP",
      "submission_deadline": "2026-06-15"
    },
    "power": { "total_kw": 35.0, "redundancy_level": "N+1" },
    "requirements": [
      {
        "id": "REQ-001",
        "theme": "power",
        "description": "Facility must supply 35 kW of conditioned power",
        "priority": "mandatory",
        "quantitative_value": "35 kW",
        "source": { "page": 4, "excerpt": "The facility shall provide a minimum of 35 kW..." }
      }
    ],
    "evaluation_criteria": [
      { "category": "Location", "weight_pct": 20.0 },
      { "category": "Power & Facility Infrastructure", "weight_pct": 25.0 }
    ]
  },
  "solution_mappings": {
    "mappings": [
      {
        "solution_name": "Security & Resilience",
        "signal_assessments": [
          {
            "signal": "Customer requires compliance certifications (SOC 2, HIPAA, PCI, etc.)",
            "status": "MET",
            "requirement_ids": ["REQ-012", "REQ-013"]
          }
        ],
        "counter_evidence": null,
        "confidence": "HIGH",
        "score": 0.88,
        "rationale": "Two mandatory compliance requirements are directly evidenced..."
      }
    ]
  },
  "validation": {
    "passed": true,
    "issues": [],
    "missing_catalog_plays": [],
    "unknown_catalog_plays": []
  },
  "analysis_timestamp": "2026-05-15T10:30:45.123456+00:00"
}
```

## Key Features

### Multi-Agent Architecture
- Three-node sequential workflow: extract → map → validate
- State shared between nodes via `RFPProcessState` TypedDict
- LangGraph provides clear orchestration and state management

### Granular Traceability
- Every requirement has a stable REQ-NNN ID
- Every mapper confidence score is backed by cited REQ IDs
- Every extracted field includes page number and verbatim source excerpt
- Deterministic validation confirms cited IDs actually exist

### Data Validation
- Pydantic v2 validators enforce score/confidence consistency
- REQ-ID format enforced at construction time
- `NOT_MET` signals cannot cite IDs; `MET`/`PARTIAL` must cite at least one

### Production Ready
- Error handling and HTTP exceptions
- Dependency injection pattern
- CORS enabled
- Health check endpoint
- Swagger/OpenAPI documentation

## Customization

### Change LLM Model
Edit `app/services/extraction_service.py` and `app/services/mapping_service.py`:
```python
model="gpt-5.2-chat-latest"   # Current (best reasoning, large context)
model="gpt-4o"                 # Faster, lower cost
```

### Modify Solution Catalog
Edit `solutions.json` — keys are play names (must match exactly what the mapper returns).
Override the path via env var:
```bash
SOLUTIONS_JSON_PATH=/path/to/my-catalog.json
```

### Extend Extraction Sub-Models
Add fields to the relevant sub-model in `app/models/rfp_extraction.py` and update `EXTRACTION_SYSTEM_PROMPT` in `app/utils/prompts.py` with instructions for the new field.

### Batch Processing Example

```python
import json
from app.services.graph_service import RFPProcessGraph
from app.services.pdf_service import PDFService

graph = RFPProcessGraph()
pdf_service = PDFService()

pdf_files = ["Dataset/CCAC_RFP.pdf", "Dataset/WHEDA_RFP.pdf"]
results = []

for pdf_path in pdf_files:
    with open(pdf_path, "rb") as f:
        pdf_bytes = f.read()

    rfp_text = pdf_service.extract_text(pdf_bytes, format="text")
    analysis = graph.process_rfp(rfp_text, rfp_id=pdf_path)
    results.append(analysis.model_dump())

with open("analysis_results.json", "w") as f:
    json.dump(results, f, indent=2, default=str)
```

## Troubleshooting

### "ModuleNotFoundError: No module named 'app'"
Run from the project root directory using `uv run`.

### "Missing credentials. Please pass an `api_key`..."
Set `OPENAI_API_KEY` before starting the server.

### "File must be a PDF" / "File exceeds 10MB limit"
Only PDF files up to 10MB are accepted. Use the `Dataset/` samples for testing.

### `validation.passed` is `false` in the response
This is a warning, not a hard error — the response is still returned. Check:
- `validation.issues` — mapper cited a REQ ID not in the extraction (hallucinated ID)
- `validation.missing_catalog_plays` — a catalog play was omitted
- `validation.unknown_catalog_plays` — mapper invented a play name not in `solutions.json`

### "Connection refused"
Start the server: `uv run python -m uvicorn main:app --host 0.0.0.0 --port 8000`

## Next Steps

1. **Add Authentication**: Implement API key validation in `dependencies.py`
2. **Add Database**: Store analysis results in PostgreSQL/MongoDB
3. **Batch Endpoint**: Add `/api/v1/analyze-batch` for multiple PDFs
4. **Re-extraction Loop**: When validation fails grounding checks, re-invoke extraction
5. **Caching**: Cache solution definitions and prior results (Redis)
6. **Monitoring**: Add structured logging and metrics (Prometheus/Grafana)
7. **Rate Limiting**: Add per-client rate limits to prevent API abuse

## Additional Resources

- **LangGraph Docs**: https://langchain-ai.github.io/langgraph/
- **FastAPI Docs**: https://fastapi.tiangolo.com/
- **OpenAI Responses API**: https://platform.openai.com/docs/api-reference/responses
- **Pydantic Docs**: https://docs.pydantic.dev/

---

**Status**: Production Ready
