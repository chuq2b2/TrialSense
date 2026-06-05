from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from ctgov import extract_trial_summary, fetch_trial, parse_nct_id
from schemas import TrialLookupRequest, TrialSummary

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
