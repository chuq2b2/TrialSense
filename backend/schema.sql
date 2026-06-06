CREATE TABLE IF NOT EXISTS patients (
    patient_id TEXT PRIMARY KEY,
    age INTEGER NOT NULL,
    gender TEXT NOT NULL,
    active_conditions INTEGER NOT NULL DEFAULT 0,
    conditions TEXT[] NOT NULL DEFAULT '{}',
    condition_text TEXT NOT NULL DEFAULT '',
    medications TEXT[] NOT NULL DEFAULT '{}',
    bmi DOUBLE PRECISION,
    hba1c_pct DOUBLE PRECISION,
    glucose_mgdl DOUBLE PRECISION,
    systolic_bp DOUBLE PRECISION,
    diastolic_bp DOUBLE PRECISION,
    cholesterol_mgdl DOUBLE PRECISION,
    hospital_name TEXT NOT NULL,
    pcp_name TEXT NOT NULL DEFAULT '',
    pcp_contact TEXT NOT NULL DEFAULT ''
);

CREATE INDEX IF NOT EXISTS idx_patients_age ON patients (age);
CREATE INDEX IF NOT EXISTS idx_patients_gender ON patients (gender);
CREATE INDEX IF NOT EXISTS idx_patients_active_conditions ON patients (active_conditions);
