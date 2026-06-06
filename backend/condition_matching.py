import re

# Terms too generic to use alone for disease matching
GENERIC_TERMS = {
    "acute",
    "chronic",
    "mild",
    "moderate",
    "severe",
    "primary",
    "secondary",
    "disorder",
    "disorders",
    "disease",
    "diseases",
    "condition",
    "conditions",
    "finding",
    "findings",
    "situation",
    "therapy",
    "treatment",
    "patient",
    "patients",
    "adult",
    "adults",
    "pediatric",
    "active",
    "inactive",
    "unspecified",
    "other",
    "history",
    "status",
    "syndrome",
    "infection",
    "infections",
    "viral",
    "bacterial",
    "symptom",
    "symptoms",
    "pain",
    "related",
    "due",
    "with",
    "without",
    "type",
    "stage",
    "phase",
    "recurrent",
    "relapsed",
    "refractory",
    "advanced",
    "metastatic",
    "localized",
    "general",
    "local",
    "systemic",
    "post",
    "term",
    "terms",
    "stress",
}


def _normalize_phrase(value: str) -> str:
    value = value.strip().lower()
    value = value.replace("_", " ")
    value = re.sub(r"\s+", " ", value)
    return value


def is_meaningful_keyword(keyword: str) -> bool:
    token = _normalize_phrase(keyword)
    if not token:
        return False
    if " " in token or "-" in token:
        words = re.split(r"[\s\-]+", token)
        content_words = [w for w in words if w not in GENERIC_TERMS and len(w) >= 3]
        if content_words:
            return True
        return len(words) >= 2 and any(len(w) >= 4 for w in words)
    return len(token) >= 5 and token not in GENERIC_TERMS


def _significant_tokens(phrase: str) -> list[str]:
    words = re.split(r"[\s\-/,]+", phrase.lower())
    return [w for w in words if len(w) >= 5 and w not in GENERIC_TERMS]


def extract_match_terms(trial_conditions: list[str]) -> list[str]:
    """Build disease-relevant match terms from CT.gov trial condition labels."""
    terms: list[str] = []
    seen: set[str] = set()

    def add(term: str) -> None:
        normalized = _normalize_phrase(term)
        if not normalized or normalized in seen:
            return
        if is_meaningful_keyword(normalized):
            seen.add(normalized)
            terms.append(normalized)

    for condition in trial_conditions:
        if not condition or not str(condition).strip():
            continue
        for part in re.split(r"[,;/]+", str(condition)):
            phrase = _normalize_phrase(part)
            if not phrase:
                continue
            add(phrase)
            for token in _significant_tokens(phrase):
                add(token)

    return terms


def filter_match_keywords(keywords: list[str]) -> list[str]:
    filtered: list[str] = []
    seen: set[str] = set()
    for keyword in keywords:
        normalized = _normalize_phrase(keyword)
        if not normalized or normalized in seen:
            continue
        if is_meaningful_keyword(normalized):
            seen.add(normalized)
            filtered.append(normalized)
    return filtered


def term_matches_patient(patient_conditions: list[str], term: str) -> bool:
    term = _normalize_phrase(term)
    if not term or not is_meaningful_keyword(term):
        return False

    for condition in patient_conditions:
        condition_lower = condition.lower()
        if " " in term or "-" in term:
            if term in condition_lower:
                return True
            continue
        if re.search(rf"\b{re.escape(term)}\b", condition_lower):
            return True
    return False


def condition_overlap_score(
    patient_conditions: list[str],
    match_terms: list[str],
) -> int:
    return sum(
        1 for term in match_terms if term_matches_patient(patient_conditions, term)
    )


def condition_matches_disease(
    patient_conditions: list[str],
    match_terms: list[str],
) -> bool:
    if not match_terms:
        return False
    return condition_overlap_score(patient_conditions, match_terms) > 0


def condition_matches(
    patient_conditions: list[str],
    keywords: list[str],
) -> bool:
    meaningful = filter_match_keywords(keywords)
    if not meaningful:
        return False
    return condition_matches_disease(patient_conditions, meaningful)
