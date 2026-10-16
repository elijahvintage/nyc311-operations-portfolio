# NYC 311 Q1 2025 data dictionary

## Source

- **Dataset:** [311 Service Requests from 2020 to Present](https://data.cityofnewyork.us/Social-Services/311-Service-Requests-from-2020-to-Present/erm2-nwe9)
- **Provider:** NYC OpenData / 311
- **Dataset ID:** `erm2-nwe9`
- **Extract:** requests created from 2025-01-01 through 2025-03-31
- **Rows downloaded:** 884,765

## Fields used

| Field | Meaning |
|---|---|
| `unique_key` | Unique service-request identifier |
| `created_date` | Timestamp when the request was created |
| `closed_date` | Timestamp when the responding agency closed the request |
| `agency` / `agency_name` | Responding agency code and name |
| `complaint_type` | Broad problem category |
| `descriptor` | More specific problem detail |
| `location_type` | Location type associated with the request |
| `incident_zip` | Geo-validated incident ZIP code |
| `status` | Request status in the source system |
| `borough` | NYC borough |
| `latitude`, `longitude` | Incident coordinates when available |
| `open_data_channel_type` | Intake channel, such as phone, online, or mobile |

## Derived fields

- `resolution_hours`: elapsed hours between `created_date` and `closed_date`.
- `closed_flag`: valid close timestamp and source status `Closed`.
- `sla_breach_72h`: closed requests with resolution time above 72 hours. This is an **analytical triage threshold**, not a published NYC service-level agreement.
- `open_at_extract`: requests without a valid closed record in the extract.
- `priority_score`: `volume × 72-hour breach rate × median resolution hours` by complaint type.
