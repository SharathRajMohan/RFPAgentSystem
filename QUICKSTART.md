# 🚀 Quick Reference

## Start Here

```bash
# 1. Set API key
export OPENAI_API_KEY="sk-your-key-here"

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
| POST | `/api/v1/analyze-pdf` | Analyze RFP PDFs and get solution mappings |
| GET | `/api/v1/health` | Health check |
| GET | `/docs` | Interactive API documentation (Swagger) |
| GET | `/redoc` | Alternative API documentation |

## Example: curl Request


## Solution Categories

1. **Hybrid Multicloud Enablement** - Multi-cloud connectivity and optimization
2. **Digital Infrastructure Expansion** - Global scaling and high-density workloads
3. **Interconnection & Ecosystem** - Partner connectivity and network effects
4. **Edge & Low-Latency** - Real-time applications at the edge
5. **Security & Resilience** - Secure, compliant, disaster-resistant infrastructure
6. **AI / High-Performance Compute** - GPU-ready AI/ML infrastructure

## File Structure

```
app/
  ├── models/           # Data models (rfp_extraction.py, solution_mapping.py)
  ├── services/         # Business logic (extraction_service.py, mapping_service.py, graph_service.py)
  ├── api/             # REST API (routes.py, dependencies.py)
  └── utils/           # Utilities (prompts.py)
main.py               # FastAPI app
test_api.py          # Test suite
check_setup.py       # Setup validator
```

## Configuration


**Change LLM model**:
```python
# In extraction_service.py and mapping_service.py search and replace the following
model="gpt-3.5-turbo"  # Cost: cheaper, speed: fast, quality: good
model="gpt-4"          # Cost: expensive, speed: slow, quality: best
model="gpt-4-turbo"    # Cost: moderate, speed: medium, quality: excellent
```

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

**View server logs:**
```
Watch the terminal where you started the server
```

## Common Errors

| Error | Solution |
|-------|----------|
| `ModuleNotFoundError: langgraph` | Use `uv run` command, not bare `python` |
| `Missing credentials` | Set `OPENAI_API_KEY` environment variable |
| `Connection refused` | Start server: `uv run python -m uvicorn main:app --reload` |
| `Internal Server Error (500)` | Check server logs for actual error |
| `Minimum 100 characters` | RFP text must be at least 100 characters long |

## Environment Variables

```bash
OPENAI_API_KEY          # Required: Your OpenAI API key (sk-...)
```

## Performance Tips

- Batch RFPs in non-critical times (off-peak hours)
- Use GPT-3.5-Turbo for faster analysis of simple RFPs
- Cache solution definitions to reduce API calls
- Consider async task queue for high volume

## Need Help?

1. Check `README.md` for full API documentation
2. Check `DEPLOYMENT.md` for setup and customization
3. View Swagger UI at `http://localhost:8000/docs`
4. Review `SYSTEM_SUMMARY.md` for architecture overview
5. Check `app/utils/prompts.py` for solution definitions

---
