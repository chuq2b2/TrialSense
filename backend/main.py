from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from ctgov import extract_trial_summary, fetch_trial, parse_nct_id
from matching import run_patient_matching
from nebius_client import NebiusError
from schemas import TrialLookupRequest, TrialMatchResponse, TrialSummary

app = FastAPI(
    title="TrialSense API",
    description="Clinical trial eligibility extraction for coordinator outreach",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/trials/lookup", response_model=TrialSummary)
async def lookup_trial(request: TrialLookupRequest) -> TrialSummary:
    try:
        nct_id = parse_nct_id(request.input)
        study = await fetch_trial(nct_id)
        summary = extract_trial_summary(study)
        return TrialSummary(**summary)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail="Unable to fetch trial data from ClinicalTrials.gov. Please try again.",
        ) from exc


@app.post("/api/trials/match", response_model=TrialMatchResponse)
async def match_trial(trial: TrialSummary) -> TrialMatchResponse:
    try:
        result = run_patient_matching(trial.model_dump())
        return TrialMatchResponse(
            nct_id=trial.nct_id,
            pool_size=result["pool_size"],
            prefilter_passed=result["prefilter_passed"],
            structured_criteria=result["structured_criteria"],
            matches=result["matches"],
            data_source=result.get("data_source", "csv"),
        )
    except NebiusError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail="Patient matching failed. Please try again in a moment.",
        ) from exc
