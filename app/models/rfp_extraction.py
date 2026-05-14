from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field


# ----- Enums (stable categorical vocabularies) -----

class Priority(str, Enum):
    MANDATORY = "mandatory"   # explicit pass/fail or "must"
    PREFERRED = "preferred"   # "should" or "preferred"
    OPTIONAL = "optional"     # "nice to have"

class RequirementTheme(str, Enum):
    POWER = "power"
    COOLING = "cooling"
    SPACE = "space"
    NETWORK_INTERNET = "network_internet"
    NETWORK_CARRIER = "network_carrier"
    NETWORK_CLOUD = "network_cloud"
    NETWORK_INTERCONNECT = "network_interconnect"
    PHYSICAL_SECURITY = "physical_security"
    LOGICAL_SECURITY = "logical_security"
    COMPLIANCE = "compliance"
    RESILIENCY = "resiliency"
    OPERATIONS = "operations"
    SCALABILITY = "scalability"
    GEOGRAPHIC = "geographic"
    COMMERCIAL = "commercial"
    MIGRATION = "migration"
    OTHER = "other"

class RedundancyLevel(str, Enum):
    N = "N"
    N_PLUS_1 = "N+1"
    TWO_N = "2N"
    TWO_N_PLUS_1 = "2N+1"
    UNSPECIFIED = "unspecified"

class IssuerType(str, Enum):
    PUBLIC_SECTOR = "public_sector"
    HIGHER_EDUCATION = "higher_education"
    HEALTHCARE = "healthcare"
    FINANCIAL_SERVICES = "financial_services"
    ENTERPRISE = "enterprise"
    OTHER = "other"


# ----- Source provenance -----

class SourceSpan(BaseModel):
    page: int = Field(..., ge=1, description="1-indexed page number")
    excerpt: str = Field(
        ..., max_length=400,
        description="Verbatim quote from the RFP supporting this field"
    )


# ----- The granular requirement (the most important addition) -----

class Requirement(BaseModel):
    id: str = Field(..., description="Stable ID: REQ-001, REQ-002, ...")
    theme: RequirementTheme
    description: str = Field(..., description="What the RFP asks for, in plain language")
    priority: Priority
    quantitative_value: Optional[str] = Field(
        None, description="Numeric/unit value if applicable, e.g. '35kW', '/16', '250 miles'"
    )
    source: SourceSpan


# ----- Domain sub-models (signal-rich, typed) -----

class GeographicConstraint(BaseModel):
    reference_address: Optional[str] = None
    preferred_radius_miles: Optional[float] = None
    max_radius_miles: Optional[float] = None
    excluded_regions: List[str] = Field(default_factory=list)
    source: Optional[SourceSpan] = None

class PowerSpec(BaseModel):
    total_kw: Optional[float] = None
    kw_per_cabinet: Optional[float] = None
    feed_redundancy: Optional[str] = Field(None, description="e.g. 'A/B feeds', 'dual substation'")
    redundancy_level: Optional[RedundancyLevel] = None
    generator_backup: Optional[bool] = None
    source: Optional[SourceSpan] = None

class CoolingSpec(BaseModel):
    capacity_tons: Optional[float] = None
    reserve_tons: Optional[float] = None
    cooling_features: List[str] = Field(
        default_factory=list,
        description="e.g. 'air-side economizer', 'hot/cold aisle containment', 'VESDA'"
    )
    redundancy_level: Optional[RedundancyLevel] = None
    source: Optional[SourceSpan] = None

class NetworkSpec(BaseModel):
    carrier_neutral_required: Optional[bool] = None
    required_carriers: List[str] = Field(default_factory=list)
    bgp_required: Optional[bool] = None
    public_asn_required: Optional[bool] = None
    customer_ip_advertisement: Optional[str] = Field(None, description="e.g. '/16'")
    cloud_on_ramps_required: List[str] = Field(
        default_factory=list, description="e.g. ['AWS', 'Azure', 'GCP']"
    )
    cross_connects_required: Optional[bool] = None
    meet_me_room_diversity_required: Optional[bool] = None
    ddos_protection_required: Optional[bool] = None
    source: Optional[SourceSpan] = None

class PhysicalSecuritySpec(BaseModel):
    staffed_24x7: Optional[bool] = None
    armed_guards: Optional[bool] = None
    perimeter_fencing: Optional[bool] = None
    person_trap_entry: Optional[bool] = None
    biometric_access: Optional[bool] = None
    multi_factor_access: Optional[bool] = None
    cctv_required: Optional[bool] = None
    customer_owned_cameras_permitted: Optional[bool] = None
    noc_soc_onsite: Optional[bool] = None
    no_exterior_windows_on_floor: Optional[bool] = None
    source: Optional[SourceSpan] = None

class ComplianceRequirement(BaseModel):
    standard: str = Field(..., description="e.g. 'SOC 2 Type II', 'HIPAA', 'PCI DSS', 'NDAA'")
    priority: Priority
    source: Optional[SourceSpan] = None

class ResiliencySpec(BaseModel):
    facility_tier: Optional[str] = Field(None, description="e.g. 'Uptime Institute Tier III'")
    uptime_sla: Optional[str] = None
    generator_runtime_hours: Optional[float] = None
    lightning_protection: Optional[bool] = None
    historical_uptime_required: Optional[bool] = None
    source: Optional[SourceSpan] = None

class OperationsSpec(BaseModel):
    remote_hands_24x7: Optional[bool] = None
    emergency_access_required: Optional[bool] = None
    chain_of_custody_required: Optional[bool] = None
    onsite_workspace_required: Optional[bool] = None
    receiving_and_storage_required: Optional[bool] = None
    source: Optional[SourceSpan] = None

class WorkloadProfile(BaseModel):
    use_case: Optional[str] = Field(
        None, description="e.g. 'production migration', 'disaster recovery', 'edge'"
    )
    listed_equipment: List[str] = Field(
        default_factory=list,
        description="Specific hardware mentioned, e.g. 'VMware hosts', 'Palo Alto firewalls'"
    )
    application_types: List[str] = Field(
        default_factory=list,
        description="Application/workload categories, e.g. 'SIS', 'LMS', 'ERP', 'AI training'"
    )
    high_density_indicated: Optional[bool] = Field(
        None, description="True if kW/cabinet > 15 or GPU/HPC mentioned"
    )
    real_time_or_low_latency_indicated: Optional[bool] = None
    source: Optional[SourceSpan] = None


# ----- Administrative / evaluation -----

class AdministrativeDetails(BaseModel):
    rfp_title: str
    rfp_number: Optional[str] = None
    issue_date: Optional[str] = None
    questions_deadline: Optional[str] = None
    submission_deadline: Optional[str] = None
    target_service_start: Optional[str] = None
    contract_term: Optional[str] = None
    submission_method: Optional[str] = None
    contact: Optional[str] = None
    procurement_constraints: List[str] = Field(
        default_factory=list,
        description="e.g. 'MBE/WBE participation goals', 'debarment certification required'"
    )

class CompanyInfo(BaseModel):
    name: str
    issuer_type: IssuerType
    industry: Optional[str] = None
    headquarters: Optional[str] = None
    description: Optional[str] = Field(None, max_length=300)

class EvaluationCriterion(BaseModel):
    category: str = Field(..., description="e.g. 'Location', 'Power & Facility Infrastructure'")
    weight_pct: float = Field(..., ge=0, le=100)
    description: Optional[str] = None
    source: Optional[SourceSpan] = None

class MandatoryItem(BaseModel):
    description: str
    source: Optional[SourceSpan] = None


# ----- Root -----

class ExtractedRFP(BaseModel):
    rfp_id: str = Field(..., description="Stable ID derived from filename or hash")
    company_info: CompanyInfo
    administrative: AdministrativeDetails
    project_objective: str = Field(
        ..., max_length=500,
        description="One-sentence statement of what the RFP is trying to achieve"
    )
    workload: WorkloadProfile

    # High-signal domain sub-models — all optional, populated where the RFP speaks to them
    geographic_constraint: Optional[GeographicConstraint] = None
    power: Optional[PowerSpec] = None
    cooling: Optional[CoolingSpec] = None
    network: Optional[NetworkSpec] = None
    physical_security: Optional[PhysicalSecuritySpec] = None
    resiliency: Optional[ResiliencySpec] = None
    operations: Optional[OperationsSpec] = None
    compliance: List[ComplianceRequirement] = Field(default_factory=list)

    # Granular, ID-addressable requirements — the mapper cites these
    requirements: List[Requirement] = Field(
        ..., description="All individual requirements as first-class objects with IDs"
    )

    # Priority signal from the RFP itself
    mandatory_requirements: List[MandatoryItem] = Field(default_factory=list)
    evaluation_criteria: List[EvaluationCriterion] = Field(default_factory=list)

    # Catch-alls
    notable_unique_requirements: List[str] = Field(
        default_factory=list,
        description="Distinctive requirements that don't fit the sub-models (e.g. 'customer-owned IP cameras in cage', 'NDAA/John McCain Defense Act compliance')"
    )
    referenced_attachments: List[str] = Field(
        default_factory=list,
        description="Files the RFP references but that weren't provided (e.g. 'Cost Sheet xlsx')"
    )