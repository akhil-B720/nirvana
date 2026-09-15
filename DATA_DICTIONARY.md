# NIRVANA — Data Dictionary

**Team:** TYRANTS | SIH26102

---

## Table: `projects`

The core project table. Never overwrite original government values — use `original_value` / `normalized_value` pattern.

| Column | Type | Description | Source |
|---|---|---|---|
| project_id | UUID | Primary key | System |
| external_id | VARCHAR(100) | ID from source system (e.g., eSAKSHI unique_work_number) | Source |
| project_name | TEXT | Official name of the work | Source |
| project_type | VARCHAR(50) | BUILDING, ROAD, BRIDGE, WATER_TANK, OTHER | Normalized |
| sector | VARCHAR(100) | Sector (Roads, Education, Health, Drinking Water, etc.) | Source |
| state | VARCHAR(100) | State/UT name | Source |
| district | VARCHAR(100) | District name | Source |
| constituency | VARCHAR(100) | Lok Sabha / Rajya Sabha constituency | Source |
| block | VARCHAR(100) | Block name (if available) | Source |
| village | VARCHAR(100) | Village name (if available) | Source |
| latitude | FLOAT | Project latitude (constituency centroid if precise not available) | Derived |
| longitude | FLOAT | Project longitude | Derived |
| geo_precision | VARCHAR(20) | EXACT, CONSTITUENCY_CENTROID, DISTRICT_CENTROID | System |
| sanction_amount | NUMERIC(15,2) | Sanctioned amount in INR | Source |
| released_amount | NUMERIC(15,2) | Released amount in INR (if available) | Source |
| expenditure_amount | NUMERIC(15,2) | Expenditure incurred in INR (if available) | Source |
| start_date | DATE | Project start date | Source |
| expected_completion_date | DATE | Planned completion date | Source |
| actual_completion_date | DATE | Actual completion date (null if not complete) | Source |
| reported_progress | FLOAT | Progress % as reported (0–100) | Source |
| status | VARCHAR(30) | COMPLETED, IN_PROGRESS, NOT_STARTED, DELAYED, STALLED | Normalized |
| agency | VARCHAR(200) | Implementing agency name | Source |
| mp_name | VARCHAR(200) | MP name (public record) | Source |
| house | VARCHAR(20) | LOK_SABHA, RAJYA_SABHA | Source |
| lok_sabha_term | VARCHAR(10) | e.g., "17th", "18th" | Source |
| data_availability_status | VARCHAR(20) | PUBLIC_VERIFIED, AUTHORIZED, SYNTHETIC, MISSING | System |
| source_id | UUID FK | Reference to data_sources table | System |
| created_at | TIMESTAMPTZ | Record creation timestamp | System |
| updated_at | TIMESTAMPTZ | Last update timestamp | System |

---

## Table: `project_financials`

Financial time-series per project (history of payments).

| Column | Type | Description |
|---|---|---|
| financial_id | UUID | Primary key |
| project_id | UUID FK | Reference to projects |
| record_date | DATE | Date of financial record |
| cumulative_expenditure | NUMERIC(15,2) | Running expenditure |
| installment_released | NUMERIC(15,2) | Amount released in this installment |
| utilization_rate | FLOAT | expenditure / released_amount |
| financial_source | VARCHAR(50) | Source of this record |

---

## Table: `project_progress`

Progress snapshots over time.

| Column | Type | Description |
|---|---|---|
| progress_id | UUID | Primary key |
| project_id | UUID FK | Reference to projects |
| snapshot_date | DATE | Date of snapshot |
| reported_progress | FLOAT | Reported % (0–100) |
| observed_progress | FLOAT | AI-estimated % (null if not available) |
| observed_confidence | FLOAT | Confidence of observed estimate (0–1) |
| observation_source | VARCHAR(50) | IMAGE_AI, FIELD_INSPECTION, SATELLITE, NOT_AVAILABLE |
| expected_progress | FLOAT | Model-estimated expected progress % |
| expected_confidence | FLOAT | Confidence interval width |

---

## Table: `project_events`

Timeline of significant project events.

| Column | Type | Description |
|---|---|---|
| event_id | UUID | Primary key |
| project_id | UUID FK | Reference to projects |
| event_date | DATE | Date of event |
| event_type | VARCHAR(50) | RECOMMENDATION, SANCTION, PAYMENT, COMPLETION, DELAY, STALL, INSPECTION |
| description | TEXT | Event description |
| source | VARCHAR(100) | Source of this event record |

---

## Table: `project_documents`

Document inventory for a project.

| Column | Type | Description |
|---|---|---|
| doc_id | UUID | Primary key |
| project_id | UUID FK | Reference to projects |
| doc_type | VARCHAR(50) | SANCTION_ORDER, COMPLETION_CERT, UTILIZATION_CERT, PHOTO, MB_EXTRACT |
| file_path | TEXT | Storage path (local or object store) |
| upload_timestamp | TIMESTAMPTZ | Upload time |
| uploaded_by | UUID FK | User who uploaded |
| file_hash | VARCHAR(64) | SHA-256 hash for integrity |
| extracted_amount | NUMERIC(15,2) | Amount extracted from document (if applicable) |
| extracted_date | DATE | Date extracted from document |
| consistency_score | FLOAT | Consistency with DB records (0–1) |

---

## Table: `project_evidence`

Physical evidence (images) per project.

| Column | Type | Description |
|---|---|---|
| evidence_id | UUID | Primary key |
| project_id | UUID FK | Reference to projects |
| image_path | TEXT | Storage path |
| capture_timestamp | TIMESTAMPTZ | When image was taken |
| latitude | FLOAT | GPS latitude of capture |
| longitude | FLOAT | GPS longitude of capture |
| source | VARCHAR(50) | DRONE, SATELLITE, FIELD_PHONE, UPLOAD |
| file_hash | VARCHAR(64) | SHA-256 hash |
| estimated_progress | FLOAT | CV-estimated progress (null if model not available) |
| cv_confidence | FLOAT | CV model confidence |
| detected_components | JSONB | List of detected construction components |
| availability_status | VARCHAR(20) | NOT_AVAILABLE, PENDING, PROCESSED |

---

## Table: `project_locations`

Geographic data for projects.

| Column | Type | Description |
|---|---|---|
| location_id | UUID | Primary key |
| project_id | UUID FK | Reference to projects |
| latitude | FLOAT | Latitude |
| longitude | FLOAT | Longitude |
| precision_level | VARCHAR(30) | EXACT, NEIGHBOURHOOD, CONSTITUENCY_CENTROID |
| source | VARCHAR(100) | Where geo came from |
| verified | BOOLEAN | Whether location is field-verified |

---

## Table: `project_anomalies`

Individual anomaly signals detected.

| Column | Type | Description |
|---|---|---|
| anomaly_id | UUID | Primary key |
| project_id | UUID FK | Reference to projects |
| anomaly_type | VARCHAR(50) | COST, PAYMENT_PROGRESS, DELAY, DUPLICATE, LOCATION, DOCUMENT, REALITY_GAP |
| signal_value | FLOAT | Raw anomaly score |
| normalized_score | FLOAT | Score normalized 0–100 |
| confidence | FLOAT | Confidence of this signal (0–1) |
| contributing_features | JSONB | Feature values that contributed |
| model_id | UUID FK | Model that generated this |
| detected_at | TIMESTAMPTZ | Detection timestamp |
| status | VARCHAR(20) | OPEN, VERIFIED, DISMISSED |

---

## Table: `risk_scores`

Fused risk score for a project.

| Column | Type | Description |
|---|---|---|
| risk_id | UUID | Primary key |
| project_id | UUID FK | Reference to projects |
| risk_score | FLOAT | Final fused risk score (0–100) |
| risk_level | VARCHAR(20) | LOW, MEDIUM, HIGH, CRITICAL |
| reality_gap_score | FLOAT | Reality gap component (0–100) |
| cost_anomaly_score | FLOAT | Cost anomaly component |
| delay_probability | FLOAT | Delay probability |
| similarity_score | FLOAT | Duplicate similarity signal |
| document_score | FLOAT | Document consistency score |
| weights_used | JSONB | Weight configuration at time of scoring |
| explanation | TEXT | Human-readable explanation |
| shap_values | JSONB | SHAP feature attributions |
| confidence | FLOAT | Overall confidence of this risk score |
| computed_at | TIMESTAMPTZ | Computation timestamp |
| model_version_ids | JSONB | Model versions used |

---

## Table: `model_predictions`

Individual model output records.

| Column | Type | Description |
|---|---|---|
| prediction_id | UUID | Primary key |
| project_id | UUID FK | Project reference |
| model_id | UUID FK | Model that made prediction |
| prediction_type | VARCHAR(50) | COST_ANOMALY, DELAY, SIMILARITY, PROGRESS |
| input_features | JSONB | Feature values used |
| raw_output | JSONB | Raw model output |
| prediction_value | FLOAT | Primary prediction value |
| confidence | FLOAT | Confidence score |
| predicted_at | TIMESTAMPTZ | Timestamp |

---

## Table: `model_versions`

Model registry.

| Column | Type | Description |
|---|---|---|
| model_id | UUID | Primary key |
| model_name | VARCHAR(100) | e.g., "cost_anomaly_isolation_forest" |
| version | VARCHAR(20) | Semantic version e.g., "1.0.0" |
| algorithm | VARCHAR(100) | Algorithm name |
| training_data_version | VARCHAR(50) | Dataset version used for training |
| training_timestamp | TIMESTAMPTZ | When trained |
| features | JSONB | List of feature names |
| hyperparameters | JSONB | Model hyperparameters |
| metrics | JSONB | Evaluation metrics |
| status | VARCHAR(20) | ACTIVE, RETIRED, EXPERIMENTAL |
| model_path | TEXT | File path to saved model |
| card_path | TEXT | File path to model card |

---

## Table: `data_sources`

Data source registry with provenance.

| Column | Type | Description |
|---|---|---|
| source_id | UUID | Primary key |
| source_name | VARCHAR(200) | Human-readable name |
| source_url | TEXT | URL of source |
| source_type | VARCHAR(50) | GOVERNMENT_OPEN, AUTHORIZED_API, SYNTHETIC, CSV_UPLOAD |
| retrieval_timestamp | TIMESTAMPTZ | When data was fetched |
| last_modified | TIMESTAMPTZ | Source's last modified time |
| license | VARCHAR(100) | License identifier (GODL, TOS, etc.) |
| access_method | VARCHAR(50) | DIRECT_DOWNLOAD, API, UPLOAD, SCRAPE |
| verification_status | VARCHAR(20) | PUBLIC_VERIFIED, AUTHORIZED, SYNTHETIC |
| record_count | INTEGER | Number of records from this source |

---

## Table: `officer_feedback`

Human feedback loop records.

| Column | Type | Description |
|---|---|---|
| feedback_id | UUID | Primary key |
| project_id | UUID FK | Project reference |
| officer_id | UUID FK | Officer who provided feedback |
| feedback_type | VARCHAR(50) | VERIFIED_NORMAL, CONFIRMED_ANOMALY, DISMISSED, ESCALATED |
| risk_score_at_feedback | FLOAT | Risk score at time of feedback |
| notes | TEXT | Officer notes |
| field_verified | BOOLEAN | Whether field inspection was conducted |
| created_at | TIMESTAMPTZ | Feedback timestamp |

---

## Table: `audit_logs`

Complete audit trail.

| Column | Type | Description |
|---|---|---|
| log_id | UUID | Primary key |
| user_id | UUID FK | User who performed action |
| project_id | UUID FK | Project affected (if applicable) |
| action | VARCHAR(100) | Action performed |
| entity_type | VARCHAR(50) | Type of entity changed |
| entity_id | UUID | ID of entity changed |
| previous_value | JSONB | Value before change |
| new_value | JSONB | Value after change |
| model_version | VARCHAR(50) | Model version if AI action |
| ip_address | VARCHAR(45) | Client IP |
| timestamp | TIMESTAMPTZ | Log timestamp |

---

## Table: `users`

User accounts with roles.

| Column | Type | Description |
|---|---|---|
| user_id | UUID | Primary key |
| username | VARCHAR(100) | Login username |
| email | VARCHAR(200) | Email address |
| hashed_password | VARCHAR(200) | Bcrypt hash |
| role | VARCHAR(20) | ADMIN, OFFICER, ANALYST, VIEWER |
| state | VARCHAR(100) | State jurisdiction (null = national) |
| is_active | BOOLEAN | Account active flag |
| created_at | TIMESTAMPTZ | Account creation time |
| last_login | TIMESTAMPTZ | Last successful login |
