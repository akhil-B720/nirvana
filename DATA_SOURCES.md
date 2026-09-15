# NIRVANA — Data Sources

**Team:** TYRANTS | SIH26102

> Every data source is documented with provenance, license, access method, and data availability status.

---

## Data Availability Status Definitions

| Status | Meaning |
|---|---|
| `PUBLIC_VERIFIED` | Government open data with verified URL and license |
| `AUTHORIZED` | Available only with authorized government access |
| `SYNTHETIC` | Generated for development/testing — not real government data |
| `MISSING` | Field is unavailable from any source |

---

## Source 1: MPLADS Works List — 17th Lok Sabha

| Field | Value |
|---|---|
| **Source Name** | MPLADS Works List (17th Lok Sabha) |
| **Source URL** | https://data.gov.in/resource/mplads-works-list-17th-lok-sabha |
| **Publisher** | Ministry of Statistics and Programme Implementation (MoSPI) |
| **Source Type** | Open Government Dataset |
| **Format** | CSV, JSON, XML |
| **License** | Government Open Data License — India (GODL) |
| **Access Method** | Direct CSV download (no login required) |
| **Verification Status** | `PUBLIC_VERIFIED` |
| **Time Period** | 17th Lok Sabha (2019–2024) |

### Available Fields
| Field | Description |
|---|---|
| MP Name | Name of the Member of Parliament |
| Constituency | Lok Sabha / Rajya Sabha constituency |
| State/UT | State or Union Territory |
| Work Description | Name/description of the sanctioned work |
| Sector | Sector category (Roads, Education, Health, etc.) |
| Estimated Cost (₹) | Cost estimate at sanctioning |
| Recommended Date | Date of MP recommendation |
| Sanction Date | Date of district sanction |
| Status of Work | Completion status (Completed/In Progress/Not Started) |

### Missing Fields (Not in public data)
- Precise latitude/longitude of work site
- Contractor/vendor name
- Expenditure as of date
- Photo evidence
- Payment vouchers

---

## Source 2: Year-wise MPLADS Fund Position (2014–2018)

| Field | Value |
|---|---|
| **Source Name** | Year-wise Position of MPLADS Funds 2014-15 to 2017-18 |
| **Source URL** | https://data.gov.in/resource/year-wise-position-members-parliament-local-area-development-scheme-mplads-2014-15-2017-18 |
| **Publisher** | MoSPI |
| **License** | GODL |
| **Access Method** | Direct CSV download |
| **Verification Status** | `PUBLIC_VERIFIED` |

### Available Fields
- State/UT
- Year
- Recommended Amount (₹ Lakhs)
- Sanctioned Amount (₹ Lakhs)
- Released Amount (₹ Lakhs)
- Expenditure Incurred (₹ Lakhs)

---

## Source 3: Sector-wise Cumulative Cost of Sanctioned Works (2015)

| Field | Value |
|---|---|
| **Source URL** | https://data.gov.in/resource/sector-wise-cumulative-cost-sanctioned-works-under-members-parliament-local-area |
| **Publisher** | MoSPI |
| **License** | GODL |
| **Access Method** | Direct CSV download |
| **Verification Status** | `PUBLIC_VERIFIED` |

### Available Fields
- Sector Name (Drinking Water, Sanitation, Roads/Bridges, Education, Health, etc.)
- Number of Works Sanctioned
- Cumulative Cost Sanctioned (₹ Lakhs)

---

## Source 4: State-wise Works & Financial Performance (2016–2020)

| Field | Value |
|---|---|
| **Source URL** | https://data.gov.in/resource/state-wise-details-worksprojects-under-members-parliament-local-area-development-scheme |
| **Publisher** | MoSPI |
| **License** | GODL |
| **Access Method** | Direct CSV download |
| **Verification Status** | `PUBLIC_VERIFIED` |

### Available Fields
- State/UT
- Works Recommended / Sanctioned / Completed
- Funds Released (₹ Lakhs)
- Funds Utilised (₹ Lakhs)
- % Expenditure

---

## Source 5: State-wise Unspent Balance (Nov 2018)

| Field | Value |
|---|---|
| **Source URL** | https://data.gov.in/resource/stateut-wise-details-unspent-balance-members-parliament-local-area-development-scheme |
| **Publisher** | MoSPI |
| **License** | GODL |
| **Access Method** | Direct CSV download |
| **Verification Status** | `PUBLIC_VERIFIED` |

---

## Source 6: 18th Lok Sabha MPLADS Works (Detailed — 44,169 rows)

| Field | Value |
|---|---|
| **Source URL** | https://dataful.in/datasets/22566/ |
| **Publisher** | MoSPI / Dataful |
| **License** | Dataful Terms of Service |
| **Access Method** | Free account required for bulk download |
| **Verification Status** | `PUBLIC_VERIFIED` (once downloaded) |
| **Record Count** | 44,169 rows |

### Available Fields (18 columns)
`data_as_on`, `state`, `implementing_district_per_source`, `implementing_district_per_lgd`,
`implementing_district_lgd_code`, `loksabha_constituency`, `house_name`, `loksabha_MP_name`,
`work_category`, `unique_work_number`, `work_name`, `implementing_agency_name`,
`work_description`, `date_of_completion`, `image_uploaded`, `amount`, `units`, `notes`

> **To download:** Register at https://dataful.in → Search "MPLADS 18th Lok Sabha" → Download CSV.
> Place the file at: `dataset/raw/mplads_18ls_works.csv`

---

## Source 7: eSAKSHI Portal (mplads.mospi.gov.in)

| Field | Value |
|---|---|
| **Source URL** | https://mplads.mospi.gov.in |
| **Publisher** | MoSPI / TCS |
| **Access Method** | Authorized login (MP / District Officer / MoSPI) |
| **Verification Status** | `AUTHORIZED` |

### Available (behind login)
- Full project lifecycle data
- Payment records
- Geo-coordinates of works
- Document attachments
- Contractor information
- Progress photos (uploaded by agencies)

> **Note:** Integration with eSAKSHI requires authorization from MoSPI. This is a future integration path.

---

## NOT Available From Any Public Source

| Data Type | Status | Reason |
|---|---|---|
| Real-time project geo-coordinates | `MISSING` | Behind eSAKSHI login |
| Physical progress photos | `MISSING` | Behind eSAKSHI + field data |
| Payment vouchers/UTRs | `MISSING` | Restricted government records |
| Contractor/vendor blacklist | `MISSING` | No public dataset |
| Satellite imagery (project-level) | `MISSING` | Requires commercial/ISRO contract |
| Drone footage | `MISSING` | Requires field collection |
| Confirmed fraud flags | `MISSING` | No labeled fraud dataset exists |

---

## Synthetic Data Policy

Synthetic data is used ONLY for:
- Development and testing
- ML pipeline validation
- UI demonstration

**Synthetic data is NEVER represented as real government data.**

All synthetic records are marked with `data_availability_status = 'SYNTHETIC'` in the database and the UI shows a `[SYNTHETIC DATA]` badge.

Synthetic distributions are derived from the real statistical properties of the GODL-licensed datasets to ensure pipelines work realistically.
