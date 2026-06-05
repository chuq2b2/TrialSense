import asyncio
import re

import requests

CTGOV_API_BASE = "https://clinicaltrials.gov/api/v2"
NCT_ID_PATTERN = re.compile(r"NCT\d{8}", re.IGNORECASE)


def parse_nct_id(raw_input: str) -> str:
    """Extract a normalized NCT ID from a bare ID or ClinicalTrials.gov URL."""
    value = raw_input.strip()
    if not value:
        raise ValueError("Trial input is required.")

    match = NCT_ID_PATTERN.search(value)
    if not match:
        raise ValueError(
            "Could not find a valid NCT ID. Enter something like NCT05123456 "
            "or a ClinicalTrials.gov study URL."
        )

    return match.group(0).upper()


def split_eligibility_criteria(criteria_text: str | None) -> tuple[str | None, str | None]:
    """Split unstructured eligibility text into inclusion and exclusion sections."""
    if not criteria_text or not criteria_text.strip():
        return None, None

    text = criteria_text.strip()
    inclusion_markers = [
        r"inclusion\s+criteria\s*:",
        r"key\s+inclusion\s+criteria\s*:",
    ]
    exclusion_markers = [
        r"exclusion\s+criteria\s*:",
        r"key\s+exclusion\s+criteria\s*:",
    ]

    inclusion_start = None
    for pattern in inclusion_markers:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            inclusion_start = match.end()
            break

    exclusion_start = None
    for pattern in exclusion_markers:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            exclusion_start = match.start()
            break

    if inclusion_start is not None and exclusion_start is not None:
        inclusion = text[inclusion_start:exclusion_start].strip()
        exclusion = text[exclusion_start:].strip()
        exclusion = re.sub(
            r"^exclusion\s+criteria\s*:",
            "",
            exclusion,
            flags=re.IGNORECASE,
        ).strip()
        return inclusion or None, exclusion or None

    if inclusion_start is not None:
        inclusion = text[inclusion_start:].strip()
        return inclusion or None, None

    if exclusion_start is not None:
        exclusion = text[exclusion_start:].strip()
        exclusion = re.sub(
            r"^exclusion\s+criteria\s*:",
            "",
            exclusion,
            flags=re.IGNORECASE,
        ).strip()
        return None, exclusion or None

    return text, None


def _fetch_trial_sync(nct_id: str) -> dict:
    url = f"{CTGOV_API_BASE}/studies/{nct_id}"

    response = requests.get(
        url,
        headers={"Accept": "application/json"},
        timeout=30,
    )

    if response.status_code == 404:
        raise LookupError(f"No trial found for {nct_id}.")

    response.raise_for_status()
    return response.json()


async def fetch_trial(nct_id: str) -> dict:
    return await asyncio.to_thread(_fetch_trial_sync, nct_id)


def extract_trial_summary(study: dict) -> dict:
    protocol = study.get("protocolSection", {})
    identification = protocol.get("identificationModule", {})
    status = protocol.get("statusModule", {})
    conditions = protocol.get("conditionsModule", {})
    design = protocol.get("designModule", {})
    eligibility = protocol.get("eligibilityModule", {})

    nct_id = identification.get("nctId", "")
    criteria_text = eligibility.get("eligibilityCriteria")
    inclusion, exclusion = split_eligibility_criteria(criteria_text)

    healthy_volunteers = eligibility.get("healthyVolunteers")
    if isinstance(healthy_volunteers, str):
        healthy_volunteers = healthy_volunteers.upper() == "YES"

    return {
        "nct_id": nct_id,
        "brief_title": identification.get("briefTitle", "Untitled trial"),
        "official_title": identification.get("officialTitle"),
        "overall_status": status.get("overallStatus"),
        "phases": design.get("phases", []) or [],
        "conditions": conditions.get("conditions", []) or [],
        "eligibility": {
            "inclusion_criteria": inclusion,
            "exclusion_criteria": exclusion,
            "minimum_age": eligibility.get("minimumAge"),
            "maximum_age": eligibility.get("maximumAge"),
            "sex": eligibility.get("sex"),
            "healthy_volunteers": healthy_volunteers,
        },
        "ctgov_url": f"https://clinicaltrials.gov/study/{nct_id}",
    }
