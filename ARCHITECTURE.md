# 🏗️ System Architecture

## High-Level Flow

```
┌─────────────────────────────────────────────────────────────┐
│                    CLIENT APPLICATIONS                      │
│  (Swagger UI, cURL, Python, Web Frontend, etc.)            │
└──────────────────┬──────────────────────────────────────────┘
                   │
                   │ POST /api/v1/analyze
                   │ { "rfp_text": "..." }
                   ▼
┌─────────────────────────────────────────────────────────────┐
│                    FastAPI Application                      │
│  (main.py - ASGI server on 0.0.0.0:8000)                   │
└──────────────────┬──────────────────────────────────────────┘
                   │
                   ▼
         ┌─────────────────────┐
         │  Route Handler      │
         │  /api/v1/analyze    │
         │  (routes.py)        │
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
         │  │ Extraction     │      │
         │  │ Node           │      │
         │  └────┬───────────┘      │
         │       │                  │
         │       ▼                  │
         │  ┌────────────────┐      │
         │  │ Mapping        │      │
         │  │ Node           │      │
         │  └────┬───────────┘      │
         │       │                  │
         │       ▼                  │
         │  END                     │
         │                          │
         └──────────┬───────────────┘
                    │
         ┌──────────┴──────────┐
         │                     │
         ▼                     ▼
    ┌─────────────┐    ┌──────────────┐
    │ Extraction  │    │    Mapping   │
    │ Service     │    │    Service   │
    │             │    │              │
    │ • Parse RFP │    │ • Match      │
    │ • Extract   │    │   solutions  │
    │   data      │    │ • Score      │
    │ • Validate  │    │   confidence │
    └──────┬──────┘    └──────┬───────┘
           │                   │
           │ Uses GPT-4        │ Uses GPT-4
           │                   │
           └────┬──────────┬───┘
                │          │
                ▼          ▼
        ┌─────────────────────────┐
        │    OpenAI API (GPT-4)    │
        │                         │
        │ • Extracts structured   │
        │   data from RFP         │
        │ • Maps to solutions     │
        │ • Generates scores      │
        └────────────┬────────────┘
                     │
                     ▼
        ┌─────────────────────────┐
        │  RFPAnalysisResponse    │
        │  JSON Response          │
        └────────────┬────────────┘
                     │
                     ▼
        ┌─────────────────────────┐
        │    Response to Client   │
        │  • Extracted data       │
        │  • Solution mappings    │
        │  • Confidence scores    │
        │  • Evidence             │
        └─────────────────────────┘
```

---

## Component Interaction Diagram

```
┌────────────────────────────────────────────────────────────────────┐
│  MODELS (Data Validation & Type Safety)                           │
│                                                                    │
│  CompanyInfo ─────────────┐                                       │
│                           ├─► ExtractedRFP ─────┐                │
│  TechnicalRequirements ───┤                     │                │
│                           ├─► SolutionMapping   ├─► RFPAnalysisResponse
│  SecurityRequirements ────┤                     │                │
│                           ├─► Confidence Scores │                │
│  OperationalConstraints ──┘                     │                │
│                                                 │                │
└────────────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────────────┐
│  SERVICES (Business Logic)                                         │
│                                                                    │
│  ExtractionService                                                │
│  • extract_rfp_info(text) → ExtractedRFP                         │
│  • Uses: GPT-4, EXTRACTION_PROMPT                                │
│                                                                    │
│  MappingService                                                   │
│  • map_to_solutions(data) → List[SolutionMapping]               │
│  • Uses: GPT-4, MAPPING_PROMPT, SOLUTION_DEFINITIONS            │
│                                                                    │
│  RFPProcessGraph (LangGraph)                                      │
│  • Orchestrates extraction_node and mapping_node                 │
│  • Manages state between nodes                                    │
│  • process_rfp() → RFPAnalysisResponse                           │
│                                                                    │
└────────────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────────────┐
│  API LAYER (REST Endpoints)                                       │
│                                                                    │
│  POST /api/v1/analyze                                             │
│  • Input: AnalyzeRequest (rfp_text, rfp_id)                      │
│  • Output: RFPAnalysisResponse                                    │
│  • Uses: RFPProcessGraph, OpenAI client                           │
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
│  • EXTRACTION_PROMPT - Instructions for Agent 1                  │
│  • MAPPING_PROMPT - Instructions for Agent 2                     │
│  • SOLUTION_DEFINITIONS - 6 solution descriptions                 │
│  • format_extracted_for_mapping() - Data formatting              │
│                                                                    │
│  dependencies.py                                                  │
│  • get_openai_client() - Singleton OpenAI client                 │
│                                                                    │
└────────────────────────────────────────────────────────────────────┘
```

---

## Data Flow Through Agents

```
                    INPUT: RFP Text
                          │
                          ▼
            ┌──────────────────────────┐
            │  AGENT 1: Extraction     │
            │  Service                 │
            │                          │
            │  Prompt: "Extract from   │
            │  RFP: company profile,   │
            │  tech requirements,      │
            │  security needs,         │
            │  operational constraints"│
            │                          │
            │  LLM: GPT-4             │
            │  Temp: 0.3 (precise)    │
            └──────────┬───────────────┘
                       │
                       ▼
            ┌──────────────────────────┐
            │  ExtractedRFP Object     │
            │  • company_info          │
            │  • tech_requirements     │
            │  • security_requirements │
            │  • operational_constraints
            │  • raw_summary           │
            └──────────┬───────────────┘
                       │
                       ▼
            ┌──────────────────────────┐
            │  AGENT 2: Mapping        │
            │  Service                 │
            │                          │
            │  Prompt: "Match          │
            │  requirements to:        │
            │  - Hybrid Multicloud     │
            │  - Digital Expansion     │
            │  - Interconnection       │
            │  - Edge                  │
            │  - Security              │
            │  - AI/HPC                │
            │                          │
            │  LLM: GPT-4             │
            │  Temp: 0.2 (analytical) │
            └──────────┬───────────────┘
                       │
                       ▼
            ┌──────────────────────────┐
            │  List[SolutionMapping]   │
            │  • solution_name         │
            │  • confidence_score      │
            │  • supporting_evidence   │
            │  • key_features_aligned  │
            │  (sorted by confidence)  │
            └──────────┬───────────────┘
                       │
                       ▼
                OUTPUT: RFPAnalysisResponse
                • extracted_data
                • solution_mappings
                • analysis_timestamp
```

---

## Request/Response Example

```
REQUEST
───────
POST /api/v1/analyze
Content-Type: application/json

{
  "rfp_text": "ACME Corp - Enterprise RFP. Needs: 1000+ CPU cores, 500TB storage, 
  10Gbps network, SOC2/HIPAA compliance, 99.99% uptime, multi-region failover, 
  GPU support for AI workloads. Budget: $5M/year. Timeline: 6 months.",
  "rfp_id": "acme-2026-001"
}


RESPONSE
────────
HTTP/1.1 200 OK
Content-Type: application/json

{
  "rfp_id": "acme-2026-001",
  "extracted_data": {
    "company_info": {
      "name": "ACME Corp",
      "industry": "Enterprise",
      "size": "Enterprise",
      "headquarters": null
    },
    "technical_requirements": {
      "compute_needs": "1000+ CPU cores, GPU support",
      "storage_capacity": "500TB storage",
      "networking": "10Gbps network",
      "performance_sla": "99.99% uptime",
      "specific_workloads": ["AI workloads"]
    },
    "security_requirements": {
      "compliance_standards": ["SOC2", "HIPAA"],
      "data_residency": null,
      "encryption_needs": null,
      "threat_model": null,
      "zero_trust": null
    },
    "operational_constraints": {
      "budget_range": "$5M/year",
      "timeline": "6 months",
      "sla_uptime": "99.99%",
      "geographic_regions": ["multi-region"],
      "disaster_recovery": "Multi-region failover"
    },
    "raw_summary": "ACME Corp enterprise infrastructure..."
  },
  "solution_mappings": [
    {
      "solution_name": "Security & Resilience",
      "confidence_score": 0.94,
      "supporting_evidence": "SOC2/HIPAA compliance and 99.99% uptime requirements",
      "key_features_aligned": ["High availability and redundancy", "Improved compliance posture"]
    },
    {
      "solution_name": "AI / High-Performance Compute",
      "confidence_score": 0.91,
      "supporting_evidence": "GPU support and high CPU core requirements for AI workloads",
      "key_features_aligned": ["GPU-ready infrastructure", "High power and cooling capacity"]
    },
    {
      "solution_name": "Digital Infrastructure Expansion",
      "confidence_score": 0.78,
      "supporting_evidence": "Multi-region deployment and high resource needs",
      "key_features_aligned": ["Global IBX data center footprint", "Scalable infrastructure deployment"]
    }
  ],
  "analysis_timestamp": "2026-05-13T22:30:45.123456"
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
    │        │ │        │ │        │
    │FastAPI│ │FastAPI│ │FastAPI│
    │Server │ │Server │ │Server │
    └───┬────┘ └───┬────┘ └───┬────┘
        │          │          │
        └──────────┼──────────┘
                   │
        ┌──────────▼──────────┐
        │   OpenAI API (GPT-4)│
        │   (External Service)│
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
                    Request
                      │
                      ▼
            ┌──────────────────┐
            │ Input Validation │
            │ (Pydantic)       │
            └──────┬───────────┘
                   │
        ┌──────────┴──────────┐
        │ Valid?              │
        │                     │
    YES │                  NO │
        ▼                     ▼
    Continue            400 Bad Request
                        • Invalid input
                        • Missing field
                        • Wrong type

                      │
                      ▼
            ┌──────────────────┐
            │ Extract & Map    │
            │ (Agents)         │
            └──────┬───────────┘
                   │
        ┌──────────┴──────────┐
        │ Success?            │
        │                     │
    YES │                  NO │
        ▼                     ▼
    200 OK              500 Internal Error
    + Response          • LLM API error
                        • JSON parse error
                        • Timeout
                        • Missing API key

                      │
                      ▼
                Response
```

---

## Technologies Used

```
┌─────────────────────────────────────────────────┐
│  LangGraph                                      │
│  • StateGraph for workflow definition            │
│  • Nodes for discrete operations                 │
│  • Sequential execution with state passing       │
└─────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────┐
│  FastAPI                                        │
│  • Async request handling                       │
│  • Dependency injection                         │
│  • Auto OpenAPI/Swagger documentation           │
│  • CORS middleware                              │
└─────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────┐
│  OpenAI GPT-4                                   │
│  • Extraction Agent: Parse & structure RFPs     │
│  • Mapping Agent: Semantic matching             │
│  • Confidence scoring                           │
└─────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────┐
│  Pydantic                                       │
│  • Type validation                              │
│  • JSON serialization                           │
│  • Auto documentation                           │
└─────────────────────────────────────────────────┘
```

---

This architecture enables:
- ✅ Scalable multi-agent processing
- ✅ Clear separation of concerns
- ✅ Type-safe end-to-end data flow
- ✅ Easy testing and debugging
- ✅ Production-ready error handling
- ✅ Future extensibility
