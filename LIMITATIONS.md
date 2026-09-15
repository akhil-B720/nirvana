# NIRVANA — Known Limitations

**Team:** TYRANTS | SIH26102

This document honestly describes what NIRVANA **cannot** currently do.

---

## Data Limitations

### 1. No Real-Time Project Data
- The eSAKSHI portal (mplads.mospi.gov.in) requires authorized login
- All real-time project data, payment records, and work orders are behind authentication
- Current deployment uses GODL-licensed summary datasets + clearly labeled synthetic data

### 2. No Physical Progress Observation
- Satellite imagery integration: **NOT IMPLEMENTED** (requires commercial/ISRO contract)
- Drone footage processing: **NOT IMPLEMENTED** (requires field data)
- The computer vision pipeline is architected but **not trained** on real construction images
- All `observed_progress` values are `null` / `NOT_AVAILABLE` until evidence is uploaded or a trained model is deployed

### 3. No Geo-Coordinates in Public Data
- The publicly available MPLADS datasets do not include precise lat/lon for individual projects
- Map pins use constituency centroid approximations from Census data
- Accurate project geo-tagging requires eSAKSHI access or field data

### 4. Historical Data Only
- Available data covers up to the 18th Lok Sabha (2024–2026)
- No data before 2014 in structured machine-readable form from public sources

---

## ML Model Limitations

### Cost Anomaly Model
- Trained on anonymized MPLADS cost distribution (unsupervised)
- **No fraud labels** — detects statistical outliers, not confirmed fraud
- Cannot distinguish between legitimate high-cost projects and misreported costs
- Performance varies significantly for sparse project types

### Delay Prediction Model
- Uses `completion status` as a weak supervision signal
- Model accuracy is limited by the noisiness of self-reported status
- Does not account for external factors: floods, elections, court orders, etc.
- Baseline statistical model — minimum label count not yet reached for full supervised training

### Physical Progress Estimator
- **Architecture complete, model NOT trained**
- No publicly available labeled construction image dataset for MPLADS project types
- Returns `NOT_AVAILABLE` for all observations until a labeled dataset is provided
- When deployed with real data, transfer learning from EfficientNet/ResNet backbone will be used

### Duplicate Detection
- Text similarity only (TF-IDF cosine + geographic distance)
- Outputs `potentially_similar`, not `confirmed_duplicate`
- Short or vague project names reduce recall significantly

---

## Technical Limitations

### No Live Satellite Data
- Sentinel-2 / Bhuvan integration is designed but not active
- Requires API credentials or bulk purchase agreement

### No IoT Integration
- Sensor data from construction sites is a future integration
- Not applicable to most MPLADS project types (small infrastructure)

### No BIM Integration
- Building Information Modeling is a phase 2+ research feature
- Current digital twin uses procedural geometry, not real BIM data

### Docker
- Docker is not pre-installed on the target machine
- Manual run mode provided as the primary path
- docker-compose.yml is included for deployment environments

---

## What These Limitations Mean in Practice

| Feature | Current Status |
|---|---|
| Real project geo-coordinates | ❌ NOT_AVAILABLE (requires eSAKSHI) |
| Physical progress from imagery | ❌ NOT_AVAILABLE (no trained CV model) |
| Real-time data sync | ❌ NOT_AVAILABLE (requires authorized API) |
| Satellite change detection | ❌ NOT_AVAILABLE (requires credential) |
| Fraud classification | ❌ Will NEVER claim fraud — anomaly detection only |
| Cost anomaly detection | ✅ IMPLEMENTED (Isolation Forest, unsupervised) |
| Delay probability | ✅ IMPLEMENTED (statistical baseline with caveat labels) |
| Duplicate similarity | ✅ IMPLEMENTED (TF-IDF + geo) |
| Reality gap score | ✅ IMPLEMENTED (prototype analytical score) |
| 3D digital twin | ✅ IMPLEMENTED (procedural, progress-driven) |
| Explainable AI (SHAP) | ✅ IMPLEMENTED for cost + delay models |
| AI assistant | ✅ IMPLEMENTED (OpenAI + DB grounding) |
| PDF reports | ✅ IMPLEMENTED |
| Audit trail | ✅ IMPLEMENTED |

---

## Future Development Roadmap

1. **Phase A**: eSAKSHI API integration (requires government authorization)
2. **Phase B**: Sentinel-2 satellite imagery change detection
3. **Phase C**: Drone footage processing pipeline
4. **Phase D**: Mobile field inspection app
5. **Phase E**: LiDAR / photogrammetry 3D reconstruction
6. **Phase F**: 4D BIM integration
7. **Phase G**: Multimodal foundation model for construction progress estimation
