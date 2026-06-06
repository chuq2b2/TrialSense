from condition_matching import condition_matches_disease, filter_match_keywords
from patients import PatientRecord


def apply_sql_prefilters(
    patients: list[PatientRecord],
    structured: dict,
) -> tuple[list[PatientRecord], list[dict]]:
    """Apply hard-rule pre-filters equivalent to SQL WHERE clauses."""
    filtered: list[PatientRecord] = []
    audit: list[dict] = []

    min_age = structured.get("min_age_years")
    max_age = structured.get("max_age_years")
    allowed_sex = (structured.get("allowed_sex") or "ALL").upper()
    requires_diagnosis = structured.get("requires_diagnosis", True)

    sql_rules = []
    for criterion in structured.get("criteria", []):
        rule = criterion.get("sql_prefilter")
        if rule:
            sql_rules.append(rule)

    for patient in patients:
        reasons: list[str] = []

        if min_age is not None and patient.age < min_age:
            reasons.append(f"Age {patient.age} below minimum {min_age}")
        if max_age is not None and patient.age > max_age:
            reasons.append(f"Age {patient.age} above maximum {max_age}")
        if allowed_sex not in {"ALL", ""} and patient.gender != allowed_sex:
            reasons.append(f"Sex {patient.gender} does not match required {allowed_sex}")
        if requires_diagnosis and patient.active_conditions == 0:
            reasons.append("No active conditions on record")

        for rule in sql_rules:
            rule_type = rule.get("type")
            if rule_type == "age_range":
                rule_min = rule.get("min")
                rule_max = rule.get("max")
                if rule_min is not None and patient.age < rule_min:
                    reasons.append(f"Age {patient.age} below {rule_min}")
                if rule_max is not None and patient.age > rule_max:
                    reasons.append(f"Age {patient.age} above {rule_max}")
            elif rule_type == "sex_allowed":
                allowed = (rule.get("allowed") or "ALL").upper()
                if allowed not in {"ALL", ""} and patient.gender != allowed:
                    reasons.append(f"Sex {patient.gender} not allowed")
            elif rule_type == "requires_condition":
                keywords = filter_match_keywords(rule.get("keywords", []))
                if keywords and not condition_matches_disease(
                    patient.conditions, keywords
                ):
                    reasons.append(
                        f"Missing required disease term(s): {', '.join(keywords)}"
                    )
            elif rule_type == "excludes_condition":
                keywords = filter_match_keywords(rule.get("keywords", []))
                if keywords and condition_matches_disease(
                    patient.conditions, keywords
                ):
                    reasons.append(
                        f"Has excluded disease term(s): {', '.join(keywords)}"
                    )

        if reasons:
            audit.append(
                {
                    "patient_id": patient.patient_id,
                    "passed": False,
                    "reasons": reasons,
                }
            )
        else:
            filtered.append(patient)
            audit.append({"patient_id": patient.patient_id, "passed": True, "reasons": []})

    return filtered, audit
