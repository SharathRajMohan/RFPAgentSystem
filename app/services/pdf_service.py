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
    def extract_text(file_content: bytes) -> str:
        """
        Extract text from PDF while preserving layout.

        Uses blocks layout to maintain document structure and formatting.

        Args:
            file_content: Raw PDF file bytes

        Returns:
            Extracted text with preserved layout
        """
        doc = fitz.open(stream=file_content, filetype="pdf")
        text = ""

        try:
            for page_num in range(len(doc)):
                page = doc[page_num]
                text += page.get_text(
                    "blocks",
                    sort=True,
                )
                text += "\n---PAGE BREAK---\n"
        finally:
            doc.close()

        return text

    @staticmethod
    def extract_markdown(file_content: bytes) -> str:
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

    @staticmethod
    def process_pdf(
        file_content: bytes,
        filename: str,
        format: str = "markdown"
    ) -> str:
        """
        Process PDF file with validation and conversion.

        Args:
            file_content: Raw PDF file bytes
            filename: Original filename
            format: Output format ('text' or 'markdown')

        Returns:
            Extracted content in requested format

        Raises:
            PDFValidationError: If validation fails
            ValueError: If format is unsupported
        """

        if format == "text":
            return PDFService.extract_text(file_content)
        elif format == "markdown":
            return PDFService.extract_markdown(file_content)
        else:
            raise ValueError(f"Unsupported format: {format} for file-{filename}. Use 'text' or 'markdown'")
