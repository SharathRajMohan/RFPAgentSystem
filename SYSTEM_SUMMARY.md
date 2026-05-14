# Multi-Agent RFP Analysis System - System Summary

## What Was Built

A production-ready **LangGraph multi-agent system** integrated with **FastAPI** to process PDF RFP documents, extract granular structured requirements, and map them to Equinix infrastructure solutions with signal-level evidence and deterministic validation.

---

## Project Structure

```
Equinix_DSCodeAlong/
│
├── app/                              # Main application package
│   ├── __init__.py
│   │
│   ├── models/                       # Pydantic data models
│   │   ├── rfp_extraction.py         # Enums, sub-models, ExtractedRFP
│   │   └── solution_mapping.py       # SignalAssessment, SolutionMappingSet, ValidationReport
│   │
│   ├── services/                     # Core business logic
│   │   ├── extraction_service.py     # Agent 1: RFP extraction (Responses API)
│   │   ├── mapping_service.py        # Agent 2: Signal-based solution mapping
│   │   ├── validation_service.py     # Agent 3: Grounding + coverage validation (no LLM)
│   │   ├── pdf_service.py            # PDF validation and text extraction
│   │   └── graph_service.py          # LangGraph orchestration (extract→map→validate)
│   │
│   ├── api/                          # FastAPI REST API
│   │   ├── routes.py                 # POST /api/v1/analyze-pdf endpoint
│   │   └── dependencies.py           # Dependency injection (OpenAI client)
│   │
│   └── utils/                        # Utilities
│       └── prompts.py                # LLM prompts & solution catalog formatting
│
├── main.py                           # FastAPI application entry point
├── solutions.json                    # Equinix catalog (6 sales plays)
├── test_api.py                       # API test suite
├── check_setup.py                    # Dependency & configuration checker
│
├── README.md                         # Full API documentation
├── ARCHITECTURE.md                   # Architecture diagrams and data flow
├── SYSTEM_SUMMARY.md                 # This file
├── DEPLOYMENT.md                     # Deployment & customization guide
├── QUICKSTART.md                     # Quick reference card
├── DELIVERY_CHECKLIST.md             # Implementation checklist
│
├── Dataset/                          # Sample RFP PDFs for testing
├── pyproject.toml                    # Project dependencies
└── uv.lock                           # Locked dependency versions
```

---

## Agent Pipeline

### Agent 1: Extraction Agent
**Location**: [app/services/extraction_service.py](app/services/extraction_service.py)

```python
ExtractionService.extract_rfp_info(rfp_text: str) -> ExtractedRFP
```

**What it does:**
- Calls the OpenAI Responses API (`client.responses.parse`) with a detailed system prompt
- Extracts a rich, typed `ExtractedRFP` object:
  - Company profile (`CompanyInfo`, `IssuerType` enum)
  - Administrative details (deadlines, contract term, contact)
  - Workload profile (use case, listed equipment, high-density flag)
  - Domain sub-models: `PowerSpec`, `CoolingSpec`, `NetworkSpec`, `PhysicalSecuritySpec`, `ResiliencySpec`, `OperationsSpec`
  - **Granular `Requirement` list** — every distinct ask as a REQ-NNN object with theme, priority, quantitative value, and verbatim source
  - Evaluation criteria with weights; mandatory pass/fail items
- Uses `text_format=ExtractedRFP` so the LLM output is parsed into a Pydantic model directly

---

### Agent 2: Mapping Agent
**Location**: [app/services/mapping_service.py](app/services/mapping_service.py)

```python
MappingService.map_to_solutions(extracted_rfp: ExtractedRFP) -> SolutionMappingSet
```

**What it does:**
- Serializes the `ExtractedRFP` as JSON and injects it into the mapping prompt
- Calls OpenAI Responses API with `text_format=SolutionMappingSet`
- For each of the 6 catalog plays, the model:
  1. Walks each signal-statement (MET / PARTIAL / NOT_MET), citing REQ IDs as evidence
  2. Identifies counter-evidence (RFP facts arguing against this play)
  3. Assigns a `Confidence` label (HIGH/MEDIUM/LOW/NONE) per rubric
  4. Produces a numeric `score` in `[0, 1]` consistent with the confidence tier
  5. Writes a 2–3 sentence rationale
- Returns a `SolutionMappingSet` containing all 6 plays in catalog order

---

### Agent 3: Validation Node
**Location**: [app/services/validation_service.py](app/services/validation_service.py)

```python
ValidationService.validate(
    mappings: SolutionMappingSet,
    extracted_rfp: ExtractedRFP,
    catalog_names: set[str]
) -> ValidationReport
```

**What it does (no LLM call):**
- **Grounding check**: Every REQ-xxx ID cited in `signal_assessments` must exist in `extracted_rfp.requirements`. Violations are recorded as `GroundingIssue` objects.
- **Coverage check**: Every play in the catalog must appear exactly once. Missing and unknown plays are recorded separately.
- Returns `ValidationReport(passed, issues, missing_catalog_plays, unknown_catalog_plays)`

---

### Orchestrator: LangGraph Workflow
**Location**: [app/services/graph_service.py](app/services/graph_service.py)

```python
RFPProcessGraph.process_rfp(rfp_text: str, rfp_id: str = None) -> RFPAnalysisResponse
```

**Workflow:**
```
RFP Text
   ↓
[extract node] → ExtractionService → ExtractedRFP
   ↓
[map node]     → MappingService    → SolutionMappingSet
   ↓
[validate node] → ValidationService → ValidationReport
   ↓
RFPAnalysisResponse
```

**State** (`RFPProcessState` TypedDict):
```python
{
    "rfp_text": str,
    "extracted_data": Optional[ExtractedRFP],
    "solution_mappings": Optional[SolutionMappingSet],
    "validation": Optional[ValidationReport],
}
```

---

## REST API

### Main Endpoint: `POST /api/v1/analyze-pdf`

**Request (multipart/form-data):**
- `file`: PDF file (required, max 10MB)
- `format`: `"text"` or `"markdown"` (optional)
- `rfp_id`: unique identifier (optional, auto-generated if omitted)

**Response:**
```json
{
  "extracted_data": {
    "rfp_id": "my-rfp-001",
    "company_info": { "name": "...", "issuer_type": "higher_education" },
    "administrative": { "rfp_title": "...", "submission_deadline": "..." },
    "workload": { "use_case": "...", "listed_equipment": [] },
    "power": { "total_kw": 35.0, "redundancy_level": "N+1" },
    "requirements": [
      {
        "id": "REQ-001",
        "theme": "power",
        "description": "...",
        "priority": "mandatory",
        "quantitative_value": "35 kW",
        "source": { "page": 4, "excerpt": "The facility shall provide..." }
      }
    ],
    "evaluation_criteria": [
      { "category": "Location", "weight_pct": 20.0 }
    ]
  },
  "solution_mappings": {
    "mappings": [
      {
        "solution_name": "Security & Resilience",
        "signal_assessments": [
          {
            "signal": "Customer requires compliance certifications...",
            "status": "MET",
            "requirement_ids": ["REQ-012", "REQ-013"]
          }
        ],
        "counter_evidence": null,
        "confidence": "HIGH",
        "score": 0.88,
        "rationale": "Two mandatory compliance requirements..."
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

### Health Check: `GET /api/v1/health`
```json
{ "status": "healthy" }
```

---

## Tech Stack

| Component | Purpose | Version |
|-----------|---------|---------|
| **LangGraph** | Three-node multi-agent orchestration | 1.2.0+ |
| **FastAPI** | REST API framework | ≥0.136.1 |
| **OpenAI** | GPT-5 via Responses API | ≥2.36.0 |
| **Pydantic v2** | Data validation with cross-field validators | ≥2.13.4 |
| **PyMuPDF** | PDF text extraction with page markers | ≥1.27.2 |
| **Uvicorn** | ASGI server | ≥0.46.0 |
| **Python** | Runtime | ≥3.13 |

---

## Data Models Summary

### Extraction Models (`rfp_extraction.py`)

| Model | Key Fields |
|-------|-----------|
| `Requirement` | `id` (REQ-NNN), `theme`, `priority`, `quantitative_value`, `source` |
| `SourceSpan` | `page`, `excerpt` (verbatim quote) |
| `ExtractedRFP` | `requirements[]`, domain sub-models, `evaluation_criteria`, `mandatory_requirements` |
| `PowerSpec` | `total_kw`, `kw_per_cabinet`, `redundancy_level`, `generator_backup` |
| `NetworkSpec` | `carrier_neutral_required`, `bgp_required`, `cloud_on_ramps_required[]` |
| `PhysicalSecuritySpec` | Boolean flags for guards, biometrics, CCTV, person traps, etc. |

### Mapping Models (`solution_mapping.py`)

| Model | Key Fields |
|-------|-----------|
| `SignalAssessment` | `signal`, `status` (MET/PARTIAL/NOT_MET), `requirement_ids[]` |
| `SolutionMapping` | `solution_name`, `signal_assessments[]`, `counter_evidence`, `confidence`, `score`, `rationale` |
| `SolutionMappingSet` | `mappings[]` — all 6 plays, unique names enforced |
| `ValidationReport` | `passed`, `issues[]`, `missing_catalog_plays[]`, `unknown_catalog_plays[]` |

---

## Key Features

- **Three-Agent Pipeline**: Extract → Map → Validate with clear data boundaries
- **Granular Requirement IDs**: Every RFP ask is a first-class REQ-NNN object; the mapper cites these IDs making every confidence score traceable
- **Signal-Level Mapping**: Per-signal MET/PARTIAL/NOT_MET assessments prevent vague "overall fit" judgements
- **Calibrated Confidence**: Rubric instructs the model to choose the lower tier when uncertain
- **Deterministic Validation**: Grounding and catalog coverage checks run without an LLM call — instant, zero additional cost
- **Source Provenance**: Every extracted field includes page number and verbatim excerpt
- **Pydantic v2 Invariants**: Score/confidence consistency and REQ-ID format enforced at construction time
- **OpenAI Responses API**: `responses.parse()` with `text_format` — no manual JSON parsing

---

## Files Reference

| File | Purpose |
|------|---------|
| `extraction_service.py` | RFP parsing & extraction (Agent 1) |
| `mapping_service.py` | Signal-based solution scoring (Agent 2) |
| `validation_service.py` | Grounding & coverage validation (Agent 3, no LLM) |
| `graph_service.py` | LangGraph three-node workflow |
| `pdf_service.py` | PDF validation and text extraction |
| `routes.py` | FastAPI endpoint handlers |
| `dependencies.py` | Dependency injection setup |
| `rfp_extraction.py` | Pydantic models for extracted RFP data |
| `solution_mapping.py` | Pydantic models for solution mappings and validation |
| `prompts.py` | LLM prompts & solution catalog helpers |
| `solutions.json` | Equinix catalog definitions (6 sales plays) |
| `main.py` | FastAPI app setup |
| `test_api.py` | API test suite |
| `check_setup.py` | Setup validation script |
