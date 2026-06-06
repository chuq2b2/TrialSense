import csv
import re
from dataclasses import dataclass
from functools import lru_cache

from config import DATA_DIR


@dataclass
class PatientRecord:
    patient_id: str
    age: int
    gender: str
    conditions: list[str]
    active_conditions: int
    medications: list[str]
    bmi: float | None
    hba1c_pct: float | None
    glucose_mgdl: float | None
    systolic_bp: float | None
    diastolic_bp: float | None
    cholesterol_mgdl: float | None
    hospital_name: str
    pcp_name: str
    pcp_contact: str


def _parse_float(value: str) -> float | None:
    if not value or not str(value).strip():
        return None
    try:
        return float(value)
    except ValueError:
        return None


def _parse_int(value: str) -> int:
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return 0


def _split_pipe_list(value: str) -> list[str]:
    if not value or not str(value).strip():
        return []
    return [item.strip() for item in str(value).split("|") if item.strip()]


def _normalize_gender(value: str) -> str:
    value = (value or "").strip().upper()
    if value in {"M", "MALE"}:
        return "MALE"
    if value in {"F", "FEMALE"}:
        return "FEMALE"
    return value


@lru_cache(maxsize=1)
def _load_provider_contacts() -> dict[str, dict[str, str]]:
    contacts: dict[str, dict[str, str]] = {}

    provider_path = DATA_DIR / "patient_provider.csv"
    providers_path = DATA_DIR / "providers_clean.csv"

    provider_phones: dict[str, str] = {}
    with providers_path.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            provider_phones[row["PROVIDER_ID"]] = row.get("ORGANIZATION_PHONE", "")

    with provider_path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        for row in reader:
            patient_id = row["PATIENT_ID"]
            if patient_id in contacts:
                continue
            contacts[patient_id] = {
                "hospital_name": row.get("ORGANIZATION_NAME", "Unknown hospital"),
                "pcp_name": row.get("PROVIDER_NAME", ""),
                "pcp_contact": provider_phones.get(row.get("PROVIDER_ID", ""), ""),
            }

    return contacts


@lru_cache(maxsize=1)
def load_patients() -> list[PatientRecord]:
    contacts = _load_provider_contacts()
    patients: list[PatientRecord] = []
    master_path = DATA_DIR / "patient_master.csv"

    with master_path.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            patient_id = row["PATIENT_ID"]
            contact = contacts.get(
                patient_id,
                {"hospital_name": "Unknown hospital", "pcp_name": "", "pcp_contact": ""},
            )
            patients.append(
                PatientRecord(
                    patient_id=patient_id,
                    age=_parse_int(row.get("AGE", "0")),
                    gender=_normalize_gender(row.get("GENDER", "")),
                    conditions=_split_pipe_list(row.get("CONDITION_LIST", "")),
                    active_conditions=_parse_int(row.get("ACTIVE_CONDITIONS", "0")),
                    medications=_split_pipe_list(row.get("MEDICATION_LIST", "")),
                    bmi=_parse_float(row.get("BMI")),
                    hba1c_pct=_parse_float(row.get("HBA1C_PCT")),
                    glucose_mgdl=_parse_float(row.get("GLUCOSE_MGDL")),
                    systolic_bp=_parse_float(row.get("SYSTOLIC_BP")),
                    diastolic_bp=_parse_float(row.get("DIASTOLIC_BP")),
                    cholesterol_mgdl=_parse_float(row.get("CHOLESTEROL_MGDL")),
                    hospital_name=contact["hospital_name"],
                    pcp_name=contact["pcp_name"],
                    pcp_contact=contact["pcp_contact"],
                )
            )

    return patients


def patient_to_llm_summary(patient: PatientRecord, ref: str) -> dict:
    return {
        "ref": ref,
        "age": patient.age,
        "sex": patient.gender,
        "active_conditions": patient.active_conditions,
        "conditions": patient.conditions,
        "medications": patient.medications,
        "bmi": patient.bmi,
        "hba1c_pct": patient.hba1c_pct,
        "glucose_mgdl": patient.glucose_mgdl,
        "systolic_bp": patient.systolic_bp,
        "diastolic_bp": patient.diastolic_bp,
        "cholesterol_mgdl": patient.cholesterol_mgdl,
    }


def condition_matches(condition_list: list[str], keywords: list[str]) -> bool:
    from condition_matching import condition_matches as disease_match

    return disease_match(condition_list, keywords)


def parse_age_years(value: str | None) -> int | None:
    if not value:
        return None
    match = re.search(r"(\d+)", value)
    return int(match.group(1)) if match else None
