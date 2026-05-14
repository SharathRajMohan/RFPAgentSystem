import fitz
import pymupdf4llm
import pymupdf
from io import BytesIO
from typing import Tuple


class PDFValidationError(Exception):
    """Raised when PDF validation fails."""
    pass


class PDFService:
    """Service for PDF validation and conversion to text/markdown."""

    MAX_FILE_SIZE_MB = 10
    MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024

    @staticmethod
    def validate_pdf(file_content: bytes, filename: str) -> None:
        """
        Validate PDF file.

        Args:
            file_content: Raw file bytes
            filename: Original filename

        Raises:
            PDFValidationError: If validation fails
        """
        if not filename.lower().endswith('.pdf'):
            raise PDFValidationError(f"File must be a PDF. Got: {filename}")

        if len(file_content) == 0:
            raise PDFValidationError("File is empty")

        if len(file_content) > PDFService.MAX_FILE_SIZE_BYTES:
            size_mb = len(file_content) / (1024 * 1024)
            raise PDFValidationError(
                f"File exceeds {PDFService.MAX_FILE_SIZE_MB}MB limit. Got: {size_mb:.2f}MB"
            )

        try:
            doc = fitz.open(stream=file_content, filetype="pdf")
            if len(doc) == 0:
                raise PDFValidationError("PDF has no pages")
            doc.close()
        except Exception as e:
            raise PDFValidationError(f"Invalid PDF file: {str(e)}")

    @staticmethod
    def process_pdf(
        file_content: bytes
    ) -> str:
        """
        Extract text from PDF as markdown while preserving layout.

        Analyzes text blocks for structure (headers, lists) and converts to markdown.

        Args:
            file_content: Raw PDF file bytes

        Returns:
            Extracted content formatted as markdown
        """
        raw_doc = pymupdf.open(stream=BytesIO(file_content), filetype="pdf")
        doc = pymupdf4llm.to_markdown(raw_doc)

        return doc
