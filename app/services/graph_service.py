from typing import TypedDict
from langgraph.graph import StateGraph, START, END
from app.services.extraction_service import ExtractionService
from app.services.mapping_service import MappingService
from app.models.rfp_extraction import ExtractedRFP
from app.models.solution_mapping import RFPAnalysisResponse
from datetime import datetime
from openai import OpenAI
from loguru import logger


class RFPProcessState(TypedDict):
    """State shared between graph nodes."""

    rfp_text: str
    extracted_data: ExtractedRFP
    solution_mappings: list


class RFPProcessGraph:
    def __init__(self, client=None):
        self.client = client or OpenAI()
        self.extraction_service = ExtractionService(self.client)
        self.mapping_service = MappingService(self.client)
        self.graph = self._build_graph()

    def _build_graph(self):
        """Build LangGraph workflow."""
        graph = StateGraph(RFPProcessState)

        graph.add_node("extract", self._extraction_node)
        graph.add_node("map", self._mapping_node)

        graph.add_edge(START, "extract")
        graph.add_edge("extract", "map")
        graph.add_edge("map", END)

        return graph.compile()

    def _extraction_node(self, state: RFPProcessState) -> RFPProcessState:
        """Extract structured data from RFP."""
        logger.debug(f"Starting extraction node with RFP text length: {len(state["rfp_text"])}")
        extracted_data = self.extraction_service.extract_rfp_info(state["rfp_text"])
        return {
            **state,
            "extracted_data": extracted_data,
        }

    def _mapping_node(self, state: RFPProcessState) -> RFPProcessState:
        """Map extracted data to solutions."""
        solution_mappings = self.mapping_service.map_to_solutions(
            state["extracted_data"]
        )
        return {
            **state,
            "solution_mappings": solution_mappings,
        }

    def process_rfp(self, rfp_text: str, rfp_id: str = None) -> RFPAnalysisResponse:
        """
        Process RFP through the multi-agent workflow.

        Args:
            rfp_text: Raw RFP document text
            rfp_id: Optional unique identifier for this RFP

        Returns:
            RFPAnalysisResponse: Complete analysis with extraction and solution mappings
        """
        initial_state: RFPProcessState = {
            "rfp_text": rfp_text,
            "extracted_data": None,
            "solution_mappings": [],
        }

        result = self.graph.invoke(initial_state)

        return RFPAnalysisResponse(
            rfp_id=rfp_id,
            extracted_data=result["extracted_data"],
            solution_mappings=result["solution_mappings"],
            analysis_timestamp=datetime.utcnow(),
        )
