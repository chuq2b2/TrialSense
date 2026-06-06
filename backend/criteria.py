import json
import re

from condition_matching import extract_match_terms, filter_match_keywords
from config import NEBIUS_SCORING_MODEL, USE_LLM_CRITERIA
from nebius_client import NebiusError, chat_json
from patients import parse_age_years

GROUP_WEIGHTS = {
    "hard_exclusion": 5,
    "core_inclusion": 3,
    "soft_preference": 1,
}

CRITERIA_SYSTEM_PROMPT = """You are a clinical trial eligibility analyst.
Extract trial eligibility into structured JSON for automated patient matching.

Rules:
- Split every criterion into exactly one group:
  - hard_exclusion (weight 5): age outside range, forbidden diagnoses, prohibited treatments, pregnancy, unsafe labs, etc.
  - core_inclusion (weight 3): required diagnosis, biomarker, line of therapy, organ function, ECOG, prior treatment history
  - soft_preference (weight 1): geography, visit burden, insurance, optional imaging/genomics
- Each criterion needs assessable_fields from: age, sex, conditions, medications, bmi, hba1c_pct, glucose_mgdl, systolic_bp, diastolic_bp, cholesterol_mgdl
- Add sql_prefilter when a hard rule can be checked without LLM:
  - age_below_min, age_above_max, sex_not_allowed
  - requires_condition (keyword list), excludes_condition (keyword list)
- For requires_condition keywords, use specific disease names from trial conditions only.
  Never use generic words alone (acute, chronic, disorder, disease, infection, etc.).
- Return ONLY valid JSON, no markdown."""


def _parse_eligibility_lines(text: str | None, group: str) -> list[dict]:
    if not text or not str(text).strip():
        return []

    criteria = []
    for index, raw_line in enumerate(str(text).splitlines()):
        line = re.sub(r"^[\*\-\u2022\d\.\)\s]+", "", raw_line.strip())
        if len(line) < 12:
            continue
        lowered = line.lower()
        if lowered.startswith(("inclusion criteria", "exclusion criteria", "key inclusion", "key exclusion")):
            continue

        criteria.append(
            {
                "id": f"{group}_line_{index}",
                "group": group,
                "description": line,
                "weight": GROUP_WEIGHTS[group],
                "assessable_fields": _infer_assessable_fields(line),
            }
        )
    return criteria


def _infer_assessable_fields(line: str) -> list[str]:
    lowered = line.lower()
    fields: list[str] = []

    if any(token in lowered for token in ("age", "year", "adult", "child", "infant", "elderly")):
        fields.append("age")
    if any(token in lowered for token in ("sex", "gender", "male", "female", "both sexes")):
        fields.append("sex")
    if any(
        token in lowered
        for token in ("diagnosis", "disorder", "disease", "cancer", "syndrome", "ptsd", "diabetes")
    ):
        fields.append("conditions")
    if any(token in lowered for token in ("medication", "therapy", "drug", "chemotherapy", "psychotherapy")):
        fields.append("medications")
    if any(token in lowered for token in ("bmi", "weight", "obesity", "overweight")):
        fields.append("bmi")
    if any(token in lowered for token in ("hba1c", "glucose", "a1c")):
        fields.extend(["hba1c_pct", "glucose_mgdl"])
    if any(token in lowered for token in ("blood pressure", "hypertension", "systolic", "diastolic")):
        fields.extend(["systolic_bp", "diastolic_bp"])
    if any(token in lowered for token in ("cholesterol", "lipid")):
        fields.append("cholesterol_mgdl")

    return list(dict.fromkeys(fields))


def _is_redundant_line(criterion: dict, existing: list[dict]) -> bool:
    description = criterion.get("description", "").lower()
    has_age_rule = any(
        item.get("id") == "age_range"
        or (item.get("sql_prefilter") or {}).get("type") == "age_range"
        for item in existing
    )
    if has_age_rule and any(
        token in description
        for token in ("aged ", "age ", "years of age", "adults aged", "between ")
    ):
        if re.search(r"\d+\s*(?:to|\-)\s*\d+\s*years", description) or re.search(
            r"aged\s+\d+", description
        ):
            return True

    has_sex_rule = any(item.get("id") == "sex_restriction" for item in existing)
    if has_sex_rule and any(
        token in description for token in ("both sexes", "male or female", "all sexes")
    ):
        return True

    return False


def _dedupe_criteria(criteria: list[dict]) -> list[dict]:
    deduped: list[dict] = []
    seen: set[str] = set()
    for criterion in criteria:
        key = f"{criterion.get('group')}::{criterion.get('description', '').strip().lower()}"
        if key in seen or _is_redundant_line(criterion, deduped):
            continue
        seen.add(key)
        deduped.append(criterion)
    return deduped


def _build_base_criteria(trial: dict) -> list[dict]:
    eligibility = trial.get("eligibility", {})
    min_age = parse_age_years(eligibility.get("minimum_age"))
    max_age = parse_age_years(eligibility.get("maximum_age"))
    sex = eligibility.get("sex") or "ALL"
    conditions = trial.get("conditions", [])

    criteria: list[dict] = []

    if min_age is not None or max_age is not None:
        criteria.append(
            {
                "id": "age_range",
                "group": "hard_exclusion",
                "description": f"Age {min_age or 'any'} to {max_age or 'any'} years",
                "weight": 5,
                "assessable_fields": ["age"],
                "sql_prefilter": {
                    "type": "age_range",
                    "min": min_age,
                    "max": max_age,
                },
            }
        )

    if sex and sex != "ALL":
        criteria.append(
            {
                "id": "sex_restriction",
                "group": "hard_exclusion",
                "description": f"Sex must be {sex}",
                "weight": 5,
                "assessable_fields": ["sex"],
                "sql_prefilter": {"type": "sex_allowed", "allowed": sex},
            }
        )

    if conditions:
        criteria.append(
            {
                "id": "primary_diagnosis",
                "group": "core_inclusion",
                "description": (
                    "Primary diagnosis related to trial condition(s): "
                    + ", ".join(conditions[:3])
                ),
                "weight": 3,
                "assessable_fields": ["conditions"],
                "criterion_type": "primary_diagnosis",
            }
        )

    criteria.extend(
        _parse_eligibility_lines(eligibility.get("inclusion_criteria"), "core_inclusion")
    )
    criteria.extend(
        _parse_eligibility_lines(eligibility.get("exclusion_criteria"), "hard_exclusion")
    )

    return _dedupe_criteria(criteria)


def extract_structured_criteria(trial: dict) -> dict:
    if not USE_LLM_CRITERIA:
        return _fallback_structured_criteria(trial)

    eligibility = trial.get("eligibility", {})
    payload = {
        "nct_id": trial.get("nct_id"),
        "brief_title": trial.get("brief_title"),
        "conditions": trial.get("conditions", []),
        "minimum_age": eligibility.get("minimum_age"),
        "maximum_age": eligibility.get("maximum_age"),
        "sex": eligibility.get("sex"),
        "healthy_volunteers": eligibility.get("healthy_volunteers"),
        "inclusion_criteria": eligibility.get("inclusion_criteria"),
        "exclusion_criteria": eligibility.get("exclusion_criteria"),
    }

    user_prompt = f"""Extract structured eligibility criteria from this trial:

{json.dumps(payload, indent=2)}

Return JSON with this shape:
{{
  "trial_conditions": ["string"],
  "min_age_years": 18,
  "max_age_years": 65,
  "allowed_sex": "ALL",
  "requires_diagnosis": true,
  "criteria": [
    {{
      "id": "c1",
      "group": "hard_exclusion",
      "description": "Age must be 18-65",
      "weight": 5,
      "assessable_fields": ["age"],
      "sql_prefilter": {{"type": "age_range", "min": 18, "max": 65}}
    }}
  ]
}}"""

    try:
        result = chat_json(
            system_prompt=CRITERIA_SYSTEM_PROMPT,
            user_prompt=user_prompt,
            model=NEBIUS_SCORING_MODEL,
        )
    except (NebiusError, Exception):
        return _fallback_structured_criteria(trial)

    if not isinstance(result, dict) or "criteria" not in result:
        return _fallback_structured_criteria(trial)

    _normalize_structured_criteria(result, trial)
    return result


def _fallback_structured_criteria(trial: dict) -> dict:
    eligibility = trial.get("eligibility", {})
    min_age = parse_age_years(eligibility.get("minimum_age"))
    max_age = parse_age_years(eligibility.get("maximum_age"))
    sex = eligibility.get("sex") or "ALL"
    conditions = trial.get("conditions", [])

    return {
        "trial_conditions": conditions,
        "match_terms": extract_match_terms(conditions),
        "min_age_years": min_age,
        "max_age_years": max_age,
        "allowed_sex": sex,
        "requires_diagnosis": not eligibility.get("healthy_volunteers", False),
        "criteria": _build_base_criteria(trial),
    }


def _normalize_structured_criteria(result: dict, trial: dict) -> None:
    eligibility = trial.get("eligibility", {})
    if result.get("min_age_years") is None:
        result["min_age_years"] = parse_age_years(eligibility.get("minimum_age"))
    if result.get("max_age_years") is None:
        result["max_age_years"] = parse_age_years(eligibility.get("maximum_age"))
    if not result.get("allowed_sex"):
        result["allowed_sex"] = eligibility.get("sex") or "ALL"
    if "requires_diagnosis" not in result:
        result["requires_diagnosis"] = not eligibility.get("healthy_volunteers", False)
    if not result.get("trial_conditions"):
        result["trial_conditions"] = trial.get("conditions", [])

    result["match_terms"] = extract_match_terms(result["trial_conditions"])

    llm_criteria = result.get("criteria", [])
    base_criteria = _build_base_criteria(trial)
    result["criteria"] = _dedupe_criteria(llm_criteria + base_criteria)

    for index, criterion in enumerate(result.get("criteria", []), start=1):
        criterion.setdefault("id", f"c{index}")
        criterion["weight"] = GROUP_WEIGHTS.get(
            criterion.get("group"), criterion.get("weight", 3)
        )
        rule = criterion.get("sql_prefilter") or {}
        if rule.get("type") in {"requires_condition", "excludes_condition"}:
            rule["keywords"] = filter_match_keywords(rule.get("keywords", []))
            criterion["sql_prefilter"] = rule
