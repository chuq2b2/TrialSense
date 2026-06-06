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


class InclusionCriterionDetail(BaseModel):
    description: str
    status: str
    reason: str | None = None


class InclusionSummary(BaseModel):
    total: int
    met: int
    unmet: int
    unverified: int
    partial: int = 0
    criteria: list[InclusionCriterionDetail] = []


class PatientDetails(BaseModel):
    patient_id: str
    full_name: str
    age: int
    gender: str
    city: str = ""
    state: str = ""
    active_conditions: int = 0
    conditions: list[str] = []
    medications: list[str] = []
    bmi: float | None = None
    hba1c_pct: float | None = None
    glucose_mgdl: float | None = None
    systolic_bp: float | None = None
    diastolic_bp: float | None = None
    cholesterol_mgdl: float | None = None


class PatientMatch(BaseModel):
    patient_id: str
    patient: PatientDetails
    match_percent: float
    match_band: str
    hospital_name: str
    pcp_name: str
    organization_phone: str
    pcp_contact: str
    exclusion_reasons: list[str] = []
    needs_manual_review: bool = False
    inclusion_summary: InclusionSummary


class TrialMatchResponse(BaseModel):
    nct_id: str
    pool_size: int
    prefilter_passed: int
    structured_criteria: dict
    matches: list[PatientMatch]
    data_source: str = "csv"
