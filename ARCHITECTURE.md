# System Architecture

## High-Level Flow

```
┌─────────────────────────────────────────────────────────────┐
│                    CLIENT APPLICATIONS                      │
│  (Swagger UI, cURL, Python, Web Frontend, etc.)            │
└──────────────────┬──────────────────────────────────────────┘
                   │
                   │ POST /api/v1/analyze-pdf
                   │ multipart/form-data (PDF file)
                   ▼
┌─────────────────────────────────────────────────────────────┐
│                    FastAPI Application                      │
│  (main.py - ASGI server on 0.0.0.0:8000)                   │
└──────────────────┬──────────────────────────────────────────┘
                   │
                   ▼
         ┌─────────────────────┐
         │  PDF Service        │
         │  (pdf_service.py)   │
         │  Validate + Extract │
         │  text with [Page N] │
         │  markers            │
         └──────────┬──────────┘
                    │
                    ▼
         ┌──────────────────────────┐
         │  LangGraph Workflow      │
         │  (graph_service.py)      │
         │                          │
         │  START                   │
         │    ▼                     │
         │  ┌────────────────┐      │
         │  │ extract node   │      │
         │  └────┬───────────┘      │
         │       │                  │
         │       ▼                  │
         │  ┌────────────────┐      │
         │  │ map node       │      │
         │  └────┬───────────┘      │
         │       │                  │
         │       ▼                  │
         │  ┌────────────────┐      │
         │  │ validate node  │      │
         │  └────┬───────────┘      │
         │       │                  │
         │  END                     │
         │                          │
         └──────────┬───────────────┘
                    │
         ┌──────────┼──────────────────┐
         │          │                  │
         ▼          ▼                  ▼
    ┌─────────┐ ┌─────────┐  ┌──────────────────┐
    │Extraction│ │Mapping  │  │Validation Service│
    │Service  │ │Service  │  │(no LLM)          │
    │         │ │         │  │                  │
    │• Parse  │ │• Score  │  │• Grounding check │
    │  RFP    │ │  each   │  │• Catalog coverage│
    │• Build  │ │  play   │  │• Returns         │
    │  REQ IDs│ │• Signal │  │  ValidationReport│
    └──────┬──┘ │  assess.│  └──────────────────┘
           │    └──────┬──┘
           │ Uses GPT-5│ Uses GPT-5
           └────┬──────┘
                │
                ▼
        ┌─────────────────────────┐
        │  OpenAI Responses API   │
        │  (responses.parse)      │
        │                         │
        │ • Structured output via │
        │   text_format=<Model>   │
        │ • No manual JSON parse  │
        └────────────┬────────────┘
                     │
                     ▼
        ┌─────────────────────────┐
        │  RFPAnalysisResponse    │
        │  • extracted_data       │
        │  • solution_mappings    │
        │  • validation           │
        │  • analysis_timestamp   │
        └─────────────────────────┘
```

---

## Component Interaction Diagram

```
┌────────────────────────────────────────────────────────────────────┐
│  MODELS (Data Validation & Type Safety)                           │
│                                                                    │
│  Enums: Priority, RequirementTheme, RedundancyLevel, IssuerType   │
│                                                                    │
│  Extraction models:                                               │
│  SourceSpan ──────────────────────────────────────────────────┐  │
│  Requirement (REQ-001…) ──────────────────────────────────┐   │  │
│  PowerSpec, CoolingSpec, NetworkSpec ─────────────────┐   │   │  │
│  PhysicalSecuritySpec, ResiliencySpec, OperationsSpec ┤   │   │  │
│  WorkloadProfile, GeographicConstraint ───────────────┤   ├───┤  │
│  AdministrativeDetails, CompanyInfo ──────────────────┤   │   │  │
│  EvaluationCriterion, MandatoryItem ──────────────────┘   │   │  │
│                                                            ▼   ▼  │
│                                                     ExtractedRFP  │
│                                                            │      │
│  Mapping models:                                           │      │
│  Confidence (HIGH/MEDIUM/LOW/NONE) ────────────────┐      │      │
│  SignalStatus (MET/PARTIAL/NOT_MET) ───────────────┤      │      │
│  SignalAssessment (cites REQ IDs) ─────────────────┤      │      │
│  SolutionMapping ──────────────────────────────────┤      │      │
│  SolutionMappingSet ───────────────────────────────┘      │      │
│                                                            │      │
│  Validation models:                                        │      │
│  GroundingIssue, ValidationReport ─────────────────────┐  │      │
│                                                         │  │      │
│                                              RFPAnalysisResponse  │
└────────────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────────────┐
│  SERVICES (Business Logic)                                         │
│                                                                    │
│  ExtractionService                                                │
│  • extract_rfp_info(text) → ExtractedRFP                         │
│  • Uses: EXTRACTION_SYSTEM_PROMPT + EXTRACTION_USER_PROMPT       │
│  • API: client.responses.parse(text_format=ExtractedRFP)         │
│                                                                    │
│  MappingService                                                   │
│  • map_to_solutions(extracted_rfp) → SolutionMappingSet         │
│  • Uses: MAPPING_SYSTEM_PROMPT + MAPPING_USER_PROMPT             │
│  • API: client.responses.parse(text_format=SolutionMappingSet)   │
│  • Exposes: catalog_names (set of valid play names)              │
│                                                                    │
│  ValidationService  (deterministic, no LLM)                      │
│  • validate(mappings, extracted_rfp, catalog_names)              │
│    → ValidationReport                                            │
│  • Grounding: every cited REQ-xxx must exist in extraction       │
│  • Coverage: every catalog play scored exactly once              │
│                                                                    │
│  RFPProcessGraph (LangGraph)                                      │
│  • Nodes: extract → map → validate                               │
│  • State: RFPProcessState (TypedDict)                            │
│  • process_rfp(text, rfp_id) → RFPAnalysisResponse              │
│                                                                    │
└────────────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────────────┐
│  API LAYER (REST Endpoints)                                       │
│                                                                    │
│  POST /api/v1/analyze-pdf                                         │
│  • Input: PDF file (multipart), format, rfp_id                   │
│  • Output: RFPAnalysisResponse                                    │
│  • Uses: PDFService, RFPProcessGraph, OpenAI client              │
│                                                                    │
│  GET /api/v1/health                                               │
│  • Output: { "status": "healthy" }                                │
│                                                                    │
│  GET /docs, /redoc                                                │
│  • Auto-generated OpenAPI documentation                          │
│                                                                    │
└────────────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────────────┐
│  UTILITIES & CONFIG                                               │
│                                                                    │
│  prompts.py                                                        │
│  • EXTRACTION_SYSTEM_PROMPT — detailed extraction instructions   │
│  • EXTRACTION_USER_PROMPT — user-turn template                   │
│  • MAPPING_SYSTEM_PROMPT — signal rubric + catalog injection     │
│  • MAPPING_USER_PROMPT — extracted JSON injection               │
│  • format_extracted_for_mapping() — dumps ExtractedRFP as JSON  │
│  • load_solution_definitions() — reads solutions.json            │
│  • format_solutions_for_prompt() — formats catalog for prompt   │
│                                                                    │
│  solutions.json                                                   │
│  • 6 Equinix sales plays with descriptions and key features      │
│  • Path configurable via SOLUTIONS_JSON_PATH env var             │
│                                                                    │
│  dependencies.py                                                  │
│  • get_openai_client() — singleton OpenAI client                 │
│  • get_openai_model() — model name from OPENAI_MODEL env var     │
│                                                                    │
└────────────────────────────────────────────────────────────────────┘
```

---

## Data Flow Through Agents

```
                    INPUT: PDF → Extracted Text (with [Page N] markers)
                          │
                          ▼
            ┌──────────────────────────┐
            │  AGENT 1: Extraction     │
            │  (ExtractionService)     │
            │                          │
            │  System prompt instructs │
            │  precise extraction:     │
            │  • One ask per REQ ID    │
            │  • Verbatim source spans │
            │  • No inference/guessing │
            │  • Typed domain models   │
            │                          │
            │  API: responses.parse    │
            │  Model: via OPENAI_MODEL │
            │         env var          │
            └──────────┬───────────────┘
                       │
                       ▼
            ┌──────────────────────────┐
            │  ExtractedRFP            │
            │  • company_info          │
            │  • administrative        │
            │  • workload              │
            │  • power / cooling /     │
            │    network / security /  │
            │    resiliency / ops      │
            │  • requirements[]        │
            │    REQ-001 … REQ-N       │
            │  • mandatory_requirements│
            │  • evaluation_criteria   │
            │  • notable_unique_reqs   │
            └──────────┬───────────────┘
                       │ (serialized to JSON)
                       ▼
            ┌──────────────────────────┐
            │  AGENT 2: Mapping        │
            │  (MappingService)        │
            │                          │
            │  Scores all 6 plays:     │
            │  For each signal:        │
            │  • MET / PARTIAL /       │
            │    NOT_MET              │
            │  • cite REQ IDs          │
            │  Then assigns:           │
            │  • confidence label      │
            │  • numeric score         │
            │  • counter-evidence      │
            │  • 2–3 sentence rationale│
            │                          │
            │  API: responses.parse    │
            └──────────┬───────────────┘
                       │
                       ▼
            ┌──────────────────────────┐
            │  SolutionMappingSet      │
            │  6 × SolutionMapping     │
            │  • solution_name         │
            │  • signal_assessments[]  │
            │  • counter_evidence      │
            │  • confidence (enum)     │
            │  • score (float 0–1)     │
            │  • rationale             │
            └──────────┬───────────────┘
                       │
                       ▼
            ┌──────────────────────────┐
            │  AGENT 3: Validation     │
            │  (ValidationService)     │
            │  — No LLM call —         │
            │                          │
            │  Grounding check:        │
            │  • Every cited REQ-xxx   │
            │    exists in extraction  │
            │                          │
            │  Coverage check:         │
            │  • Every catalog play    │
            │    scored exactly once   │
            │  • No invented plays     │
            └──────────┬───────────────┘
                       │
                       ▼
                OUTPUT: RFPAnalysisResponse
                • extracted_data
                • solution_mappings (SolutionMappingSet)
                • validation (ValidationReport)
                • analysis_timestamp (UTC)
```

---

## Request/Response Shape

```
REQUEST
───────
POST /api/v1/analyze-pdf
Content-Type: multipart/form-data

file=<rfp.pdf>
format=markdown          (optional)
rfp_id=ccac-2026-001    (optional)


RESPONSE
────────
HTTP/1.1 200 OK
Content-Type: application/json

{
  "extracted_data": {
    "rfp_id": "ccac-2026-001",
    "company_info": { "name": "CCAC", "issuer_type": "higher_education" },
    "administrative": {
      "rfp_title": "...",
      "submission_deadline": "2026-06-15",
      "contract_term": "5 years"
    },
    "workload": {
      "use_case": "production migration",
      "listed_equipment": ["VMware hosts", "Palo Alto firewalls"],
      "high_density_indicated": false
    },
    "power": { "total_kw": 35.0, "redundancy_level": "N+1" },
    "network": { "carrier_neutral_required": true, "bgp_required": true },
    "requirements": [
      {
        "id": "REQ-001",
        "theme": "power",
        "description": "Facility must supply 35 kW of conditioned power",
        "priority": "mandatory",
        "quantitative_value": "35 kW",
        "source": { "page": 4, "excerpt": "The colocation facility shall provide a minimum of 35 kW..." }
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
        "rationale": "Two mandatory compliance requirements (SOC 2 Type II, NDAA) are directly evidenced..."
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

---

## Deployment Architecture

```
┌──────────────────────────────────────────────────┐
│              Load Balancer / Reverse Proxy        │
│              (Nginx, HAProxy, etc.)               │
└───────────────────┬────────────────────────────────┘
                    │
        ┌───────────┼───────────┐
        │           │           │
        ▼           ▼           ▼
    ┌────────┐ ┌────────┐ ┌────────┐
    │Instance│ │Instance│ │Instance│
    │  1     │ │  2     │ │  3     │
    │FastAPI │ │FastAPI │ │FastAPI │
    │Server  │ │Server  │ │Server  │
    └───┬────┘ └───┬────┘ └───┬────┘
        │          │          │
        └──────────┼──────────┘
                   │
        ┌──────────▼──────────┐
        │  OpenAI API (GPT-5) │
        │  Responses API      │
        │  (External Service) │
        └─────────────────────┘

Optional Enhancements:
├── Redis Cache (solution definitions, results)
├── PostgreSQL/MongoDB (result storage, analytics)
├── Celery + RabbitMQ (async task processing)
├── Prometheus/Grafana (monitoring)
├── ELK Stack (logging)
└── Docker Compose (containerization)
```

---

## Error Handling Flow

```
                    Request (PDF upload)
                          │
                          ▼
            ┌──────────────────────┐
            │  PDF Validation      │
            │  (PDFService)        │
            └──────┬───────────────┘
                   │
        ┌──────────┴──────────┐
        │ Valid?              │
        │                     │
    YES │                  NO │
        ▼                     ▼
    Continue            400 Bad Request
                        • Not a PDF
                        • Exceeds 10MB
                        • Corrupted file

                      │
                      ▼
            ┌──────────────────────┐
            │ Extract + Map        │
            │ (Agents 1 & 2)       │
            └──────┬───────────────┘
                   │
        ┌──────────┴──────────┐
        │ Success?            │
        │                     │
    YES │                  NO │
        ▼                     ▼
   Continue            500 Internal Error
                        • LLM API error
                        • Pydantic parse error
                        • Timeout
                        • Missing API key

                      │
                      ▼
            ┌──────────────────────┐
            │ Validate             │
            │ (ValidationService)  │
            └──────┬───────────────┘
                   │
                   │ Always returns
                   │ (passed or not)
                   ▼
            ┌──────────────────────┐
            │ 200 OK               │
            │ RFPAnalysisResponse  │
            │ validation.passed    │
            │ may be false         │
            └──────────────────────┘
```

---

## Technologies Used

```
┌─────────────────────────────────────────────────┐
│  LangGraph                                      │
│  • StateGraph with TypedDict state              │
│  • Three sequential nodes: extract→map→validate │
│  • State passing between nodes                  │
└─────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────┐
│  FastAPI                                        │
│  • Async request handling                       │
│  • Dependency injection (OpenAI client)         │
│  • Auto OpenAPI/Swagger documentation           │
│  • CORS middleware                              │
└─────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────┐
│  OpenAI Responses API (GPT-5)                   │
│  • responses.parse() — structured output        │
│  • text_format=<PydanticModel>                  │
│  • Separate system/user prompts via             │
│    instructions + input parameters              │
└─────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────┐
│  Pydantic v2                                    │
│  • Type validation with @field_validator        │
│  • Cross-field invariants via @model_validator  │
│  • Score/confidence consistency enforced        │
│  • REQ-ID format enforced                       │
└─────────────────────────────────────────────────┘
```

---

This architecture enables:
- Scalable multi-agent processing
- Clear separation of concerns
- Type-safe, traceable end-to-end data flow
- Deterministic post-LLM validation without additional LLM cost
- Production-ready error handling
- Future extensibility
