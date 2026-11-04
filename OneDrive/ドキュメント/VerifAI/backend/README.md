# VerifAI – Phase 1: Backend & Machine Learning Engine

> **Tagline**: Verify opportunities. Protect your future.

VerifAI is an AI-powered job and internship scam risk detection platform developed for the Neural Storm hackathon.

This repository contains the complete **Phase 1: Backend and Machine Learning Development**, featuring real-time ML inference, an independent rule-based risk engine, PDF text extraction, and SQLite analysis history tracking.

---

## 1. System Architecture

```text
┌────────────────────────────────────────────────────────┐
│              Client (React / HTTP Client)              │
└───────────────────────────┬────────────────────────────┘
                            │ REST API (JSON / Multipart)
┌───────────────────────────▼────────────────────────────┐
│                    FastAPI Application                 │
│  ┌───────────────────────┐   ┌───────────────────────┐ │
│  │   /api/analyze/text   │   │   /api/analyze/file   │ │
│  └───────────┬───────────┘   └───────────┬───────────┘ │
│              │                           │             │
│              │                     PyMuPDF (fitz)      │
│              │                  (Text Extraction &     │
│              │                   Magic Byte Checking)  │
│              ▼                           ▼             │
│  ┌───────────────────────────────────────────────────┐ │
│  │               Analysis Coordination               │ │
│  └───────────────┬───────────────────┬───────────────┘ │
│                  │                   │                 │
│                  ▼                   ▼                 │
│  ┌───────────────────────┐   ┌───────────────────────┐ │
│  │ Machine Learning      │   │ Contextual Rule       │ │
│  │ Pipeline (TF-IDF +    │   │ Engine (Modular,      │ │
│  │ Calibrated LinearSVM) │   │ Negation-Aware)       │ │
│  └───────────┬───────────┘   └───────────┬───────────┘ │
│              │ (ML Score)                │ (Rule Score)│
│              └───────────┬───────────────┘             │
│                          ▼                             │
│              Composite Risk Assessment                 │
│                (LOW / MODERATE / HIGH)                 │
│                          │                             │
│                          ▼                             │
│              SQLite Persistence (SQLAlchemy)           │
│        (Privacy-conscious Preview, Hash & Result)      │
└────────────────────────────────────────────────────────┘
```

---

## 2. Machine Learning Pipeline

### Dataset
- **Dataset**: Employment Scam Aegean Dataset (EMSCAD).
- **Research Citation**: Vidros, S., Miniotas, C., Pedemonte, E., & Kolias, C. (2017). *A Method for the In-Depth, Real-Time Detection of Scam Job Advertisements*. Future Internet, 9(1), 6. [https://www.mdpi.com/1999-5903/9/1/6](https://www.mdpi.com/1999-5903/9/1/6).
- **Location**: `backend/ml/data/fake_job_postings.csv` (17,880 samples: 17,014 legitimate, 866 fraudulent).

### Model Configuration & Training
- **Text Features**: Concatenation of `title`, `company_profile`, `description`, `requirements`, and `benefits`.
- **Text Preprocessing**: HTML decoding/stripping, URL/email redaction, non-alphanumeric cleanup, whitespace normalization, lowercase conversion.
- **Stratified Split**: 80% Training, 20% Held-out Test (`random_state=42`, stratified on `fraudulent`).
- **Feature Extraction**:
  ```python
  TfidfVectorizer(
      max_features=30000,
      ngram_range=(1, 2),
      min_df=2,
      sublinear_tf=True,
      strip_accents="unicode"
  )
  ```
- **Algorithms Compared**:
  - TF-IDF + Logistic Regression (`class_weight="balanced"`)
  - TF-IDF + Calibrated Linear SVM (`class_weight="balanced"`, calibrated via `CalibratedClassifierCV`)
- **Model Selection**: Calibrated Linear SVM chosen based on stratified 3-fold cross-validation PR-AUC and F1 performance.
- **Evaluation Metrics (Held-out Test Set)**:
  - Accuracy: `98.52%`
  - Precision: `91.38%`
  - Recall: `74.13%`
  - F1-Score: `81.85%`
  - PR-AUC: `88.38%`
  - True Negatives: `3,013`, False Positives: `10`, False Negatives: `37`, True Positives: `106`

---

## 3. Contextual Rule-Based Risk Engine

Operates independently from ML inference and flags specific red flags with **strict negation and context handling**:
- **Registration Fee Demands**: Detects upfront onboarding or application charges.
- **Processing Fee Requirements**: Flags testing, screening, or interview costs.
- **Security Deposit Demands**: Detects laptop or caution money demands.
- **Payment Before Joining**: Flags demands to purchase training kits or licenses.
- **Guaranteed Selection**: Flags direct selection without technical interview or assessment.
- **Urgent Payment Deadlines**: Flags coercive artificial deadlines.
- **Unrealistic Salary Promises**: Flags exorbitant daily/hourly sums for unskilled typing/data entry.
- **Sensitive Document Demands**: Flags requests for credit card details, bank PINs, or original passports.

### Negation Handling Example
- `"Pay ₹2,500 as a registration fee to confirm your internship."` ➔ **Flagged (CRITICAL severity)**.
- `"There is no registration fee for this internship."` ➔ **Suppressed (Zero risk score)**.
- `"Disclaimer: We never ask candidates for any processing fee or payment."` ➔ **Suppressed**.

---

## 4. Setup and Installation (Windows PowerShell)

Ensure Python 3.11+ is installed.

```powershell
# Navigate to the backend directory
cd backend

# Create Python virtual environment
py -3.11 -m venv .venv

# Activate the virtual environment
.venv\Scripts\Activate.ps1

# Install dependencies
python -m pip install -r requirements.txt
```

---

## 5. Model Training & Evaluation

The training script automatically loads the dataset, cleans the text, runs stratified cross-validation, selects the optimal classifier, evaluates on the held-out test split, and writes `model.joblib` and `metrics.json`.

```powershell
# Run training pipeline
python ml/train.py
```

Saved artifacts:
- `backend/ml/saved_model/model.joblib` (Trained pipeline)
- `backend/ml/saved_model/metrics.json` (Real evaluation metrics)

---

## 6. Starting the FastAPI Server

```powershell
# Start FastAPI development server with hot reload
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Once running:
- **Interactive Swagger UI**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **ReDoc API Documentation**: [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)
- **Health Endpoint**: [http://127.0.0.1:8000/api/health](http://127.0.0.1:8000/api/health)

---

## 7. Running the Test Suite

Execute the comprehensive Pytest suite:

```powershell
# Run all automated tests
pytest -p no:anyio -v
```

To run a specific test module:

```powershell
pytest -p no:anyio tests/test_health.py -v
pytest -p no:anyio tests/test_prediction.py -v
pytest -p no:anyio tests/test_risk_engine.py -v
pytest -p no:anyio tests/test_analysis.py -v
pytest -p no:anyio tests/test_history.py -v
pytest -p no:anyio tests/test_metrics.py -v
```

---

## 8. REST API Reference

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/health` | Backend status, database connection, and ML model availability. |
| `POST` | `/api/analyze/text` | Analyzes recruitment text, runs ML inference + rules, stores history. |
| `POST` | `/api/analyze/file` | Accepts PDF (up to 10 MB), extracts text via PyMuPDF, runs analysis. |
| `GET` | `/api/history` | Returns paginated list of past analyses (newest first). |
| `GET` | `/api/history/{id}` | Returns full details of an individual analysis record. |
| `DELETE` | `/api/history/{id}` | Permanently deletes an analysis record from SQLite. |
| `GET` | `/api/model/metrics` | Returns actual held-out test evaluation metrics. |

### Mandatory Legal Disclaimer
Every analysis response includes:
> *"VerifAI provides automated risk assessments based on submitted content. It does not verify employer identity or establish that an organisation is fraudulent. Always independently verify recruitment opportunities before sharing money or sensitive information."*

---

## 9. Environment Configuration

Copy `.env.example` to `.env` to customize settings:

```ini
APP_NAME=VerifAI
APP_ENV=development
DEBUG=True
PORT=8000
HOST=0.0.0.0
CORS_ORIGINS=http://localhost:3000,http://localhost:5173,http://127.0.0.1:3000,http://127.0.0.1:5173
DATABASE_URL=sqlite:///./verifai.db
MODEL_PATH=ml/saved_model/model.joblib
METRICS_PATH=ml/saved_model/metrics.json
MAX_UPLOAD_SIZE_MB=10
```

---

## 10. Known Limitations & Next Steps

1. **Scanned / Image-Only PDFs**: Text extraction is currently digital-native via PyMuPDF. Pure scanned image PDFs return an informative `422 Unprocessable Content` advising the user that OCR is slated for a future phase.
2. **Frontend Integration**: Phase 1 is strictly backend. Phase 2 will implement the React/Tailwind frontend dashboard.
