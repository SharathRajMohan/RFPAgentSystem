from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from app.services.graph_service import RFPProcessGraph
from app.services.pdf_service import PDFService, PDFValidationError
from app.models.solution_mapping import RFPAnalysisResponse
from app.api.dependencies import get_openai_client
from openai import OpenAI
from loguru import logger


router = APIRouter(prefix="/api/v1", tags=["RFP Analysis"])

@router.post("/analyze-pdf", response_model=RFPAnalysisResponse)
async def analyze_pdf(
    file: UploadFile = File(...),
    client: OpenAI = Depends(get_openai_client)
):
    """
    Analyze PDF RFP document and map to Equinix solutions.

    Accepts: PDF files up to 10MB
    Process:
    1. Validate PDF format and size
    2. Extract markdown from PDF preserving layout
    3. Extract structured information (company, technical, security, operational)
    4. Map extracted requirements to solution categories
    5. Return analysis with confidence scores
    """
    try:
        file_content = await file.read()

        PDFService.validate_pdf(file_content, file.filename)
        logger.debug(f"PDF '{file.filename}' passed validation")

        rfp_text = PDFService.process_pdf(file_content=file_content)
        logger.debug(f"Extracted text from PDF '{file.filename}' (length: {len(rfp_text)} characters)")

        if not rfp_text.strip():
            raise ValueError("PDF contains no extractable text")
        
        graph = RFPProcessGraph(client=client)
        response = graph.process_rfp(rfp_text=rfp_text)
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
