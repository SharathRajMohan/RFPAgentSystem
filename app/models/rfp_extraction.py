from pydantic import BaseModel, Field
from typing import Optional, List


class CompanyInfo(BaseModel):
    name: str = Field(..., description="Company name")
    industry: str = Field(..., description="Industry vertical")
    size: Optional[str] = Field(None, description="Company size (e.g., SMB, Enterprise)")
    headquarters: Optional[str] = Field(None, description="Headquarters location")


class TechnicalRequirements(BaseModel):
    compute_needs: Optional[str] = Field(None, description="Compute requirements (CPU, GPU, etc.)")
    storage_capacity: Optional[str] = Field(None, description="Storage capacity needs")
    networking: Optional[str] = Field(None, description="Network requirements and bandwidth")
    performance_sla: Optional[str] = Field(None, description="Performance SLAs and latency requirements")
    specific_workloads: Optional[List[str]] = Field(None, description="Specific workload types (e.g., AI, IoT, streaming)")


class SecurityRequirements(BaseModel):
    compliance_standards: Optional[List[str]] = Field(None, description="Compliance requirements (HIPAA, SOC2, etc.)")
    data_residency: Optional[str] = Field(None, description="Data residency requirements")
    encryption_needs: Optional[str] = Field(None, description="Encryption requirements")
    threat_model: Optional[str] = Field(None, description="Specific threat concerns or attack surface reduction")
    zero_trust: Optional[bool] = Field(None, description="Requires zero-trust architecture")


class OperationalConstraints(BaseModel):
    budget_range: Optional[str] = Field(None, description="Budget range if specified")
    timeline: Optional[str] = Field(None, description="Implementation timeline")
    sla_uptime: Optional[str] = Field(None, description="Required uptime SLA")
    geographic_regions: Optional[List[str]] = Field(None, description="Geographic regions required")
    disaster_recovery: Optional[str] = Field(None, description="Disaster recovery and redundancy needs")


class ExtractedRFP(BaseModel):
    company_info: CompanyInfo
    technical_requirements: TechnicalRequirements
    security_requirements: SecurityRequirements
    operational_constraints: OperationalConstraints
    raw_summary: str = Field(..., description="Brief summary of the RFP")
