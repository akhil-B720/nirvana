# NIRVANA — Ethics & Responsible AI

**Team:** TYRANTS | SIH26102

---

## Core Ethical Principle

NIRVANA is a **decision-support system**, not a judgment system.

Every AI output carries an explicit disclaimer:

> "AI-generated risk indicators are decision-support signals and do not constitute proof of fraud, corruption, or wrongdoing. Final decisions are made by authorized government officers."

---

## Language Policy

| ❌ NEVER use | ✅ USE instead |
|---|---|
| "Fraud detected" | "Potential anomaly detected" |
| "This MP is corrupt" | "High-risk pattern identified" |
| "Confirmed duplicate" | "Potentially similar project" |
| "Proven irregularity" | "Potential irregularity — verification recommended" |
| "AI says it's fake" | "Reality gap identified — officer review required" |

---

## Human-in-the-Loop

All NIRVANA risk signals flow through a human verification step:

1. AI generates risk indicators and recommendations
2. Analyst reviews evidence and signals
3. Officer makes final determination
4. All decisions are logged in the audit trail with human attribution

---

## Data Honesty

NIRVANA never fabricates data:

- Missing physical progress → shown as `NOT_AVAILABLE`, not a fake percentage
- Unavailable satellite imagery → architecture ready, status shown as `NOT_AVAILABLE`
- Synthetic data used for development → explicitly labeled `SYNTHETIC` in DB and UI
- Government data → labeled `PUBLIC_VERIFIED` with source URL and retrieval timestamp

---

## Fairness Considerations

### Regional Bias
Cost anomaly detection is normalized per:
- Project type (road vs. school vs. bridge)
- State/region (cost of construction varies significantly)
- Time period (inflation adjustment)

A ₹10 lakh road in rural Bihar is **not** compared directly with a ₹10 lakh road in urban Mumbai.

### Performance Equity
Model performance is evaluated separately for:
- Different regions
- Different project categories
- Different time periods

Substantial performance differences across groups are documented in model cards and shown in the admin analytics panel.

### No Targeting
NIRVANA does not target individual MPs or officers. It analyzes **projects**, not people.

---

## Appropriate Use

✅ **Appropriate:**
- Identifying projects that warrant physical verification
- Prioritizing officer inspection work
- Tracking implementation progress across constituencies
- Identifying data quality issues in reporting

❌ **Inappropriate:**
- Using risk scores as proof of wrongdoing
- Publishing individual risk scores without investigation
- Making disciplinary decisions based solely on AI output
- Replacing domain expertise with automated decisions

---

## Known Failure Modes

1. **Construction cost volatility**: Emergency projects, natural disaster reconstruction, and COVID-period projects may show anomalous costs that are entirely legitimate
2. **Data quality propagation**: If reported data is incorrect, AI conclusions based on it will be incorrect
3. **Rural vs. urban baseline**: Sparse data for remote constituencies may reduce model confidence
4. **Label scarcity**: No confirmed fraud labels exist — the system detects anomalies, not fraud

---

## Bias Monitoring

The system includes a fairness evaluation module that checks for:
- Significant anomaly rate differences across states
- Systematic under/over-flagging of specific project types
- Confidence distribution by data density

See `/admin/analytics` → Model Performance for current fairness metrics.

---

## Data Retention & Privacy

- No personally identifiable information beyond public records
- MP names, constituency, and district data are public government records
- No private contractor data without authorization
- Audit logs retained per government data retention policy
