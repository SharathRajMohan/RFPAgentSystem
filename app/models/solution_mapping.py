from datetime import datetime, timezone
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field, field_validator, model_validator

class Confidence(str, Enum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    NONE = "NONE"


class SignalStatus(str, Enum):
    MET = "MET"
    PARTIAL = "PARTIAL"
    NOT_MET = "NOT_MET"

class SignalAssessment(BaseModel):
    """Each play has 4 signal-statements; the mapper walks them one by one."""
    signal: str = Field(
        ...,
        description="Verbatim signal-statement from the catalog. Do not paraphrase.",
    )
    status: SignalStatus
    requirement_ids: List[str] = Field(
        default_factory=list,
        description=(
            "IDs (REQ-xxx) from ExtractedRFP.requirements that evidence this signal. "
            "Empty when status is NOT_MET; non-empty otherwise."
        ),
    )

    @field_validator("requirement_ids")
    @classmethod
    def _id_prefix(cls, v: List[str]) -> List[str]:
        for rid in v:
            if not rid.startswith("REQ-"):
                raise ValueError(f"Requirement ID must start with 'REQ-': {rid!r}")
        return v

    @model_validator(mode="after")
    def _status_matches_evidence(self) -> "SignalAssessment":
        if self.status == SignalStatus.NOT_MET and self.requirement_ids:
            raise ValueError("NOT_MET signals must not cite requirement_ids")
        if self.status in (SignalStatus.MET, SignalStatus.PARTIAL) and not self.requirement_ids:
            raise ValueError(f"{self.status.value} signals must cite at least one requirement_id")
        return self

class SolutionMapping(BaseModel):
    solution_name: str = Field(
        ...,
        description="Exact catalog name; validated against the loaded catalog in code.",
    )

    signal_assessments: List[SignalAssessment] = Field(
        ...,
        min_length=1,
        description="One assessment per signal-statement in the play, in catalog order.",
    )

    counter_evidence: Optional[str] = Field(
        None,
        max_length=500,
        description=(
            "RFP facts that argue AGAINST this fit. Null only when none apply."
        ),
    )

    confidence: Confidence

    score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Alignment score; loose anchors: HIGH 0.75–1.00, MEDIUM 0.45–0.74, LOW 0.15–0.44, NONE 0.00–0.14.",
    )

    rationale: str = Field(
        ...,
        min_length=20,
        max_length=600,
        description="2–3 sentences applying the rubric.",
    )

    @property
    def supporting_requirement_ids(self) -> List[str]:
        """Derived from signal_assessments — do not ask the LLM to repeat this."""
        return sorted({
            rid for s in self.signal_assessments for rid in s.requirement_ids
        })

    @model_validator(mode="after")
    def _score_aligned_with_confidence(self) -> "SolutionMapping":
        bounds = {
            Confidence.HIGH:   (0.70, 1.00),
            Confidence.MEDIUM: (0.40, 0.79),
            Confidence.LOW:    (0.10, 0.49),
            Confidence.NONE:   (0.00, 0.20),
        }
        lo, hi = bounds[self.confidence]
        if not (lo <= self.score <= hi):
            raise ValueError(
                f"score {self.score} inconsistent with confidence {self.confidence.value} "
                f"(expected {lo}–{hi})"
            )
        return self

class SolutionMappingSet(BaseModel):
    """One SolutionMapping per catalog play, in catalog order."""
    mappings: List[SolutionMapping] = Field(..., min_length=1)

    @model_validator(mode="after")
    def _unique_names(self) -> "SolutionMappingSet":
        names = [m.solution_name for m in self.mappings]
        if len(names) != len(set(names)):
            raise ValueError("Each catalog play may appear at most once")
        return self

class GroundingIssue(BaseModel):
    solution_name: str
    signal: str
    invalid_requirement_ids: List[str]
    message: str


class ValidationReport(BaseModel):
    passed: bool
    issues: List[GroundingIssue] = Field(default_factory=list)
    missing_catalog_plays: List[str] = Field(default_factory=list)
    unknown_catalog_plays: List[str] = Field(default_factory=list)


class RFPAnalysisResponse(BaseModel):
    extracted_data: "ExtractedRFP"
    solution_mappings: SolutionMappingSet
    validation: ValidationReport
    analysis_timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
    )


from .rfp_extraction import ExtractedRFP   # circular import, deferred
RFPAnalysisResponse.model_rebuild()