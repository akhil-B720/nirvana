# NIRVANA — System Architecture

**Team:** TYRANTS | SIH26102

---

## High-Level Architecture

```
┌─────────────────────────────────────────────────────┐
│              DATA SOURCES                           │
│  data.gov.in (GODL) │ eSAKSHI* │ CSV/PDF uploads  │
│  * requires authorization                           │
└────────────────┬────────────────────────────────────┘
                 │
┌────────────────▼────────────────────────────────────┐
│              DATA PIPELINE                          │
│  fetch() → validate() → normalize() → load()       │
│  provenance tracking per record                    │
└────────────────┬────────────────────────────────────┘
                 │
┌────────────────▼────────────────────────────────────┐
│              DATABASE (SQLite/PostgreSQL)            │
│  15 tables via SQLAlchemy ORM                      │
│  Full provenance, audit trail, availability status │
└────────────────┬────────────────────────────────────┘
                 │
┌────────────────▼────────────────────────────────────┐
│              FEATURE ENGINEERING                    │
│  cost features │ delay features │ similarity feats │
└────────────────┬────────────────────────────────────┘
                 │
┌────────────────▼────────────────────────────────────┐
│              ML MODELS                              │
│  Cost Anomaly (Isolation Forest, unsupervised)     │
│  Delay Prediction (Random Forest, weak labels)     │
│  Duplicate Similarity (TF-IDF cosine)              │
│  Physical Progress (CV architecture, NOT_AVAILABLE)│
└────────────────┬────────────────────────────────────┘
                 │
┌────────────────▼────────────────────────────────────┐
│              ENGINES                                │
│  Risk Fusion Engine (configurable weights)         │
│  Reality Gap Engine                                │
│  Expected Progress Engine                          │
│  Verification Recommender                          │
└────────────────┬────────────────────────────────────┘
                 │
┌────────────────▼────────────────────────────────────┐
│              FastAPI (REST API)                     │
│  /projects, /ml, /data, /models endpoints          │
│  JWT auth + RBAC (ADMIN/OFFICER/ANALYST/VIEWER)   │
│  Rate limiting, audit logging                      │
└────────────────┬────────────────────────────────────┘
                 │
┌────────────────▼────────────────────────────────────┐
│              React Frontend (Vite + TypeScript)     │
│  MapLibre GL JS (2D/3D map)                        │
│  Three.js / React Three Fiber (3D digital twins)  │
│  OpenAI-powered contextual assistant               │
│  PDF report generation                             │
└─────────────────────────────────────────────────────┘
```

---

## Backend Architecture

### `backend/`
```
main.py                  # FastAPI app, CORS, middleware mounting
api/
  projects.py            # Project CRUD + listing
  risk.py                # Risk scores + SHAP explanations
  reality_gap.py         # Reality gap computation
  digital_twin.py        # 3D state generation
  evidence.py            # Image upload + CV inference
  timeline.py            # Project time series
  recommendations.py     # Verification recommendations  
  reports.py             # PDF report generation
  ml_endpoints.py        # /ml/* inference endpoints
  data_endpoints.py      # /data/* pipeline control
  models_api.py          # /models/* registry
  auth.py                # JWT login/refresh/roles
database/
  models.py              # SQLAlchemy ORM models (15 tables)
  session.py             # DB engine + session factory
  init_db.py             # Schema creation + seed data
engines/
  risk_fusion.py         # Weighted risk aggregation
  reality_gap.py         # Gap score computation
  expected_progress.py   # Historical baseline estimation
  recommendation.py      # Rule-based verification recommendations
middleware/
  auth_middleware.py     # JWT validation + role check
  rate_limiter.py        # Per-user rate limiting
  audit_middleware.py    # Request/response audit logging
```

---

## ML Architecture

### `ml/`
```
features/
  cost_features.py       # utilization_rate, cost_percentile, regional_deviation
  delay_features.py      # elapsed_ratio, progress_vs_time, sector_baseline
  similarity_features.py # TF-IDF vectors, geo distance matrix
train/
  cost_anomaly.py        # Isolation Forest training
  delay_model.py         # Random Forest + XGBoost training
  similarity_model.py    # TF-IDF vectorizer training
inference/
  cost_inference.py      # Batch + single inference
  delay_inference.py
  similarity_inference.py
  progress_inference.py  # CV inference (NOT_AVAILABLE state)
evaluate.py              # Metrics + fairness evaluation
```

---

## Data Pipeline Architecture

### `data_pipeline/`
```
sources/
  base.py                # BaseDataSource (ABC)
  data_gov_in.py         # DataGovInSource (CKAN API)
  csv_source.py          # CSVDataSource
  pdf_source.py          # PDFDataSource (pdfplumber)
processors/
  normalizer.py          # Field standardization
  validator.py           # Quality checks
normalizers/
  sector_normalizer.py   # Sector name unification
  amount_normalizer.py   # Currency/unit normalization
  status_normalizer.py   # Status code normalization
loaders/
  db_loader.py           # Batch upsert to DB
logs/                    # Rotating JSON log files
run.py                   # Entry point: python -m data_pipeline.run
```

---

## Frontend Architecture

### `frontend/src/`
```
pages/
  Overview.tsx           # Main command centre
  Map3D.tsx              # MapLibre + Three.js geospatial view
  Projects.tsx           # Filterable project list
  ProjectDetail.tsx      # Full project intelligence
  DigitalTwin.tsx        # Standalone 3D twin viewer
  RiskMonitor.tsx        # Live risk feed
  RealityGap.tsx         # Gap analysis dashboard
  Analytics.tsx          # Model performance + data quality
  AuditTrail.tsx         # User action log
  Settings.tsx           # Admin settings (weights, roles)
components/
  twins/
    BuildingTwin.tsx     # Foundation → Finishing
    RoadTwin.tsx         # Earthwork → Markings
    BridgeTwin.tsx
    WaterTankTwin.tsx
    ProgressSlider.tsx
    ComparisonView.tsx
  map/
    ProjectPins.tsx      # MapLibre project pins
    ColorModeControl.tsx # PROGRESS/RISK/REALITY_GAP modes
  risk/
    RiskDNA.tsx          # Radar chart (Physical/Financial/Time/etc.)
    AnomalyChain.tsx     # Anomaly signal chain graph
    ExplanationPanel.tsx # SHAP explanation display
  shared/
    DataBadge.tsx        # PUBLIC_VERIFIED / SYNTHETIC / NOT_AVAILABLE
    ConfidenceMeter.tsx  # Confidence display
    MetricCard.tsx
    RiskBadge.tsx
  assistant/
    AIAssistant.tsx      # OpenAI + DB grounding chat
hooks/
  useProject.ts
  useRiskScore.ts
  useRealityGap.ts
  useDigitalTwin.ts
lib/
  api.ts                 # Axios API client
  constants.ts
  types.ts               # TypeScript types
```

---

## Three.js Digital Twin

Each project type has a parameterized 3D model that responds to `progress` (0–100%).

**Component lifecycle stages:**

### Building
| Stage | Progress Range |
|---|---|
| Foundation | 0–15% |
| Columns | 10–35% |
| Beams | 25–45% |
| Walls | 40–70% |
| Roof | 65–80% |
| Services | 75–92% |
| Finishing | 90–100% |

### Road
| Stage | Progress Range |
|---|---|
| Land Preparation | 0–15% |
| Earthwork | 10–30% |
| Sub-base | 25–50% |
| Base Course | 45–70% |
| Asphalt | 65–90% |
| Markings | 88–100% |

### Bridge / Water Tank — similar staged progression

---

## Reality Gap Engine

Computes 5 gap dimensions:

| Dimension | Formula |
|---|---|
| Financial Gap | `abs(utilization_rate - reported_progress/100)` |
| Reported-Observed Gap | `abs(reported_progress - observed_progress)` (null if no observation) |
| Expected-Reported Gap | `abs(expected_progress - reported_progress)` |
| Time-Progress Gap | deviation from expected timeline |
| Document Consistency | extracted vs. reported values |

**Combined Score:**  
`REALITY_GAP = weighted_sum(gaps) × 100`

| Score | Level |
|---|---|
| 0–30 | NORMAL |
| 31–60 | WATCH |
| 61–80 | HIGH |
| 81–100 | CRITICAL |

> Note: This is a prototype analytical score — not an official government metric.

---

## Risk Fusion Engine

Default weights (configurable via `/admin/settings`):

| Signal | Weight |
|---|---|
| Cost anomaly | 0.20 |
| Payment–progress mismatch | 0.20 |
| Delay probability | 0.15 |
| Duplicate similarity | 0.10 |
| Document inconsistency | 0.10 |
| Reality gap | 0.25 |

Final: `RISK_SCORE = sum(signal_i × weight_i) × 100`

---

## Security Architecture

- JWT (HS256) with 60-minute expiry + refresh tokens
- Role-based access control: ADMIN > OFFICER > ANALYST > VIEWER
- Rate limiting: 100 req/min per user
- File upload: JPEG/PNG only, max 10MB, SHA-256 hash checked
- SQL injection protection: SQLAlchemy parameterized queries
- XSS protection: response sanitization
- Secrets: environment variables only, never committed
- Audit trail: every state-changing action logged

---

## Deployment

### Development (no Docker)
```
backend: uvicorn backend.main:app --port 8000
frontend: cd frontend && npm run dev (port 5173)
database: SQLite (nirvana.db in project root)
```

### Production (Docker Compose)
```
Services: frontend (nginx), backend (uvicorn), postgres, ml-service
```

See DEPLOYMENT.md for full instructions.
