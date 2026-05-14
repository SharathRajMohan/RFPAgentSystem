import json

EXTRACTION_PROMPT = """
You are an expert RFP analyst. Extract key information from the provided RFP document and structure it into the following JSON format:

{{
    "company_info": {{
        "name": "Company name",
        "industry": "Industry vertical",
        "size": "Company size (SMB/Enterprise/etc)",
        "headquarters": "Location if mentioned"
    }},
    "technical_requirements": {{
        "compute_needs": "Specific compute requirements (CPU, GPU, cores, etc.)",
        "storage_capacity": "Storage requirements (TB, EB, specific types like SSD, etc.)",
        "networking": "Network bandwidth, connectivity, protocols needed",
        "performance_sla": "Latency requirements, throughput, uptime SLAs",
        "specific_workloads": ["List of workload types: e.g., AI training, real-time analytics, video streaming, etc."]
    }},
    "security_requirements": {{
        "compliance_standards": ["List of compliance needs: HIPAA, SOC2, ISO 27001, GDPR, PCI-DSS, etc."],
        "data_residency": "Geographic data residency requirements if any",
        "encryption_needs": "Encryption requirements (at rest, in transit, specific algorithms)",
        "threat_model": "Specific threat concerns or security architectures needed",
        "zero_trust": true
    }},
    "operational_constraints": {{
        "budget_range": "Budget if mentioned",
        "timeline": "Implementation timeline",
        "sla_uptime": "Required uptime percentage",
        "geographic_regions": ["List of regions/availability zones needed"],
        "disaster_recovery": "Disaster recovery and backup requirements"
    }},
    "raw_summary": "Brief 2-3 sentence summary of the RFP"
}}

Extract all available information from the RFP. Use null for fields that are not mentioned. Be specific and include exact numbers/requirements when found.

RFP Document:
{rfp_text}
"""
MAPPING_PROMPT = """You are scoring an RFP against a fixed catalog of six Equinix sales plays. \
Score EVERY play in the catalog — including plays that are a poor fit. Do not omit plays.
# Catalog (the only allowed solution names)

{solutions_text}

Each play has 4 signal-statements, these are conditions that indicate if the solution matches the problem. You will check the extracted RFP information against each signal individually.

Extracted Requirements:
{extracted_requirements}

For each relevant solution, provide:
1. Solution name
2. Confidence Level: High, Medium, Low or None based on how well the solution aligns with the requirements
3. Specific evidence from the RFP supporting this mapping
4. Key features that align with the RFP requirements

# Confidence rubric (apply strictly)
HIGH    — At least 3 of the play's 4 signals are evidenced by requirements in the RFP,
          AND at least one supporting requirement is MANDATORY,
          AND supporting evidence concentrates in evaluation criteria with combined weight >= 20%.
MEDIUM  — 2 signals evidenced, OR 3+ signals all from PREFERRED (no mandatory) requirements,
          OR strong evidence concentrated in low-weight criteria.
LOW     — 1 signal evidenced, indirect/inferred matches only, or conflicting indicators.
NONE    — 0 signals evidenced.

# Required reasoning (think before scoring)
For each play, in order:
  a) Walk the 4 signals one by one. For each, mark MET / PARTIAL / NOT_MET and cite the
     evidence that support the judgment.
  b) Identify evidence: requirements or facts that argue that this play is a good fit.
  c) Apply the rubric to assign confidence.

Return ONLY a JSON array like this:
[
    {{
        "solution_name": "Solution Name",
        "confidence_level": "High/Medium/Low",
        "supporting_evidence": "Specific quotes/references from RFP",
        "key_features_aligned": ["feature 1", "feature 2"],
        "reason": "2-3 sentences explaining why this is the confidence level assigned, referencing the signals and evidence."
    }}
]

# Constraints:
- Output exactly 6 mappings, one per catalog play.
- `solution_name` must exactly match a catalog name; never invent new categories.
- Be conservative: when evidence is weak, prefer LOW over MEDIUM."""

def format_extracted_for_mapping(extracted_rfp) -> str:
    """Format extracted RFP data for the mapping prompt."""
    return f"""
Company: {extracted_rfp.company_info.name} ({extracted_rfp.company_info.industry})
Size: {extracted_rfp.company_info.size or 'Not specified'}

Technical Requirements:
- Compute: {extracted_rfp.technical_requirements.compute_needs or 'Not specified'}
- Storage: {extracted_rfp.technical_requirements.storage_capacity or 'Not specified'}
- Networking: {extracted_rfp.technical_requirements.networking or 'Not specified'}
- Performance SLA: {extracted_rfp.technical_requirements.performance_sla or 'Not specified'}
- Workloads: {', '.join(extracted_rfp.technical_requirements.specific_workloads) if extracted_rfp.technical_requirements.specific_workloads else 'Not specified'}

Security Requirements:
- Compliance: {', '.join(extracted_rfp.security_requirements.compliance_standards) if extracted_rfp.security_requirements.compliance_standards else 'Not specified'}
- Data Residency: {extracted_rfp.security_requirements.data_residency or 'Not specified'}
- Encryption: {extracted_rfp.security_requirements.encryption_needs or 'Not specified'}
- Threat Model: {extracted_rfp.security_requirements.threat_model or 'Not specified'}
- Zero Trust: {extracted_rfp.security_requirements.zero_trust or 'Not specified'}

Operational Constraints:
- Budget: {extracted_rfp.operational_constraints.budget_range or 'Not specified'}
- Timeline: {extracted_rfp.operational_constraints.timeline or 'Not specified'}
- Uptime SLA: {extracted_rfp.operational_constraints.sla_uptime or 'Not specified'}
- Regions: {', '.join(extracted_rfp.operational_constraints.geographic_regions) if extracted_rfp.operational_constraints.geographic_regions else 'Not specified'}
- Disaster Recovery: {extracted_rfp.operational_constraints.disaster_recovery or 'Not specified'}
"""

def load_solution_definitions(json_path: str) -> dict:
    """
    Load solution definitions from a JSON file.
    """
    with open(json_path, "r", encoding="utf-8") as f:
        return json.load(f)


def format_solutions_for_prompt(solution_definitions: dict) -> str:
    """
    Convert solution JSON into a formatted prompt section.
    """
    formatted = []

    for idx, (solution_name, details) in enumerate(solution_definitions.items(), start=1):

        features = ", ".join(details.get("key_features", []))

        section = f"""
                    {idx}. {solution_name}
                    - Description: {details.get('description', '')}
                    - Key features: {features}
                    """

        formatted.append(section.strip())

    return "\n\n".join(formatted)