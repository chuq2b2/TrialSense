from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from typing import Literal

import psycopg
from psycopg.rows import dict_row

from condition_matching import filter_match_keywords
from config import DATABASE_URL, SQLITE_PATH
from patients import PatientRecord

DbBackend = Literal["sqlite", "postgresql"]


class DatabaseUnavailable(Exception):
    pass


def get_backend() -> DbBackend:
    if DATABASE_URL.startswith("sqlite"):
        return "sqlite"
    return "postgresql"


@contextmanager
def get_connection():
    if get_backend() == "sqlite":
        SQLITE_PATH.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(SQLITE_PATH)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()
        return

    with psycopg.connect(DATABASE_URL, row_factory=dict_row) as conn:
        yield conn


def _fetch_count() -> int:
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) AS count FROM patients")
        row = cur.fetchone()
        if get_backend() == "sqlite":
            return int(row[0])
        return int(row["count"])


def is_database_ready() -> bool:
    try:
        return _fetch_count() > 0
    except Exception:
        return False


def get_pool_size() -> int:
    return _fetch_count()


def get_data_source_label() -> str:
    return get_backend()


def _pname(key: str) -> str:
    return f":{key}" if get_backend() == "sqlite" else f"%({key})s"


def _like_clause(column: str, param_name: str, *, negated: bool = False) -> str:
    if get_backend() == "sqlite":
        operator = "NOT LIKE" if negated else "LIKE"
        return f"lower({column}) {operator} lower({_pname(param_name)})"
    operator = "NOT ILIKE" if negated else "ILIKE"
    return f"{column} {operator} {_pname(param_name)}"


def _row_to_patient(row) -> PatientRecord:
    if get_backend() == "sqlite":
        return PatientRecord(
            patient_id=row["patient_id"],
            age=row["age"],
            gender=row["gender"],
            conditions=json.loads(row["conditions_json"] or "[]"),
            active_conditions=row["active_conditions"],
            medications=json.loads(row["medications_json"] or "[]"),
            bmi=row["bmi"],
            hba1c_pct=row["hba1c_pct"],
            glucose_mgdl=row["glucose_mgdl"],
            systolic_bp=row["systolic_bp"],
            diastolic_bp=row["diastolic_bp"],
            cholesterol_mgdl=row["cholesterol_mgdl"],
            hospital_name=row["hospital_name"],
            pcp_contact=row["pcp_contact"],
        )

    return PatientRecord(
        patient_id=row["patient_id"],
        age=row["age"],
        gender=row["gender"],
        conditions=list(row["conditions"] or []),
        active_conditions=row["active_conditions"],
        medications=list(row["medications"] or []),
        bmi=row["bmi"],
        hba1c_pct=row["hba1c_pct"],
        glucose_mgdl=row["glucose_mgdl"],
        systolic_bp=row["systolic_bp"],
        diastolic_bp=row["diastolic_bp"],
        cholesterol_mgdl=row["cholesterol_mgdl"],
        hospital_name=row["hospital_name"],
        pcp_contact=row["pcp_contact"],
    )


def _collect_sql_rules(structured: dict) -> list[dict]:
    rules = []
    for criterion in structured.get("criteria", []):
        rule = criterion.get("sql_prefilter")
        if rule:
            rules.append(rule)
    return rules


def _fetch_rows(query: str, params: dict) -> list:
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute(query, params)
        rows = cur.fetchall()
        if get_backend() == "sqlite":
            return [dict(row) for row in rows]
        return rows


def _select_columns() -> str:
    if get_backend() == "sqlite":
        return """
            patient_id, age, gender, active_conditions,
            conditions_json, medications_json,
            bmi, hba1c_pct, glucose_mgdl, systolic_bp, diastolic_bp,
            cholesterol_mgdl, hospital_name, pcp_contact
        """
    return """
        patient_id, age, gender, active_conditions, conditions, medications,
        bmi, hba1c_pct, glucose_mgdl, systolic_bp, diastolic_bp,
        cholesterol_mgdl, hospital_name, pcp_contact
    """


def _overlap_expression(keywords: list[str], params: dict) -> str:
    if not keywords:
        return "0"

    cases = []
    for index, keyword in enumerate(keywords):
        key = f"overlap_{index}"
        if get_backend() == "sqlite":
            cases.append(
                f"CASE WHEN lower(condition_text) LIKE lower({_pname(key)}) THEN 1 ELSE 0 END"
            )
        else:
            cases.append(f"CASE WHEN condition_text ILIKE {_pname(key)} THEN 1 ELSE 0 END")
        params[key] = f"%{keyword}%"
    return " + ".join(cases)


def prefilter_patients_sql(
    structured: dict,
    *,
    limit: int,
) -> tuple[list[PatientRecord], int]:
    min_age = structured.get("min_age_years")
    max_age = structured.get("max_age_years")
    allowed_sex = (structured.get("allowed_sex") or "ALL").upper()
    requires_diagnosis = structured.get("requires_diagnosis", True)
    trial_conditions = structured.get("trial_conditions", [])

    required_keywords: list[str] = []
    excluded_keywords: list[str] = []
    for rule in _collect_sql_rules(structured):
        if rule.get("type") == "requires_condition":
            required_keywords.extend(rule.get("keywords", []))
        elif rule.get("type") == "excludes_condition":
            excluded_keywords.extend(rule.get("keywords", []))
        elif rule.get("type") == "age_range":
            if rule.get("min") is not None:
                min_age = rule["min"] if min_age is None else max(min_age, rule["min"])
            if rule.get("max") is not None:
                max_age = rule["max"] if max_age is None else min(max_age, rule["max"])
        elif rule.get("type") == "sex_allowed":
            allowed_sex = (rule.get("allowed") or allowed_sex).upper()

    overlap_keywords = (
        structured.get("match_terms")
        or filter_match_keywords(trial_conditions)
        or filter_match_keywords(required_keywords)
    )

    def build_query(where_clauses: list[str], base_params: dict) -> tuple[str, dict]:
        params = dict(base_params)
        overlap_expr = _overlap_expression(overlap_keywords, params)
        query = f"""
            SELECT {_select_columns()}, ({overlap_expr}) AS overlap_score
            FROM patients
            WHERE {" AND ".join(where_clauses)}
            ORDER BY overlap_score DESC, age ASC
            LIMIT {_pname("limit")}
        """
        return query, params

    params: dict = {"limit": limit}
    where_clauses = ["1=1"]

    if min_age is not None:
        where_clauses.append(f"age >= {_pname('min_age')}")
        params["min_age"] = min_age
    if max_age is not None:
        where_clauses.append(f"age <= {_pname('max_age')}")
        params["max_age"] = max_age
    if allowed_sex not in {"", "ALL"}:
        where_clauses.append(f"gender = {_pname('gender')}")
        params["gender"] = allowed_sex
    if requires_diagnosis:
        where_clauses.append("active_conditions > 0")

    for index, keyword in enumerate(filter_match_keywords(required_keywords)):
        key = f"required_{index}"
        where_clauses.append(_like_clause("condition_text", key))
        params[key] = f"%{keyword}%"

    for index, keyword in enumerate(filter_match_keywords(excluded_keywords)):
        key = f"excluded_{index}"
        where_clauses.append(_like_clause("condition_text", key, negated=True))
        params[key] = f"%{keyword}%"

    query, query_params = build_query(where_clauses, params)
    rows = _fetch_rows(query, query_params)
    patients = [_row_to_patient(row) for row in rows]
    if patients:
        return patients, len(patients)

    relaxed_where = ["1=1"]
    relaxed_params: dict = {"limit": limit}
    if min_age is not None:
        relaxed_where.append(f"age >= {_pname('min_age')}")
        relaxed_params["min_age"] = min_age
    if max_age is not None:
        relaxed_where.append(f"age <= {_pname('max_age')}")
        relaxed_params["max_age"] = max_age
    if allowed_sex not in {"", "ALL"}:
        relaxed_where.append(f"gender = {_pname('gender')}")
        relaxed_params["gender"] = allowed_sex

    query, query_params = build_query(relaxed_where, relaxed_params)
    rows = _fetch_rows(query, query_params)
    patients = [_row_to_patient(row) for row in rows]
    return patients, len(patients)
