# Car Dealer Lead Processing Automation — Solution

## Overview

A production-grade automation system that processes car dealer leads through a complete pipeline:
**Ingestion → Validation → File Enrichment → API Enrichment → Scoring → Routing → Storage**

---

## Quick Start

```bash
docker-compose up --build
```

The application will be available at `http://localhost:8000`.

---

## Architecture


### Components

| Module | Responsibility |
|--------|---------------|
| `src/main.py` | FastAPI app, endpoints, startup lifecycle |
| `src/models.py` | Pydantic data models for the entire pipeline |
| `src/validation.py` | Email/phone/required field validation |
| `src/file_loader.py` | Parse branch_config.xlsx and car_models.txt |
| `src/enrichment.py` | External API client with retry logic |
| `src/scoring.py` | Lead scoring engine (0-100 points) |
| `src/routing.py` | HOT/WARM/COLD routing logic |
| `src/database.py` | SQLite async persistence |
| `src/pipeline.py` | Pipeline orchestrator (OOP) |
| `src/logger.py` | Structured JSON logging |

---

## API Documentation

### POST /api/leads
Submit a lead for processing.

**Request:**
```json
{
  "BranchID": "400",
  "WorkerCode": "910290",
  "AskedCar": "90962_101",
  "FirstName": "דני",
  "LastName": "כהן",
  "Email": "danny.cohen@gmail.com",
  "Phone": "0542100319",
  "FromWebSite": "forthing",
  "Area": "1"
}
```

**Success Response (202):**
```json
{
  "lead_id": "uuid",
  "status": "accepted",
  "message": "Lead accepted and processed successfully",
  "score": 90,
  "priority": "HOT",
  "assigned_to": "David Cohen"
}
```

**Validation Error (422):**
```json
{
  "lead_id": "uuid",
  "status": "rejected",
  "message": "Lead validation failed",
  "errors": ["At least one valid contact method required..."]
}
```

### GET /api/leads
List all processed leads (paginated).

### GET /api/leads/{lead_id}
Retrieve a specific processed lead with full enrichment data.

### GET /health
Health check — returns number of branches and cars loaded.

---

## Sample Curl Commands

**Submit a valid lead:**
```bash
curl -X POST http://localhost:8000/api/leads \
  -H "Content-Type: application/json" \
  -d '{
    "BranchID": "400",
    "WorkerCode": "910290",
    "AskedCar": "90962_101",
    "FirstName": "Danny",
    "LastName": "Cohen",
    "Email": "danny.cohen@gmail.com",
    "Phone": "0542100319",
    "FromWebSite": "forthing",
    "Area": "1"
  }'
```

**Health check:**
```bash
curl http://localhost:8000/health
```

**List all leads:**
```bash
curl http://localhost:8000/api/leads
```

---

## Design Decisions

### 1. OOP Pipeline
בחרתי לעטוף את הפייפליין במחלקה `LeadPipeline` במקום פונקציות נפרדות.
הנתונים העסקיים (branches, cars) נטענים פעם אחת ב-`__init__` ומשותפים לכל הבקשות — בלי להעביר פרמטרים בכל קריאה.

### 2. SQLite
נבחר לזירו-קונפיג. אין צורך ב-container נוסף. בסביבת production היינו משתמשים ב-PostgreSQL.

### 3. structlog
JSON-formatted structured logging לפרסור קל בסביבת containers. כל שלב בפייפליין מתועד עם lead_id, stage, status.

### 4. httpx + tenacity
קריאות HTTP אסינכרוניות עם 3 retries ו-exponential backoff (1s → 2s → 4s). הפייפליין ממשיך גם אם ה-API נכשל לחלוטין.

### 5. Startup Caching
קבצי ה-Excel וה-txt נטענים פעם אחת בעליית השרת — לא בכל בקשה.

---

## Scoring Logic

| Source | Condition | Points |
|--------|-----------|--------|
| API | lead_priority = "High" | +40 |
| API | lead_priority = "Medium" | +20 |
| API | email_insights.trust_level = "High" | +20 |
| API | phone_insights.verified = true | +20 |
| File | car category = "Luxury" | +20 |
| File | car category = "Electric" | +15 |
| File | car availability = "In Stock" | +10 |

**Max score: 100**

## Routing Rules

| Score | Priority | Assigned To |
|-------|----------|-------------|
| ≥ 70 | HOT 🔥 | Branch Manager |
| 40–69 | WARM | Worker (WorkerCode) |
| < 40 | COLD | General Pool |

---

## CI/CD — GitHub Actions

הפרויקט כולל GitHub Actions workflow שרץ אוטומטית בכל push:

push to GitHub
↓
GitHub Actions:

Install dependencies
Run pytest (unit tests)
Verify Docker build


הקובץ נמצא ב: `.github/workflows/ci.yml`

### Unit Tests
```bash
pip install pytest
pytest tests/
```

הטסטים בודקים:
- ולידציה של אימייל (פורמט, דומיינים חד פעמיים)
- ולידציה של טלפון ישראלי
- ולידציה של ליד מלא