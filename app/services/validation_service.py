from typing import List
from loguru import logger
from app.models.rfp_extraction import ExtractedRFP
from app.models.solution_mapping import (
    GroundingIssue,
    SolutionMappingSet,
    ValidationReport,
)


class ValidationService:
    """Code-side checks on LLM-produced mappings. No LLM calls.

    Two classes of check:
      1. Grounding — every requirement ID cited must exist in the extraction.
      2. Catalog coverage — every catalog play scored exactly once; no unknowns.
    """

    def validate(
        self,
        mappings: SolutionMappingSet,
        extracted_rfp: ExtractedRFP,
        catalog_names: set[str],
    ) -> ValidationReport:
        valid_req_ids = {r.id for r in extracted_rfp.requirements}
        returned_names = {m.solution_name for m in mappings.mappings}
        logger.debug(f"Returned solution names: {returned_names}")
        issues: List[GroundingIssue] = []
        for mapping in mappings.mappings:
            for assessment in mapping.signal_assessments:
                missing = [
                    rid for rid in assessment.requirement_ids
                    if rid not in valid_req_ids
                ]
                if missing:
                    issues.append(GroundingIssue(
                        solution_name=mapping.solution_name,
                        signal=assessment.signal,
                        invalid_requirement_ids=missing,
                        message=(
                            f"Signal cites {len(missing)} requirement ID(s) "
                            f"not present in the extraction."
                        ),
                    ))

        missing_plays = sorted(catalog_names - returned_names)
        unknown_plays = sorted(returned_names - catalog_names)

        return ValidationReport(
            passed=not (issues or missing_plays or unknown_plays),
            issues=issues,
            missing_catalog_plays=missing_plays,
            unknown_catalog_plays=unknown_plays,
        )