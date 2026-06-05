from pydantic import BaseModel, Field


class TrialLookupRequest(BaseModel):
    input: str = Field(
        ...,
        min_length=1,
        description="NCT ID (e.g. NCT05123456) or ClinicalTrials.gov URL",
    )


class EligibilityCriteria(BaseModel):
    inclusion_criteria: str | None = None
    exclusion_criteria: str | None = None
    minimum_age: str | None = None
    maximum_age: str | None = None
    sex: str | None = None
    healthy_volunteers: bool | None = None


class TrialSummary(BaseModel):
    nct_id: str
    brief_title: str
    official_title: str | None = None
    overall_status: str | None = None
    phases: list[str] = []
    conditions: list[str] = []
    eligibility: EligibilityCriteria
    ctgov_url: str
