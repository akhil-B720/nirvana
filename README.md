# NIRVANA
## National Infrastructure Reality & Verification Network using AI

**Team:** TYRANTS  
**Hackathon:** Smart India Hackathon — SIH26102  
**Category:** Software  
**Problem Statement:** Development of an AI-powered system to detect anomalies, fraud, and inefficiencies in MPLAD Scheme implementation.

---

## ⚠️ Ethical Statement

NIRVANA does **not** claim to detect fraud.

All outputs are **AI-generated risk indicators** that serve as decision-support signals for authorized government officers. They do **not** constitute proof of fraud, corruption, or wrongdoing.

The system uses language like:
- "Potential anomaly detected"
- "High-risk pattern — verification recommended"
- "Reality gap identified"

Final decisions are always made by **authorized human officers**.

---

## What NIRVANA Does

NIRVANA continuously evaluates five questions for every MPLADS project:

1. **WHERE** is the project? *(GIS + location data)*
2. **WHAT should exist by now?** *(Expected progress + financial model)*
3. **WHAT has been reported?** *(Official reported progress)*
4. **WHAT does available evidence suggest?** *(Physical evidence, documents, satellite — where available)*
5. **WHAT should the officer verify next?** *(AI-generated verification recommendations)*

---

## Quick Start

### Prerequisites
- Python 3.9+
- Node.js 18+
- SQLite (default) or PostgreSQL (production)

### 1. Install Python dependencies
```bash
cd nirvana
pip install -r requirements.txt
```

### 2. Set up environment
```bash
cp .env.example .env
# Edit .env with your settings (OPENAI_API_KEY, etc.)
```

### 3. Initialize database
```bash
python -m backend.database.init_db
```

### 4. Run data pipeline
```bash
python -m data_pipeline.run
```

### 5. Train ML models
```bash
python -m ml.train.cost_anomaly
python -m ml.train.delay_model
python -m ml.train.similarity_model
```

### 6. Start API server
```bash
uvicorn backend.main:app --reload --port 8000
```

### 7. Start frontend
```bash
cd frontend
npm install
npm run dev
```

### Docker (full stack)
```bash
docker compose up
```

### 8. Web Deployment (Render / Heroku)
The backend is configured with a `Procfile` (`web: uvicorn backend.main:app --host 0.0.0.0 --port $PORT`). Note: Do not assume `localhost` in production. Ensure `VITE_API_URL` is set when building the frontend.

---

## Data Sources

All data sources are documented in [DATA_SOURCES.md](DATA_SOURCES.md).

**Primary sources used:**
- MPLADS Works List — 17th Lok Sabha (data.gov.in, GODL license)
- Year-wise MPLADS Fund Position (data.gov.in, GODL license)
- State-wise Financial Performance (data.gov.in, GODL license)

**Data availability status** is shown throughout the UI:
- `PUBLIC_VERIFIED` — Government open data
- `SYNTHETIC` — Clearly marked development/test data
- `NOT_AVAILABLE` — Field is missing, not fabricated

---

## Architecture

See [ARCHITECTURE.md](ARCHITECTURE.md) for the full system design.

---

## ML Models

See [ML_PIPELINE.md](ML_PIPELINE.md) and individual model cards:
- [MODEL_CARD_COST.md](MODEL_CARD_COST.md) — Cost anomaly detection
- [MODEL_CARD_DELAY.md](MODEL_CARD_DELAY.md) — Delay prediction
- [MODEL_CARD_PROGRESS.md](MODEL_CARD_PROGRESS.md) — Physical progress estimation

---

## Ethics & Limitations

- [ETHICS.md](ETHICS.md) — Ethical principles and fairness considerations
- [LIMITATIONS.md](LIMITATIONS.md) — Known limitations and missing features

---

## License

Documentation and code: MIT License  
Data: Government Open Data License — India (GODL) for public datasets
