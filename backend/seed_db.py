#!/usr/bin/env python3
"""Load Synthea CSV patient data into SQLite or PostgreSQL."""

import json
from pathlib import Path

import psycopg

from config import DATABASE_URL
from database import get_backend
from patients import load_patients

SCHEMA_PG = Path(__file__).resolve().parent / "schema.sql"
SCHEMA_SQLITE = Path(__file__).resolve().parent / "schema_sqlite.sql"


def _patient_rows(patients):
    for patient in patients:
        yield {
            "patient_id": patient.patient_id,
            "full_name": patient.full_name,
            "city": patient.city,
            "state": patient.state,
            "age": patient.age,
            "gender": patient.gender,
            "active_conditions": patient.active_conditions,
            "conditions": patient.conditions,
            "conditions_json": json.dumps(patient.conditions),
            "condition_text": " | ".join(patient.conditions).lower(),
            "medications": patient.medications,
            "medications_json": json.dumps(patient.medications),
            "bmi": patient.bmi,
            "hba1c_pct": patient.hba1c_pct,
            "glucose_mgdl": patient.glucose_mgdl,
            "systolic_bp": patient.systolic_bp,
            "diastolic_bp": patient.diastolic_bp,
            "cholesterol_mgdl": patient.cholesterol_mgdl,
            "hospital_name": patient.hospital_name,
            "pcp_name": patient.pcp_name,
            "pcp_contact": patient.pcp_contact,
        }


def seed_sqlite(patients) -> None:
    import sqlite3

    from config import SQLITE_PATH

    SQLITE_PATH.parent.mkdir(parents=True, exist_ok=True)
    schema_sql = SCHEMA_SQLITE.read_text(encoding="utf-8")

    with sqlite3.connect(SQLITE_PATH) as conn:
        conn.executescript(schema_sql)
        for migration in (
            "ALTER TABLE patients ADD COLUMN pcp_name TEXT NOT NULL DEFAULT ''",
            "ALTER TABLE patients ADD COLUMN full_name TEXT NOT NULL DEFAULT ''",
            "ALTER TABLE patients ADD COLUMN city TEXT NOT NULL DEFAULT ''",
            "ALTER TABLE patients ADD COLUMN state TEXT NOT NULL DEFAULT ''",
        ):
            try:
                conn.execute(migration)
            except sqlite3.OperationalError:
                pass
        conn.execute("DELETE FROM patients")
        conn.executemany(
            """
            INSERT INTO patients (
                patient_id, full_name, city, state, age, gender, active_conditions,
                conditions_json, condition_text, medications_json,
                bmi, hba1c_pct, glucose_mgdl, systolic_bp, diastolic_bp,
                cholesterol_mgdl, hospital_name, pcp_name, pcp_contact
            ) VALUES (
                :patient_id, :full_name, :city, :state, :age, :gender, :active_conditions,
                :conditions_json, :condition_text, :medications_json,
                :bmi, :hba1c_pct, :glucose_mgdl, :systolic_bp, :diastolic_bp,
                :cholesterol_mgdl, :hospital_name, :pcp_name, :pcp_contact
            )
            """,
            list(_patient_rows(patients)),
        )
        conn.commit()


def seed_postgresql(patients) -> None:
    schema_sql = SCHEMA_PG.read_text(encoding="utf-8")
    with psycopg.connect(DATABASE_URL) as conn:
        with conn.cursor() as cur:
            cur.execute(schema_sql)
            cur.execute("TRUNCATE patients")
            cur.executemany(
                """
                INSERT INTO patients (
                    patient_id, full_name, city, state, age, gender,
                    active_conditions, conditions, condition_text, medications,
                    bmi, hba1c_pct, glucose_mgdl, systolic_bp, diastolic_bp,
                    cholesterol_mgdl, hospital_name, pcp_name, pcp_contact
                ) VALUES (
                    %(patient_id)s, %(full_name)s, %(city)s, %(state)s,
                    %(age)s, %(gender)s, %(active_conditions)s, %(conditions)s,
                    %(condition_text)s, %(medications)s, %(bmi)s, %(hba1c_pct)s,
                    %(glucose_mgdl)s, %(systolic_bp)s, %(diastolic_bp)s,
                    %(cholesterol_mgdl)s, %(hospital_name)s, %(pcp_name)s,
                    %(pcp_contact)s
                )
                """,
                list(_patient_rows(patients)),
            )
        conn.commit()


def main() -> None:
    patients = load_patients()
    backend = get_backend()

    if backend == "sqlite":
        seed_sqlite(patients)
    else:
        seed_postgresql(patients)

    print(f"Seeded {len(patients)} patients into {backend}.")


if __name__ == "__main__":
    main()
