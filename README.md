Problem: Clinical trial patient recruitment has long been a signficant challenge. Failure to enroll patient is one of the leading cause of clinical trial dealy. Recruitmnet process remain highly manual, involves ingesting patient health records, matching complex medical data against trial inclusion/exclusion criteria, and routing verified candidates for human review and informed consent

Around 80% of trials fail to meet the initial enrollment target and timeline, and these delays can result in lost revenue of as much as US $8 million per day for drug developing companies.

Solution: TrialSense, an AI-Powered EHR-intergrated platform that automatically identifies, scores, and presents the most eligible patients for any clinical trial.

Here is codebase for TrialSense, using public synthetic patient dataset of 111 patients with different diseases (https://synthea.mitre.org/) and public clinical trial ([clinialtrial.gov](https://clinicaltrials.gov/)). We use Cursor to assist with building code for LLM model for clinical trial matching, and Nebius to run the AI model. 

# Run it locally

1. Terminal 1: backend:

```
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

Or from the repo root:

```
pip install -r backend/requirements.txt
uvicorn main:app --reload --port 8000
```

If We have changes to the database scheme
```
python3 seed_db.py
```

2. Terminal 2 — frontend:

```
cd frontend
npm i
npm run dev
```
