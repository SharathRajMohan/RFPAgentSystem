import json
from typing import List, Optional
from openai import OpenAI
from app.models.rfp_extraction import ExtractedRFP
from app.models.solution_mapping import SolutionMappingSet
from app.utils.prompts import MAPPING_SYSTEM_PROMPT, MAPPING_USER_PROMPT, format_extracted_for_mapping, load_solution_definitions, format_solutions_for_prompt
from dotenv import load_dotenv
import os

load_dotenv()  # Load environment variables from .env file
SOLUTIONS_JSON_PATH = os.getenv("SOLUTIONS_JSON_PATH", "solutions.json")

class MappingService:
    def __init__(self, client: Optional[OpenAI] = None):
        self.client = client or OpenAI()
        self.solutions = load_solution_definitions(SOLUTIONS_JSON_PATH)
        self.catalog_names = set(self.solutions.keys())

    def map_to_solutions(self, extracted_rfp: ExtractedRFP) -> SolutionMappingSet:
        """
        Map extracted RFP requirements to Equinix solutions.

        Args:
            extracted_rfp: Structured RFP data from extraction agent

        Returns:
            List[SolutionMapping]: Solutions with confidence scores and evidence
        """
        formatted_requirements = format_extracted_for_mapping(extracted_rfp)
        formatted_solutions = format_solutions_for_prompt(self.solutions)
        system_prompt = MAPPING_SYSTEM_PROMPT.format(solutions_text=formatted_solutions)
        user_prompt = MAPPING_USER_PROMPT.format(extracted_requirements=formatted_requirements)

        response = self.client.responses.parse(
            model="gpt-5.2-chat-latest",
            instructions=system_prompt,
            input=[
                {"role": "user", "content": user_prompt},
            ],
            text_format=SolutionMappingSet,
            store=False
        )

        content = response.output_parsed
        return content
