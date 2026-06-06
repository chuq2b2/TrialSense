CREATE TABLE IF NOT EXISTS patients (
    patient_id TEXT PRIMARY KEY,
    full_name TEXT NOT NULL DEFAULT '',
    city TEXT NOT NULL DEFAULT '',
    state TEXT NOT NULL DEFAULT '',
    age INTEGER NOT NULL,
    gender TEXT NOT NULL,
    active_conditions INTEGER NOT NULL DEFAULT 0,
    conditions_json TEXT NOT NULL DEFAULT '[]',
    condition_text TEXT NOT NULL DEFAULT '',
    medications_json TEXT NOT NULL DEFAULT '[]',
    bmi REAL,
    hba1c_pct REAL,
    glucose_mgdl REAL,
    systolic_bp REAL,
    diastolic_bp REAL,
    cholesterol_mgdl REAL,
    hospital_name TEXT NOT NULL,
    pcp_name TEXT NOT NULL DEFAULT '',
    pcp_contact TEXT NOT NULL DEFAULT ''
);

CREATE INDEX IF NOT EXISTS idx_patients_age ON patients (age);
CREATE INDEX IF NOT EXISTS idx_patients_gender ON patients (gender);
CREATE INDEX IF NOT EXISTS idx_patients_active_conditions ON patients (active_conditions);
