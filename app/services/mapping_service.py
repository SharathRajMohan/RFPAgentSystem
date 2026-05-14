import json
from typing import List, Optional
from openai import OpenAI
from app.models.rfp_extraction import ExtractedRFP
from app.models.solution_mapping import SolutionMapping
from app.utils.prompts import MAPPING_PROMPT, format_extracted_for_mapping, load_solution_definitions, format_solutions_for_prompt
from dotenv import load_dotenv
import os

load_dotenv()  # Load environment variables from .env file
SOLUTIONS_JSON_PATH = os.getenv("SOLUTIONS_JSON_PATH", "solutions.json")

class MappingService:
    def __init__(self, client: Optional[OpenAI] = None):
        self.client = client or OpenAI()
        self.solutions = load_solution_definitions(SOLUTIONS_JSON_PATH)

    def map_to_solutions(self, extracted_rfp: ExtractedRFP) -> List[SolutionMapping]:
        """
        Map extracted RFP requirements to Equinix solutions.

        Args:
            extracted_rfp: Structured RFP data from extraction agent

        Returns:
            List[SolutionMapping]: Solutions with confidence scores and evidence
        """
        formatted_requirements = format_extracted_for_mapping(extracted_rfp)
        formatted_solutions = format_solutions_for_prompt(self.solutions)
        prompt = MAPPING_PROMPT.format(solutions_text =formatted_solutions ,extracted_requirements=formatted_requirements)

        response = self.client.chat.completions.create(
            model="gpt-5.2-chat-latest",
            messages=[{"role": "user", "content": prompt}]
        )

        content = response.choices[0].message.content
        mappings_data = self._parse_json_response(content)

        return [
            SolutionMapping(
                solution_name=mapping["solution_name"],
                confidence_level=mapping["confidence_level"],
                supporting_evidence=mapping["supporting_evidence"],
                key_features_aligned=mapping["key_features_aligned"],
            )
            for mapping in mappings_data
        ]


    def _parse_json_response(self, content: str) -> list:
        """Extract JSON array from LLM response."""
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            start = content.find("[")
            end = content.rfind("]") + 1
            if start >= 0 and end > start:
                return json.loads(content[start:end])
            raise ValueError("Could not parse JSON array from LLM response")
