import json
from typing import Optional
from openai import OpenAI
from app.models.rfp_extraction import (
    CompanyInfo,
    TechnicalRequirements,
    SecurityRequirements,
    OperationalConstraints,
    ExtractedRFP,
)
from app.utils.prompts import EXTRACTION_PROMPT
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
        prompt = EXTRACTION_PROMPT.format(rfp_text=rfp_text)
        logger.debug(f"Prompt Ready")

        response = self.client.chat.completions.create(
            model="gpt-5.2-chat-latest",
            messages=[{"role": "user", "content": prompt}]
        )

        content = response.choices[0].message.content
        extracted_json = self._parse_json_response(content)

        return self._build_extracted_rfp(extracted_json)

    def _parse_json_response(self, content: str) -> dict:
        """Extract JSON from LLM response."""
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            start = content.find("{")
            end = content.rfind("}") + 1
            if start >= 0 and end > start:
                return json.loads(content[start:end])
            raise ValueError("Could not parse JSON from LLM response")

    def _build_extracted_rfp(self, data: dict) -> ExtractedRFP:
        """Build ExtractedRFP model from extracted data."""
        company_info = CompanyInfo(**data.get("company_info", {}))
        technical_requirements = TechnicalRequirements(
            **data.get("technical_requirements", {})
        )
        security_requirements = SecurityRequirements(**data.get("security_requirements", {}))
        operational_constraints = OperationalConstraints(
            **data.get("operational_constraints", {})
        )
        raw_summary = data.get("raw_summary", "")

        return ExtractedRFP(
            company_info=company_info,
            technical_requirements=technical_requirements,
            security_requirements=security_requirements,
            operational_constraints=operational_constraints,
            raw_summary=raw_summary,
        )
