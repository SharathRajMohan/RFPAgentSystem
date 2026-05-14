from typing import Optional
from openai import OpenAI
from app.models.rfp_extraction import ExtractedRFP
from app.utils.prompts import EXTRACTION_USER_PROMPT, EXTRACTION_SYSTEM_PROMPT
from app.api.dependencies import get_openai_model
from loguru import logger

class ExtractionService:
    def __init__(self, client: Optional[OpenAI] = None):
        self.client = client or OpenAI()

    def extract_rfp_info(self, rfp_text: str) -> ExtractedRFP:
        """
        Extract structured information from RFP text using Claude.

        Args:
            rfp_text: Raw RFP document text

        Returns:
            ExtractedRFP: Structured extraction with company info, technical/security/operational requirements
        """
        prompt = EXTRACTION_USER_PROMPT.format(rfp_text=rfp_text)
        logger.debug(f"Prompt Ready")

        response = self.client.responses.parse(
            model=get_openai_model(),
            instructions=EXTRACTION_SYSTEM_PROMPT,
            input=[{"role": "user", "content": prompt}],
            text_format = ExtractedRFP,
            store=False
        )
        content = response.output_parsed
        return content
    