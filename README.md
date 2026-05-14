# RFP Analysis System - Multi-Agent Architecture

A production-ready system that uses LangGraph and OpenAI to process Request for Proposal (RFP) documents, extract structured requirements, and map them to Equinix's infrastructure solutions.

## Architecture

### Three-Agent Pipeline

```
RFP Text / PDF
      ↓
[Extraction Agent] → ExtractedRFP (granular Requirement objects with IDs)
      ↓
[Mapping Agent]    → SolutionMappingSet (signal-assessed, scored per play)
      ↓
[Validation Node]  → ValidationReport (grounding + catalog coverage checks)
      ↓
RFPAnalysisResponse
```

1. **Extraction Agent** (`extraction_service.py`): Parses the RFP and structures it into:
   - Administrative details (title, deadlines, contract term)
   - Company info and issuer type
   - Typed domain sub-models: `PowerSpec`, `CoolingSpec`, `NetworkSpec`, `PhysicalSecuritySpec`, `ResiliencySpec`, `OperationsSpec`
   - Granular `Requirement` objects (REQ-001, REQ-002, …) with theme, priority, quantitative value, and verbatim source excerpt
   - Evaluation criteria with weights and mandatory pass/fail items

2. **Mapping Agent** (`mapping_service.py`): Maps extracted requirements to 6 Equinix solutions using per-signal assessments:
   - Hybrid Multicloud Enablement
   - Digital Infrastructure Expansion
   - Interconnection & Ecosystem
   - Edge & Low-Latency Deployment
   - Security & Resilience
   - AI / High-Performance Compute

3. **Validation Node** (`validation_service.py`): Code-side (no LLM) checks that every cited requirement ID exists in the extraction and that every catalog play is scored exactly once.

### Project Structure
```
app/
├── models/
│   ├── rfp_extraction.py       # Enums, sub-models, ExtractedRFP
│   └── solution_mapping.py     # SignalAssessment, SolutionMappingSet, ValidationReport
├── services/
│   ├── extraction_service.py   # Agent 1: RFP extraction (OpenAI Responses API)
│   ├── mapping_service.py      # Agent 2: Solution mapping (OpenAI Responses API)
│   ├── validation_service.py   # Agent 3: Grounding & coverage validation (no LLM)
│   ├── pdf_service.py          # PDF validation and text extraction
│   └── graph_service.py        # LangGraph workflow orchestration
├── api/
│   ├── routes.py               # FastAPI endpoints
│   └── dependencies.py         # Dependency injection
├── utils/
│   └── prompts.py              # LLM prompts and solution formatting helpers
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

### Endpoint: POST `/api/v1/analyze-pdf` (PDF Upload)

Analyze a PDF RFP document with automatic text extraction and map to Equinix solutions.

**Features:**
- Accepts PDF files up to 10MB
- Validates PDF format and integrity
- Extracts text while preserving page markers (`[Page N]`) for source provenance
- Supports `text` and `markdown` output formats

**Request (multipart/form-data):**
- `file`: PDF file (required)
- `format`: `"text"` or `"markdown"` (optional, defaults to `"text"`)
- `rfp_id`: Unique identifier (optional, auto-generated if omitted)

**Interactive API test can be performed at [/docs](http://localhost:8000/docs)**

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
{ "detail": "File must be a PDF. Got: document.txt" }
```

```json
{ "detail": "File exceeds 10MB limit. Got: 15.50MB" }
```

```json
{ "detail": "Invalid PDF file: file appears to be corrupted" }
```

## Data Models

### Extraction Models (`rfp_extraction.py`)

| Model | Purpose |
|-------|---------|
| `Requirement` | Single RFP ask — ID (REQ-001…), theme, priority, quantitative value, verbatim source |
| `ExtractedRFP` | Root extraction: company, admin, workload, domain sub-models, full requirements list |
| `PowerSpec` / `CoolingSpec` / `NetworkSpec` | Typed domain views of the extracted data |
| `PhysicalSecuritySpec` / `ResiliencySpec` / `OperationsSpec` | Physical and operational typed sub-models |
| `EvaluationCriterion` | Weighted scoring criteria from the RFP |
| `MandatoryItem` | Explicit pass/fail checklist items |

### Solution Mapping Models (`solution_mapping.py`)

| Model | Purpose |
|-------|---------|
| `SignalAssessment` | MET / PARTIAL / NOT_MET verdict for one signal, with cited REQ IDs |
| `SolutionMapping` | One catalog play — signal assessments, counter-evidence, confidence, score, rationale |
| `SolutionMappingSet` | All six plays scored in catalog order |
| `ValidationReport` | Grounding issues + missing/unknown plays; `passed: bool` summary |
| `RFPAnalysisResponse` | Final response: extraction + mapping set + validation + timestamp |

### Confidence / Score System

The mapping agent produces two correlated values per solution:

| Confidence | Score Range | Meaning |
|------------|-------------|---------|
| `HIGH` | 0.75–1.00 | ≥3 signals MET, at least one mandatory requirement |
| `MEDIUM` | 0.45–0.74 | 2 signals MET, or 3+ but all preferred priority |
| `LOW` | 0.15–0.44 | 1 signal MET or weak/indirect evidence |
| `NONE` | 0.00–0.14 | No signals MET |

## Configuration

### LLM Settings
- **Model**: configurable via `OPENAI_MODEL` environment variable (default: `gpt-5.2-chat-latest`)
- **API**: OpenAI Responses API (`client.responses.parse`) with structured output (`text_format`)

### Solution Catalog
- **File**: `solutions.json` — define or extend Equinix sales plays
- **Path**: configurable via `SOLUTIONS_JSON_PATH` environment variable

## Key Design Decisions

1. **Three-node LangGraph pipeline**: Extract → Map → Validate. Validation is a deterministic code-side step with no LLM cost.

2. **Granular Requirement IDs**: Every requirement gets a stable REQ-NNN ID. The mapper cites these IDs in `SignalAssessment.requirement_ids`, making every confidence score traceable back to source text.

3. **Signal-based mapping**: Each catalog play has named signal-statements. The LLM walks them one-by-one (MET / PARTIAL / NOT_MET) before producing a confidence label and numeric score. This prevents vague "overall fit" judgements.

4. **Calibrated confidence**: When uncertain between two tiers, the rubric instructs the model to choose the lower one. Underconfidence is more useful downstream than enthusiastic mapping.

5. **OpenAI Responses API with `text_format`**: Both services use `client.responses.parse(text_format=<PydanticModel>)` so the LLM output is parsed and validated in one call — no manual JSON wrangling.

6. **Verbatim source provenance**: Every extracted field includes a `SourceSpan` (page number + verbatim excerpt). This lets downstream consumers verify claims without re-reading the full RFP.

7. **Pydantic validators enforce invariants**: `SignalAssessment` rejects `NOT_MET` signals that cite IDs and rejects `MET`/`PARTIAL` signals with no IDs. `SolutionMapping` rejects score/confidence mismatches at construction time.

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
- Consider smaller models for simpler RFPs

## Troubleshooting

### "OpenAI API key not found"
Ensure `OPENAI_API_KEY` environment variable is set.

### "Could not parse JSON from LLM response"
Check that the RFP text is detailed enough for accurate extraction. Minimum 100 characters recommended.

### "Timeout connecting to OpenAI"
Verify internet connection and OpenAI API status. Check rate limits if processing many RFPs.

### Validation report shows `passed: false`
Check `issues` for grounding problems (requirement IDs the mapper invented) and `missing_catalog_plays` / `unknown_catalog_plays` for coverage gaps. These are warnings — the response is still returned.

## Testing

### Test with Sample RFP
See `Dataset/` folder for sample RFP documents. Upload via the `/api/v1/analyze-pdf` endpoint or Swagger UI.

### Unit Tests
```bash
python test_api.py
```

## Future Enhancements

- [ ] Batch processing endpoint
- [ ] Result caching layer
- [ ] Solution recommendation explanations
- [ ] Multi-language support
- [ ] Integration with CRM systems
- [ ] Support for additional file formats (DOCX, TXT)
- [ ] Re-extraction loop when validation fails grounding checks
