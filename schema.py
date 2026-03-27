from pydantic import BaseModel, Field
from typing import List, Dict

class ComplianceReport(BaseModel):
    is_compliant: bool = Field(description="True if content follows all brand and legal rules.")
    score: int = Field(description="Quality score 1-10.")
    violations: List[str] = Field(description="List of brand/legal violations.")
    feedback: str = Field(description="Instructions for the writer to fix the content.")

class DistributionOutput(BaseModel):
    linkedin: str = Field(description="Professional post version in English.")
    twitter: str = Field(description="Short version under 280 chars in English.")
    newsletter: str = Field(description="Email marketing version in English.")
    localizations: Dict[str, str] = Field(description="Localized summaries indexed by language name (e.g., {'Bengali': '...', 'Spanish': '...'}).")