from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


class SolutionMapping(BaseModel):
    solution_name: str = Field(..., description="Name of the Equinix solution/sales play")
    confidence_level: str = Field(..., description="Confidence level of this mapping (High/Medium/Low)")
    supporting_evidence: str = Field(..., description="Evidence from RFP supporting this mapping")
    key_features_aligned: List[str] = Field(..., description="Key features that align with requirements")


class RFPAnalysisResponse(BaseModel):
    rfp_id: Optional[str] = Field(None, description="Unique identifier for this RFP analysis")
    extracted_data: "ExtractedRFP" = Field(..., description="Extracted structured data from RFP")
    solution_mappings: List[SolutionMapping] = Field(..., description="Mapped solutions with confidence scores")
    analysis_timestamp: datetime = Field(default_factory=datetime.utcnow, description="When this analysis was performed")


from .rfp_extraction import ExtractedRFP
RFPAnalysisResponse.model_rebuild()
