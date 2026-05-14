# Quick Reference

## Start Here

```bash
# 1. Set API key
export OPENAI_API_KEY="sk-your-key-here"        # Linux/Mac
$env:OPENAI_API_KEY="sk-your-key-here"          # Windows PowerShell

# 2. Install dependencies (one-time)
uv sync

# 3. Start server
uv run python -m uvicorn main:app --reload

# 4. Test (in another terminal)
uv run python test_api.py
```

## API Endpoints

| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST | `/api/v1/analyze-pdf` | Upload a PDF RFP and get structured extraction + solution mappings |
| GET | `/api/v1/health` | Health check |
| GET | `/docs` | Interactive API documentation (Swagger) |
| GET | `/redoc` | Alternative API documentation |

## Example: Python Upload

```python
import requests

with open("rfp.pdf", "rb") as f:
    response = requests.post(
        "http://localhost:8000/api/v1/analyze-pdf",
        files={"file": f},
        data={"format": "markdown", "rfp_id": "my-rfp-001"}
    )
print(response.json())
```

## Solution Categories

1. **Hybrid Multicloud Enablement** — Private connectivity to hyperscale cloud providers
2. **Digital Infrastructure Expansion** — Global scaling and high-density workloads
3. **Interconnection & Ecosystem** — Partner connectivity and network effects
4. **Edge & Low-Latency Deployment** — Real-time applications at the edge
5. **Security & Resilience** — Secure, compliant, disaster-resistant infrastructure
6. **AI / High-Performance Compute** — GPU-ready AI/ML infrastructure

## File Structure

```
app/
  ├── models/
  │   ├── rfp_extraction.py      # Enums, sub-models, ExtractedRFP
  │   └── solution_mapping.py    # SignalAssessment, SolutionMappingSet, ValidationReport
  ├── services/
  │   ├── extraction_service.py  # Agent 1: extraction (Responses API)
  │   ├── mapping_service.py     # Agent 2: signal-based mapping (Responses API)
  │   ├── validation_service.py  # Agent 3: grounding + coverage (no LLM)
  │   ├── pdf_service.py         # PDF validation & text extraction
  │   └── graph_service.py       # LangGraph orchestration (extract→map→validate)
  ├── api/
  │   ├── routes.py              # FastAPI endpoints
  │   └── dependencies.py        # OpenAI client injection
  └── utils/
      └── prompts.py             # LLM prompts & catalog formatting
main.py               # FastAPI app
solutions.json        # Equinix catalog (6 sales plays)
test_api.py           # Test suite
check_setup.py        # Setup validator
```

## Configuration

**Change LLM model** — set `OPENAI_MODEL` in `.env` or as an environment variable:
```bash
OPENAI_MODEL=gpt-5.2-chat-latest   # Default — best reasoning, large context
OPENAI_MODEL=gpt-4o                 # Faster, lower cost
```

**Change solutions catalog**: Edit `solutions.json` — the mapper reads from it at startup.
Override path via env var: `SOLUTIONS_JSON_PATH=/path/to/my-catalog.json`

## Debugging

**Check if server is running:**
```bash
curl http://localhost:8000/api/v1/health
```

**View API documentation:**
```
http://localhost:8000/docs
```

**Check dependencies:**
```bash
uv run python check_setup.py
```

**Validation warnings in response:**
If `validation.passed` is `false`, check:
- `validation.issues` — mapper cited a REQ ID that doesn't exist in the extraction
- `validation.missing_catalog_plays` — a catalog play was not scored
- `validation.unknown_catalog_plays` — mapper invented a play name not in the catalog

## Common Errors

| Error | Solution |
|-------|----------|
| `ModuleNotFoundError: langgraph` | Use `uv run` command, not bare `python` |
| `Missing credentials` | Set `OPENAI_API_KEY` environment variable |
| `Connection refused` | Start server: `uv run python -m uvicorn main:app --reload` |
| `Internal Server Error (500)` | Check server logs for actual error |
| `File must be a PDF` | Only PDF files are accepted by `/api/v1/analyze-pdf` |
| `File exceeds 10MB limit` | Use a smaller PDF or pre-extract text |

## Environment Variables

```bash
OPENAI_API_KEY          # Required: your OpenAI API key
OPENAI_MODEL            # Optional: LLM model name (default: gpt-5.2-chat-latest)
SOLUTIONS_JSON_PATH     # Optional: path to solutions catalog JSON (default: solutions.json)
```

## Performance Tips

- Batch RFPs during off-peak hours
- Cache solution definitions (already loaded once at startup via `MappingService.__init__`)
- Consider async task queue (Celery, RQ) for high-volume production use
- The validation node is deterministic and adds negligible latency

## Need Help?

1. Check `README.md` for full API documentation and design decisions
2. Check `ARCHITECTURE.md` for system diagrams and data flow
3. Check `DEPLOYMENT.md` for setup and customization guide
4. View Swagger UI at `http://localhost:8000/docs`

---
