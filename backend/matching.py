from criteria import extract_structured_criteria
from database import (
    DatabaseUnavailable,
    get_data_source_label,
    get_pool_size,
    is_database_ready,
    prefilter_patients_sql,
)
from condition_matching import condition_overlap_score
from patients import load_patients
from prefilter import apply_sql_prefilters
from scoring import rank_patients

MAX_SCORING_POOL = 10


def _prioritize_patients(patients: list, structured: dict) -> list:
    match_terms = structured.get("match_terms", [])
    if not match_terms:
        return patients

    def overlap_score(patient) -> int:
        return condition_overlap_score(patient.conditions, match_terms)

    return sorted(patients, key=overlap_score, reverse=True)


def _csv_fallback(structured: dict) -> tuple[list, int, int]:
    all_patients = load_patients()
    candidates, _audit = apply_sql_prefilters(all_patients, structured)
    scoring_pool = candidates if candidates else all_patients
    scoring_pool = _prioritize_patients(scoring_pool, structured)[:MAX_SCORING_POOL]
    return scoring_pool, len(all_patients), len(candidates)


def run_patient_matching(trial: dict) -> dict:
    structured = extract_structured_criteria(trial)
    data_source = "csv"

    try:
        if not is_database_ready():
            raise DatabaseUnavailable("Patient table is empty. Run: python seed_db.py")
        pool_size = get_pool_size()
        scoring_pool, prefilter_passed = prefilter_patients_sql(
            structured,
            limit=MAX_SCORING_POOL,
        )
        data_source = get_data_source_label()
    except DatabaseUnavailable:
        scoring_pool, pool_size, prefilter_passed = _csv_fallback(structured)

    ranked = rank_patients(
        structured=structured,
        patients=scoring_pool,
        batch_size=8,
        max_workers=1,
    )

    return {
        "structured_criteria": structured,
        "pool_size": pool_size,
        "prefilter_passed": prefilter_passed,
        "matches": ranked,
        "data_source": data_source,
    }
