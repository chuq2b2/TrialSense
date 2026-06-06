import json
import re
from concurrent.futures import ThreadPoolExecutor, as_completed

from condition_matching import (
    GENERIC_TERMS,
    condition_matches_disease,
    filter_match_keywords,
)
from config import NEBIUS_SCORING_MODEL, USE_LLM_SCORING
from nebius_client import NebiusError, chat_json
from patients import PatientRecord, patient_to_llm_summary

GROUP_WEIGHTS = {
    "hard_exclusion": 5,
    "core_inclusion": 3,
    "soft_preference": 1,
}

MATCH_BANDS = [
    (90, 100, "Strong match"),
    (75, 89, "Good match"),
    (50, 74, "Possible match; review manually"),
    (1, 49, "Poor match"),
    (0, 0, "Ineligible or blocked by exclusion"),
]

SCORING_SYSTEM_PROMPT = """You are a clinical trial eligibility scoring engine.
Score conservatively — only use "1" when clearly met, "0" when clearly not met.
Use "0.5" for partial evidence and "U" when patient data cannot answer the criterion.
Return ONLY valid JSON array, no markdown."""


def match_band(score: float) -> str:
    rounded = round(score)
    for low, high, label in MATCH_BANDS:
        if low <= rounded <= high:
            return label
    return "Possible match; review manually"


def _patient_can_assess(fields: list[str], patient: PatientRecord) -> bool:
    checks = {
        "age": True,
        "sex": bool(patient.gender),
        "conditions": bool(patient.conditions),
        "medications": bool(patient.medications),
        "bmi": patient.bmi is not None,
        "hba1c_pct": patient.hba1c_pct is not None,
        "glucose_mgdl": patient.glucose_mgdl is not None,
        "systolic_bp": patient.systolic_bp is not None,
        "diastolic_bp": patient.diastolic_bp is not None,
        "cholesterol_mgdl": patient.cholesterol_mgdl is not None,
    }
    return any(checks.get(field, False) for field in fields)


def _description_keywords(description: str) -> list[str]:
    words = re.findall(r"[a-z]{5,}", description.lower())
    return [w for w in words if w not in GENERIC_TERMS][:8]


def _conditions_support_description(
    description: str,
    patient_conditions: list[str],
    match_terms: list[str],
) -> bool:
    if condition_matches_disease(patient_conditions, match_terms):
        return True

    keywords = _description_keywords(description)
    if not keywords:
        return False

    for condition in patient_conditions:
        condition_lower = condition.lower()
        hits = sum(1 for keyword in keywords if keyword in condition_lower)
        if hits >= min(2, len(keywords)):
            return True
    return False


def _conditions_violate_description(
    description: str,
    patient_conditions: list[str],
) -> bool:
    keywords = _description_keywords(description)
    if not keywords:
        return False
    for condition in patient_conditions:
        condition_lower = condition.lower()
        if any(keyword in condition_lower for keyword in keywords):
            return True
    return False


def _score_single_criterion(
    criterion: dict,
    patient: PatientRecord,
    structured: dict,
) -> dict:
    fields = criterion.get("assessable_fields", [])
    group = criterion.get("group")
    rule = criterion.get("sql_prefilter") or {}
    description = criterion.get("description", "")
    match_terms = structured.get("match_terms", [])
    allowed_sex = (structured.get("allowed_sex") or "ALL").upper()
    min_age = structured.get("min_age_years")
    max_age = structured.get("max_age_years")

    score = "U"
    assessable = False
    reason = "Insufficient patient data to assess"
    manual_review = False

    if not _patient_can_assess(fields, patient):
        return {
            "criterion_id": criterion["id"],
            "score": "U",
            "assessable": False,
            "reason": reason,
            "manual_review": True,
        }

    assessable = True

    if "age" in fields and (rule.get("type") == "age_range" or min_age is not None or max_age is not None):
        rule_min = rule.get("min", min_age)
        rule_max = rule.get("max", max_age)
        in_range = True
        if rule_min is not None and patient.age < rule_min:
            in_range = False
        if rule_max is not None and patient.age > rule_max:
            in_range = False
        if group == "hard_exclusion":
            score = "0" if not in_range else "1"
            reason = "Outside age range" if not in_range else "Within age range"
        else:
            score = "1" if in_range else "0"
            reason = f"Age {patient.age}"
        return {
            "criterion_id": criterion["id"],
            "score": score,
            "assessable": True,
            "reason": reason,
            "manual_review": False,
        }

    if "sex" in fields:
        if allowed_sex in {"", "ALL"}:
            score = "1"
            reason = "No sex restriction"
        else:
            matches = patient.gender == allowed_sex
            if group == "hard_exclusion":
                score = "0" if not matches else "1"
            else:
                score = "1" if matches else "0"
            reason = f"Patient sex {patient.gender}"
        return {
            "criterion_id": criterion["id"],
            "score": score,
            "assessable": True,
            "reason": reason,
            "manual_review": False,
        }

    if criterion.get("criterion_type") == "primary_diagnosis" or (
        "conditions" in fields and rule.get("type") == "requires_condition"
    ):
        keywords = filter_match_keywords(rule.get("keywords", [])) or match_terms
        matched = condition_matches_disease(patient.conditions, keywords)
        score = "1" if matched else "0"
        reason = "Primary diagnosis supported" if matched else "Primary diagnosis not supported"
        return {
            "criterion_id": criterion["id"],
            "score": score,
            "assessable": True,
            "reason": reason,
            "manual_review": False,
        }

    if "conditions" in fields and rule.get("type") == "excludes_condition":
        keywords = filter_match_keywords(rule.get("keywords", []))
        matched = condition_matches_disease(patient.conditions, keywords)
        score = "0" if matched else "1"
        reason = "Excluded disease present" if matched else "Excluded disease absent"
        return {
            "criterion_id": criterion["id"],
            "score": score,
            "assessable": True,
            "reason": reason,
            "manual_review": False,
        }

    if "conditions" in fields:
        if group == "hard_exclusion":
            violated = _conditions_violate_description(description, patient.conditions)
            score = "0" if violated else "1"
            reason = "Exclusion condition present" if violated else "Exclusion condition absent"
        else:
            supported = _conditions_support_description(
                description, patient.conditions, match_terms
            )
            score = "1" if supported else "0"
            reason = "Criterion supported by conditions" if supported else "Criterion not supported"
        return {
            "criterion_id": criterion["id"],
            "score": score,
            "assessable": True,
            "reason": reason,
            "manual_review": score == "0",
        }

    if "medications" in fields:
        keywords = _description_keywords(description)
        if not keywords:
            return {
                "criterion_id": criterion["id"],
                "score": "U",
                "assessable": False,
                "reason": "Medication criterion not assessable from available data",
                "manual_review": True,
            }
        med_text = " ".join(patient.medications).lower()
        matched = any(keyword in med_text for keyword in keywords)
        if group == "hard_exclusion":
            score = "0" if matched else "1"
            reason = "Excluded medication present" if matched else "Excluded medication absent"
        else:
            score = "1" if matched else "0"
            reason = "Required medication evidence found" if matched else "Required medication evidence missing"
        return {
            "criterion_id": criterion["id"],
            "score": score,
            "assessable": True,
            "reason": reason,
            "manual_review": score in {"0", "0.5"},
        }

    return {
        "criterion_id": criterion["id"],
        "score": "U",
        "assessable": False,
        "reason": reason,
        "manual_review": True,
    }


def calculate_match_percent(
    criteria: list[dict],
    criterion_scores: list[dict],
    *,
    patient: PatientRecord | None = None,
    structured: dict | None = None,
) -> tuple[float, bool, list[str]]:
    score_map = {item["criterion_id"]: item for item in criterion_scores}
    exclusion_reasons: list[str] = []

    for criterion in criteria:
        if criterion.get("group") != "hard_exclusion":
            continue
        entry = score_map.get(criterion["id"])
        if not entry and patient and structured:
            entry = _score_single_criterion(criterion, patient, structured)
        if not entry:
            continue
        score = str(entry.get("score", "U")).upper()
        assessable = entry.get("assessable", False)
        if assessable and score == "0":
            exclusion_reasons.append(
                entry.get("reason") or criterion.get("description", "")
            )

    if exclusion_reasons:
        return 0.0, True, exclusion_reasons

    weighted_score = 0.0
    weighted_assessable = 0.0
    needs_review = False
    assessed_count = 0

    for criterion in criteria:
        entry = score_map.get(criterion["id"])
        if not entry and patient and structured:
            entry = _score_single_criterion(criterion, patient, structured)

        weight = criterion.get("weight", GROUP_WEIGHTS.get(criterion.get("group"), 3))

        if not entry:
            if patient and structured and _patient_can_assess(
                criterion.get("assessable_fields", []), patient
            ):
                entry = {
                    "score": "0",
                    "assessable": True,
                    "manual_review": True,
                }
            else:
                needs_review = True
                continue

        score = str(entry.get("score", "U")).upper()
        assessable = entry.get("assessable", False)

        if score == "U" or not assessable:
            needs_review = True
            continue

        assessed_count += 1
        if entry.get("manual_review"):
            needs_review = True

        si = {"1": 1.0, "0.5": 0.5, "0": 0.0}.get(score, 0.0)
        weighted_score += weight * si
        weighted_assessable += weight

    if weighted_assessable == 0:
        return 0.0, True, []

    percent = round(100 * weighted_score / weighted_assessable, 1)
    if assessed_count < max(1, len(criteria) // 3):
        needs_review = True
    if percent < 90 or assessed_count < len(criteria):
        needs_review = True
    return percent, needs_review, []


def _heuristic_scores(
    structured: dict,
    patients: list[PatientRecord],
    refs: list[str],
) -> list[dict]:
    criteria = structured.get("criteria", [])
    results = []
    for patient, ref in zip(patients, refs, strict=True):
        scores = [
            _score_single_criterion(criterion, patient, structured)
            for criterion in criteria
        ]
        results.append({"ref": ref, "criteria_scores": scores})
    return results


def score_patient_batch(
    *,
    structured: dict,
    patients: list[PatientRecord],
    refs: list[str],
) -> list[dict]:
    criteria = structured.get("criteria", [])
    if not criteria or not patients:
        return []

    heuristic = _heuristic_scores(structured, patients, refs)
    if not USE_LLM_SCORING:
        return heuristic

    summaries = [
        patient_to_llm_summary(patient, ref)
        for patient, ref in zip(patients, refs, strict=True)
    ]
    user_prompt = f"""Score these patients conservatively against ALL criteria.
Use "0" when inclusion is not clearly met. Use "U" only when data is truly missing.

Criteria:
{json.dumps(criteria, indent=2)}

Patients:
{json.dumps(summaries, indent=2)}

Return JSON array with one entry per patient and scores for every criterion id."""

    try:
        llm_result = chat_json(
            system_prompt=SCORING_SYSTEM_PROMPT,
            user_prompt=user_prompt,
            model=NEBIUS_SCORING_MODEL,
            temperature=0.0,
        )
    except (NebiusError, Exception):
        return heuristic

    if not isinstance(llm_result, list):
        return heuristic

    return _merge_scores(heuristic, llm_result, criteria)


def _merge_scores(
    heuristic: list[dict],
    llm_result: list[dict],
    criteria: list[dict],
) -> list[dict]:
    heuristic_by_ref = {item["ref"]: item for item in heuristic}
    llm_by_ref = {item["ref"]: item for item in llm_result if item.get("ref")}
    merged: list[dict] = []

    score_rank = {"0": 0, "0.5": 1, "U": 2, "1": 3}

    for ref, heuristic_entry in heuristic_by_ref.items():
        llm_entry = llm_by_ref.get(ref, {})
        llm_map = {
            item["criterion_id"]: item
            for item in llm_entry.get("criteria_scores", [])
        }
        combined_scores = []
        for criterion in criteria:
            h = next(
                (
                    item
                    for item in heuristic_entry.get("criteria_scores", [])
                    if item["criterion_id"] == criterion["id"]
                ),
                None,
            )
            l = llm_map.get(criterion["id"])
            if h and l and h.get("assessable") and l.get("assessable"):
                h_score = str(h.get("score", "U"))
                l_score = str(l.get("score", "U"))
                final_score = h_score if score_rank.get(h_score, 2) <= score_rank.get(l_score, 2) else l_score
                combined_scores.append({**h, "score": final_score, "manual_review": final_score in {"0", "0.5", "U"}})
            else:
                combined_scores.append(h or l or {
                    "criterion_id": criterion["id"],
                    "score": "U",
                    "assessable": False,
                    "reason": "Not scored",
                    "manual_review": True,
                })
        merged.append({"ref": ref, "criteria_scores": combined_scores})
    return merged


def rank_patients(
    *,
    structured: dict,
    patients: list[PatientRecord],
    batch_size: int = 8,
    max_workers: int = 1,
) -> list[dict]:
    criteria = structured.get("criteria", [])
    if not patients:
        return []

    batches: list[tuple[int, list[PatientRecord], list[str]]] = []
    for start in range(0, len(patients), batch_size):
        batch = patients[start : start + batch_size]
        refs = [f"P{start + index + 1}" for index in range(len(batch))]
        batches.append((start, batch, refs))

    batch_results: dict[int, list[dict]] = {}
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(
                score_patient_batch,
                structured=structured,
                patients=batch,
                refs=refs,
            ): (start, batch, refs)
            for start, batch, refs in batches
        }
        for future in as_completed(futures):
            start, batch, refs = futures[future]
            try:
                batch_results[start] = future.result()
            except Exception:
                batch_results[start] = _heuristic_scores(structured, batch, refs)

    ranked: list[dict] = []
    for start, batch, refs in batches:
        batch_scores = batch_results.get(start, [])
        score_by_ref = {item["ref"]: item for item in batch_scores}
        for patient, ref in zip(batch, refs, strict=True):
            entry = score_by_ref.get(ref, {"criteria_scores": []})
            percent, needs_review, exclusion_reasons = calculate_match_percent(
                criteria,
                entry.get("criteria_scores", []),
                patient=patient,
                structured=structured,
            )
            organization_phone = patient.pcp_contact or "Contact unavailable"
            ranked.append(
                {
                    "match_percent": percent,
                    "match_band": match_band(percent),
                    "hospital_name": patient.hospital_name,
                    "pcp_name": patient.pcp_name or "PCP unavailable",
                    "organization_phone": organization_phone,
                    "pcp_contact": organization_phone,
                    "exclusion_reasons": exclusion_reasons,
                    "needs_manual_review": needs_review,
                }
            )

    ranked.sort(key=lambda item: item["match_percent"], reverse=True)
    return ranked
