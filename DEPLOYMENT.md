# RFP Multi-Agent Analysis System - Setup & Deployment Guide

## ✅ System Built Successfully

Your multi-agent RFP analysis system is now complete and ready to deploy. The system consists of:

### Components Overview

#### 1. **Extraction Agent** (`app/services/extraction_service.py`)
- Parses RFP documents using GPT-4
- Extracts structured data including:
  - Company information
  - Technical requirements
  - Security/compliance requirements
  - Operational constraints
- Returns validated Pydantic models

#### 2. **Solution Mapper Agent** (`app/services/mapping_service.py`)
- Takes extracted requirements
- Matches against 6 Equinix solutions:
  - Hybrid Multicloud Enablement
  - Digital Infrastructure Expansion
  - Interconnection & Ecosystem
  - Edge & Low-Latency Deployment
  - Security & Resilience
  - AI / High-Performance Compute
- Returns solutions with confidence scores (0.0-1.0)
- Filters to only include matches >0.5 confidence

#### 3. **LangGraph Orchestration** (`app/services/graph_service.py`)
- Connects both agents in a sequential workflow
- State management between nodes
- Processes RFP text end-to-end

#### 4. **FastAPI REST API** (`app/api/routes.py`)
- `POST /api/v1/analyze` - Main analysis endpoint
- `GET /api/v1/health` - Health check
- Built-in Swagger UI at `/docs`
- Full request/response validation

### Project Structure
```
Equinix_DSCodeAlong/
├── app/
│   ├── models/
│   │   ├── rfp_extraction.py       # Extraction data models
│   │   └── solution_mapping.py     # Solution mapping models
│   ├── services/
│   │   ├── extraction_service.py   # Agent 1: RFP extraction
│   │   ├── mapping_service.py      # Agent 2: Solution mapping
│   │   └── graph_service.py        # LangGraph workflow
│   ├── api/
│   │   ├── routes.py               # FastAPI endpoints
│   │   └── dependencies.py         # Dependency injection
│   └── utils/
│       └── prompts.py              # LLM prompts & definitions
├── main.py                         # FastAPI app entry point
├── test_api.py                     # Test suite
├── pyproject.toml                  # Dependencies
├── uv.lock                         # Locked versions
└── README.md                       # Full documentation
```

## 🚀 Quick Start

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

### Step 2: Start the API Server

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

### Step 3: Test the API

**Option A: Using Swagger UI (Browser)**
1. Open http://localhost:8000/docs
2. Click "Try it out" on the `/api/v1/analyze` endpoint
3. Paste an RFP document into the `rfp_text` field
4. Click "Execute"

**Option B: Using curl**
```bash
curl -X POST http://localhost:8000/api/v1/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "rfp_text": "ACME Corp needs secure, high-performance infrastructure with 99.99% uptime, multi-region support, GPU workloads, and compliance with SOC2, HIPAA, and FedRAMP. Budget: $5M/year. Timeline: 6 months.",
    "rfp_id": "acme-2026-001"
  }'
```

**Option C: Using Python**
```bash
uv run python test_api.py
```

## 📊 Expected Output

The API returns a complete analysis:

```json
{
  "rfp_id": "acme-2026-001",
  "extracted_data": {
    "company_info": {
      "name": "ACME Corp",
      "industry": "Technology",
      "size": "Enterprise"
    },
    "technical_requirements": {
      "compute_needs": "High-performance GPU infrastructure",
      "storage_capacity": "100TB+",
      "networking": "Multi-region connectivity",
      "specific_workloads": ["AI training", "ML inference"]
    },
    "security_requirements": {
      "compliance_standards": ["SOC2", "HIPAA", "FedRAMP"],
      "zero_trust": true
    },
    "operational_constraints": {
      "timeline": "6 months",
      "sla_uptime": "99.99%"
    }
  },
  "solution_mappings": [
    {
      "solution_name": "Security & Resilience",
      "confidence_score": 0.95,
      "supporting_evidence": "Multiple compliance requirements and zero-trust mentioned",
      "key_features_aligned": ["Reduced attack surface", "Zero-trust support", "High availability"]
    },
    {
      "solution_name": "AI / High-Performance Compute",
      "confidence_score": 0.92,
      "supporting_evidence": "GPU infrastructure and AI workloads explicitly stated",
      "key_features_aligned": ["GPU-ready infrastructure", "High power capacity"]
    }
  ],
  "analysis_timestamp": "2026-05-13T12:34:56.789Z"
}
```

## 🔧 Key Features

### Multi-Agent Architecture
- ✅ Sequential workflow with state passing
- ✅ Independent agents can be scaled/updated independently
- ✅ LangGraph provides clear orchestration

### Data Validation
- ✅ Full Pydantic model validation
- ✅ Type-safe throughout the pipeline
- ✅ Clear error messages for invalid input

### Production Ready
- ✅ Error handling and exceptions
- ✅ Dependency injection pattern
- ✅ CORS enabled for cross-origin requests
- ✅ Health check endpoint
- ✅ Swagger/OpenAPI documentation

### Flexible Solution Matching
- ✅ Multiple solutions per RFP
- ✅ Confidence scoring
- ✅ Evidence extraction from RFP
- ✅ Configurable confidence threshold

## 📝 Customization

### Adjust Confidence Threshold
Edit `app/services/mapping_service.py`:
```python
self.min_confidence = 0.6  # Default is 0.5
```

### Change LLM Model
Edit `app/services/extraction_service.py` and `app/services/mapping_service.py`:
```python
model="gpt-3.5-turbo"  # For cost optimization
model="gpt-4-turbo"     # For better performance
```

### Modify Solution Definitions
Edit `app/utils/prompts.py` - `SOLUTION_DEFINITIONS` dict

## 🔄 Batch Processing Example

```python
import json
from app.services.graph_service import RFPProcessGraph

# Initialize graph
graph = RFPProcessGraph()

# Process multiple RFPs
rfp_files = ["rfp1.txt", "rfp2.txt", "rfp3.txt"]
results = []

for rfp_file in rfp_files:
    with open(rfp_file, 'r') as f:
        rfp_text = f.read()
    
    analysis = graph.process_rfp(rfp_text, rfp_id=rfp_file)
    results.append(analysis.model_dump())

# Save results
with open('analysis_results.json', 'w') as f:
    json.dump(results, f, indent=2, default=str)
```

## 🚨 Troubleshooting

### "ModuleNotFoundError: No module named 'app'"
Make sure you're running from the project root directory and using `uv run`

### "Missing credentials. Please pass an `api_key`..."
Set the OPENAI_API_KEY environment variable before starting the server

### "Failed with status 500: Internal Server Error"
Check the server logs for the actual error. Common causes:
- Missing OpenAI API key
- Insufficient RFP text (minimum 100 characters)
- OpenAI rate limiting

### "Connection refused"
Make sure the server is running: `uv run python -m uvicorn main:app --host 0.0.0.0 --port 8000`

## 📚 Next Steps

1. **Add Authentication**: Implement API key validation
2. **Add Database**: Store analysis results in PostgreSQL/MongoDB
3. **Batch Processing**: Add `/api/v1/analyze-batch` endpoint
4. **Webhooks**: Send results to external systems
5. **Caching**: Cache solution definitions and RFP analysis
6. **Monitoring**: Add logging and metrics collection
7. **Rate Limiting**: Prevent API abuse

## 📖 Additional Resources

- **LangGraph Docs**: https://langchain-ai.github.io/langgraph/
- **FastAPI Docs**: https://fastapi.tiangolo.com/
- **OpenAI API Docs**: https://platform.openai.com/docs/api-reference
- **Pydantic Docs**: https://docs.pydantic.dev/

---

**Created**: 2026-05-13  
**Status**: Production Ready  
**Version**: 1.0.0
