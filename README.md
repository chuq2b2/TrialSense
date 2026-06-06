

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

2. Terminal 2 — frontend:

```
cd frontend
npm i
npm run dev
```
