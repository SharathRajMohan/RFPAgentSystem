from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from pydantic import BaseModel, Field
from app.services.graph_service import RFPProcessGraph
from app.services.pdf_service import PDFService, PDFValidationError
from app.models.solution_mapping import RFPAnalysisResponse
from app.api.dependencies import get_openai_client
from openai import OpenAI
import uuid
from loguru import logger


router = APIRouter(prefix="/api/v1", tags=["RFP Analysis"])


class AnalyzeRequest(BaseModel):
    rfp_text: str = Field(..., description="RFP document text to analyze", min_length=100)
    rfp_id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        description="Optional unique identifier for this RFP",
    )


@router.post("/analyze", response_model=RFPAnalysisResponse)
def analyze_rfp(request: AnalyzeRequest, client: OpenAI = Depends(get_openai_client)):
    """
    Analyze RFP text and map to Equinix solutions.

    Process:
    1. Extract structured information (company, technical, security, operational)
    2. Map extracted requirements to solution categories
    3. Return analysis with confidence scores
    """
    try:
        graph = RFPProcessGraph(client=client)
        response = graph.process_rfp(rfp_text=request.rfp_text, rfp_id=request.rfp_id)
        return response
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error processing RFP: {str(e)}",
        )


@router.post("/analyze-pdf", response_model=RFPAnalysisResponse)
async def analyze_pdf(
    file: UploadFile = File(...),
    format: str = "markdown",
    client: OpenAI = Depends(get_openai_client)
):
    """
    Analyze PDF RFP document and map to Equinix solutions.

    Accepts: PDF files up to 10MB
    Process:
    1. Validate PDF format and size
    2. Extract text/markdown from PDF preserving layout
    3. Extract structured information (company, technical, security, operational)
    4. Map extracted requirements to solution categories
    5. Return analysis with confidence scores
    """
    try:
        file_content = await file.read()

        PDFService.validate_pdf(file_content, file.filename)
        logger.debug(f"PDF '{file.filename}' passed validation")

        rfp_text = PDFService.process_pdf(file_content, file.filename, format=format)
        logger.debug(f"Extracted text from PDF '{file.filename}' (length: {len(rfp_text)} characters)")

        if not rfp_text.strip():
            raise ValueError("PDF contains no extractable text")
        
        graph = RFPProcessGraph(client=client)
        rfp_id = str(uuid.uuid4())
        response = graph.process_rfp(rfp_text=rfp_text, rfp_id=rfp_id)
        return response

    except PDFValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error processing PDF: {str(e)}",
        )


@router.get("/health")
def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}
