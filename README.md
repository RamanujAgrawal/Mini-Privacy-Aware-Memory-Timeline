# Chronis • Mini Privacy-Aware Memory Timeline

A robust, privacy-first memory timeline prototype built for the **Chronis SDE Intern Technical Evaluation**. This application ingests and displays chronological user memory events across four core categories (`conversation`, `location`, `physiological`, `note`), allows users to dynamically toggle privacy controls, and **strictly enforces data access boundaries at the backend API layer** with an immutable audit log trail, full multi-tenancy, granular privacy rules, full-text search, and GDPR/CCPA data export capabilities.

---

## Architecture Overview

```mermaid
flowchart TD
    Client["Frontend SPA / API Clients / Postman"]
    
    subgraph Backend ["FastAPI Backend Application"]
        Router["API Router (/events, /permissions, /audit-log, /auth, /privacy-rules, /export)"]
        
        subgraph AuthTenantEngine ["Authentication & Multi-Tenancy Layer"]
            JWT["JWT Bearer Token Validator (OAuth2 / PBKDF2-HMAC)"]
            Tenant["Tenant Isolation Guard (user_id scoped queries)"]
        end

        subgraph PrivacyEngine ["Privacy & Access Control Layer"]
            Policy["PrivacyService (Allowed Category Filter)"]
            GranularRules["Granular Privacy Rules Engine (Redact / Drop Patterns)"]
            Guard["Resource Authorization Guard (403 Forbidden Check)"]
        end
        
        subgraph ExportEngine ["Data Portability Subsystem (GDPR/CCPA)"]
            Exporter["ExportService (JSON / CSV Streaming Exporter)"]
        end

        subgraph AuditEngine ["Audit Logging Subsystem"]
            Audit["AuditService (Immutable Append-Only Log)"]
        end
        
        subgraph DB ["SQLite Database (5 Dedicated Tables)"]
            Users[("users")]
            Events[("events")]
            Permissions[("permissions")]
            PrivacyRules[("privacy_rules")]
            AuditLogs[("audit_logs")]
        end
    end

    Client -->|HTTP GET/POST/PUT/DELETE| Router
    Router --> JWT
    JWT --> Tenant
    Tenant --> Policy
    Policy -->|Query-level Filtering| Events
    Policy --> GranularRules
    GranularRules -->|Pattern Redact / Drop| Events
    Router --> Guard
    Guard -->|Denied / Allowed Check| AuditLogs
    Router --> Exporter
    Exporter --> Events
    Exporter --> AuditLogs
    Router --> Audit
    Audit --> AuditLogs
    Policy --> Permissions
    GranularRules --> PrivacyRules
    Tenant --> Users
```

### Key Architectural Decisions
- **Zero-Friction Turnkey Setup**: Built with **FastAPI** + **SQLite (SQLAlchemy 2.0)** + **Vanilla Modern SPA**. Evaluators can clone, seed, execute tests, and launch the entire app without complex database servers, docker dependencies, or node daemons. Requests without explicit Bearer tokens automatically fallback to the seeded `Demo User (ID: 1)`.
- **Defense-in-Depth Privacy**: Access control is enforced strictly in the backend service layer (`PrivacyService` & `EventService`), never solely in the browser UI.
  - **Collection Listing (`GET /events`)**: Filtered at SQL query level using `WHERE type IN (:allowed_types)`. Restricted categories never enter server memory or network packets.
  - **Direct Resource Access (`GET /events/{id}`)**: Returns **`403 Forbidden`** if the requested event belongs to a disabled category, immediately recording a `DENIED` entry in `audit_logs`.
- **Read-Only Immutable Audit Log**: Every sensitive action (event creation, deletion, permission toggle, rule configuration, export, and authorized/blocked access) is recorded with an immutable schema (`timestamp`, `user_id`, `action`, `event_type`, `result`). Tampering attempts (`POST`/`PUT`/`DELETE` on `/audit-log`) are rejected with `405 Method Not Allowed`.

---

## Advanced Architectural Approaches Implemented

In addition to the baseline requirements, the following four advanced architectural enhancements are fully implemented and verified:

### 1. Full Authentication & Multi-Tenancy
- **JWT-Based OAuth2 Authentication**: Endpoints `POST /auth/register`, `POST /auth/login`, and `GET /auth/me` with PBKDF2-HMAC password hashing (100,000 iterations) and cryptographically signed JWT access tokens (HS256).
- **Tenant Isolation**: Strict row-level data scoping (`WHERE user_id = :current_user_id`) prevents horizontal privilege escalation. User A cannot view, query, or mutate events, permissions, rules, or audit entries belonging to User B.
- **Backward Compatibility**: Requests without an `Authorization: Bearer <token>` header gracefully default to `Demo User (ID: 1)`, preserving turnkey evaluation workflows.

### 2. Date-Range & Full-Text Search
- **Date-Range Filtering**: `GET /events?start_date=...&end_date=...` enables time-sliced timeline analysis (ISO 8601 timestamps).
- **Full-Text Search Across Transcripts & Notes**: Query parameter `GET /events?q=<keyword>` performs case-insensitive search across both `title` and `content`.

### 3. Automated Granular Privacy Rules
- **Rule-Based Filtering & Redaction**: Users can configure automated privacy rules (`GET /privacy-rules`, `POST /privacy-rules`, `DELETE /privacy-rules/{id}`) targeting specific categories or all categories.
- **Keyword Redaction (`action="redact"`)**: Dynamically replaces sensitive terms (e.g. passwords, client names, confidential project codenames) with `[REDACTED BY PRIVACY RULE]` in query results without mutating the underlying database record.
- **Pattern Drop (`action="drop"`)**: Automatically omits events matching sensitive criteria (e.g., specific location coordinates or home addresses) from timeline results and denies direct retrieval with `403 Forbidden`.

### 4. Export & Data Portability (GDPR Article 20 / CCPA)
- **Data Portability Endpoints**: `POST /export` and `GET /export` allow users to export their permitted timeline data, active permission configuration, and complete audit history.
- **Format Support**: Delivers data in structured `json` format or as a downloadable `csv` attachment with formatted timeline and audit headers.
- **Privacy-Aware Exports**: Exports strictly respect active category permissions and granular redaction rules so disabled or redacted data is never leaked in export archives. Every export action is recorded in the audit trail (`EXPORT_DATA`).

---

## Quickstart Guide

### 1. Prerequisites
- Python 3.10+ (Tested on Python 3.12)
- Git

### 2. Setup Virtual Environment & Dependencies
```bash
# Clone the repository
git clone https://github.com/RamanujAgrawal/Mini-Privacy-Aware-Memory-Timeline.git
cd Mini-Privacy-Aware-Memory-Timeline

# Create virtual environment
python -m venv .venv

# Activate virtual environment
# Windows:
.\.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

# Install dependencies
pip install -r backend/requirements.txt
```

### 3. Initialize & Seed Database
```bash
python backend/seed.py
```
*Creates the database tables, configures demo user `Demo User (ID: 1)`, sets all 4 permissions to `ON`, and seeds realistic memory timeline events.*

### 4. Run Automated Test Suite
```bash
pytest backend/tests -v
```
*All 16 automated test cases pass in under 2 seconds.*

### 5. Launch Application
```bash
python run.py
```
- **Web Timeline UI**: [http://127.0.0.1:8000](http://127.0.0.1:8000)
- **Interactive Swagger Docs**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **ReDoc Documentation**: [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)

### 6. Automation & Demonstration Scripts
```bash
# One-command full automated verification of privacy rules, 403 Forbidden checks, advanced features, and test suite:
python automate_demo.py

# Run live wearable telemetry simulator (generates sensor events periodically):
python backend/simulator.py
```
*(On Windows, you can also double-click `start.bat` to initialize and launch the application in one step).*

---

## API Documentation

All endpoints are available at root (e.g. `/events`) and versioned prefix (`/api/v1/events`).

| Method | Endpoint | Description | Privacy & Audit Behavior |
| :--- | :--- | :--- | :--- |
| `POST` | `/auth/register` | Register new user account | Hashes password with PBKDF2; returns signed JWT access token. |
| `POST` | `/auth/login` | Authenticate user | Validates credentials; returns JWT Bearer access token. |
| `GET` | `/auth/me` | Current user profile | Returns authenticated user metadata. |
| `GET` | `/events` | List events with pagination and filtering | Filters out disabled categories at SQL query level. Supports `?type=`, `?q=`, `?start_date=`, `?end_date=`, `?limit=`, `?offset=`. Applies active granular privacy rules. |
| `GET` | `/events/{id}` | Get event by ID | Returns `200 OK` if allowed; returns **`403 Forbidden`** and audits `DENIED` if category is OFF or dropped by rule. Returns `404` if not found. |
| `POST` | `/events` | Create new memory event | Validates schema (title, content, category enum). Audits `CREATED`. |
| `DELETE`| `/events/{id}` | Delete event by ID | Deletes event. Audits `DELETED`. |
| `GET` | `/permissions` | Get user category permissions | Returns dictionary of `{conversation, location, physiological, note}` boolean states. |
| `PUT` | `/permissions` | Toggle category permission | Updates category state (`is_enabled: true/false`). Audits `PERMISSION_SET_ON` / `PERMISSION_SET_OFF`. |
| `GET` | `/privacy-rules` | List active granular privacy rules | Returns user's configured keyword redaction and pattern drop rules. |
| `POST` | `/privacy-rules` | Create granular privacy rule | Configures rule (`category`, `rule_type`, `pattern`, `action`). Audits `CREATE_PRIVACY_RULE`. |
| `DELETE`| `/privacy-rules/{id}` | Delete privacy rule | Removes active granular rule. Audits `DELETE_PRIVACY_RULE`. |
| `POST` | `/export` | GDPR/CCPA Data Portability Export | Exports permitted timeline and audit trail in JSON or CSV format. Audits `EXPORT_DATA`. |
| `GET` | `/export` | Download exported memory package | Direct download endpoint for browsers (`?format=json` or `?format=csv`). |
| `GET` | `/audit-log` | Read-only audit log entries | Returns immutable paginated audit entries sorted by timestamp descending. |
| `GET` | `/health` | Service health status | Returns service uptime and version. |

---

## Database Schema

Separated into 5 dedicated relational tables:

1. **`users`**
   - `id` (INTEGER, PK, autoincrement)
   - `name` (VARCHAR)
   - `email` (VARCHAR, Unique)
   - `hashed_password` (VARCHAR, nullable)
   - `is_active` (BOOLEAN, default: True)
   - `created_at` (DATETIME UTC)

2. **`events`**
   - `id` (INTEGER, PK, autoincrement)
   - `user_id` (INTEGER, FK -> `users.id`, Index)
   - `timestamp` (DATETIME UTC, Index)
   - `type` (VARCHAR: `conversation`, `location`, `physiological`, `note`, Index)
   - `title` (VARCHAR)
   - `content` (TEXT)

3. **`permissions`**
   - `id` (INTEGER, PK, autoincrement)
   - `user_id` (INTEGER, FK -> `users.id`, Index)
   - `category` (VARCHAR)
   - `is_enabled` (BOOLEAN, default: True)
   - `updated_at` (DATETIME UTC)
   - *Constraint*: `Unique(user_id, category)`

4. **`privacy_rules`**
   - `id` (INTEGER, PK, autoincrement)
   - `user_id` (INTEGER, FK -> `users.id`, Index)
   - `category` (VARCHAR: `conversation`, `location`, `physiological`, `note`, `all`)
   - `rule_type` (VARCHAR: `keyword_redact`, `pattern_drop`, `threshold_redact`)
   - `pattern` (VARCHAR)
   - `action` (VARCHAR: `redact`, `drop`, `mask`)
   - `is_enabled` (BOOLEAN, default: True)
   - `created_at` (DATETIME UTC)

5. **`audit_logs`**
   - `id` (INTEGER, PK, autoincrement)
   - `timestamp` (DATETIME UTC, Index)
   - `user_id` (INTEGER, FK -> `users.id`, Index)
   - `action` (VARCHAR, e.g., `CREATE_EVENT`, `GET_EVENT_DETAIL`, `PERMISSION_SET_OFF`, `EXPORT_DATA`)
   - `event_type` (VARCHAR, optional category name)
   - `result` (VARCHAR, e.g., `ALLOWED`, `DENIED`, `CREATED`, `DELETED`, `EXPORTED_JSON`)

---

## Automated Test Coverage

The automated test suite in `backend/tests/` verifies both core requirements and advanced capabilities across 16 test cases:

### Core Privacy & Access Verification (`test_privacy_controls.py`, `test_events.py`, `test_audit_log.py`, `test_filtering_and_pagination.py`)
1. **`test_create_and_fetch_event`**: Creates an event via `POST /events` and verifies `GET /events/{id}` returns all required fields (`id`, `user_id`, `timestamp`, `type`, `title`, `content`).
2. **`test_delete_event`**: Deletes an event and asserts subsequent queries return `404 Not Found`.
3. **`test_event_validation_errors`**: Asserts invalid categories or empty titles return `422 Unprocessable Entity`.
4. **`test_type_filtering`**: Verifies `GET /events?type=conversation` returns exclusively conversation events.
5. **`test_pagination`**: Verifies `limit` and `offset` work correctly, returning non-overlapping pages and correct totals.
6. **`test_enabled_category_is_returned`**: Confirms enabled categories return data as expected.
7. **`test_disabled_category_is_not_returned_by_backend`**: Disables `physiological` category via API; asserts `GET /events` strictly excludes physiological items, and direct `GET /events/{id}` returns `403 Forbidden`.
8. **`test_changing_permission_affects_later_requests`**: Toggles permission `ON -> OFF -> ON` and verifies that later queries dynamically reflect permission state changes immediately.
9. **`test_audit_entries_created_for_important_actions`**: Confirms that creation, deletion, permission changes, and blocked direct accesses (`DENIED`) generate corresponding audit trail entries.
10. **`test_audit_log_is_read_only`**: Confirms that tampering attempts (`POST`, `PUT`, `DELETE` on `/audit-log`) are rejected with `405 Method Not Allowed`.
11. **`test_root_serves_frontend`**: Verifies the UI is served properly at `/`.

### Advanced Features Verification (`test_advanced_features.py`)
12. **`test_auth_registration_and_login`**: Tests JWT user registration, password hashing verification, token generation, and authenticated `/auth/me` profile lookup.
13. **`test_multi_tenancy_data_isolation`**: Verifies that User A's memory events and audit logs are strictly isolated and completely inaccessible to User B.
14. **`test_date_range_and_fulltext_search`**: Verifies time-slice queries (`start_date`, `end_date`) and case-insensitive full-text keyword search (`q`).
15. **`test_granular_privacy_rules_redaction_and_drop`**: Verifies dynamic in-memory keyword redaction (`[REDACTED BY PRIVACY RULE]`), pattern drop filtering, and rule deletion.
16. **`test_export_and_data_portability`**: Verifies GDPR Article 20 / CCPA data portability exports in JSON and CSV formats and confirms audit log recording (`EXPORT_DATA`).

---

## Short Engineering Note

### 1. Where is authorization enforced and why?
**Enforcement Point**: Authorization is enforced directly in the backend service layer (`PrivacyService` and `EventService`) immediately before any database query execution and before returning any single event payload.
**Why**: 
- Enforcing access controls only on the frontend is a fatal security flaw because malicious actors or API consumers can bypass UI controls with `curl`, Postman, or script automation.
- By enforcing permissions in the backend query layer, data is filtered at the database level (`WHERE type IN (:allowed_types)`). Restricted records are **never loaded into application memory** or sent over the wire, providing true data confidentiality and defense-in-depth.

### 2. What happens when a user requests data they are not allowed to see?
- **Collection Queries (`GET /events`)**: If a category is toggled OFF, events belonging to that category are omitted from the SQL result set. The response returns only events from enabled categories. If a user explicitly requests a disabled category via `GET /events?type=location`, the API returns an empty list `[]` and logs a filtered access in the audit log.
- **Direct Resource Queries (`GET /events/{id}`)**: If an event exists in the database but belongs to a disabled category, the backend halts execution and returns an **`HTTP 403 Forbidden`** response with a clear message: `"Access to '<category>' events is restricted by your active privacy settings"`.
- **Forensic Audit Entry**: A security audit log entry is immediately recorded with `action: "GET_EVENT_DETAIL"`, `event_type: "<category>"`, and `result: "DENIED"`, providing visibility into unauthorized access attempts.

### 3. What is one weakness that still exists in your implementation?
- **Synchronous Audit Log Commits**: Audit logs are committed synchronously in the same HTTP request database transaction. While this guarantees ACID consistency and prevents lost logs, under sustained write workloads (e.g., thousands of wearable telemetry events per second), writing synchronously to SQLite can introduce database lock contention.
- **In-Memory Rule Evaluation for Complex Patterns**: While keyword redactions and drops are evaluated dynamically in memory, evaluating deeply nested regex or contextual natural language privacy constraints (e.g. semantic ambiguity detection) at high request rates would benefit from dedicated pre-computed masking pipelines.

### 4. How would you change the system if it grew to 1 million events per user?
1. **Database Partitioning & Composite Indexing**:
   - Migrate to PostgreSQL and partition the `events` table by `(user_id, timestamp)` intervals (e.g., monthly partitions).
   - Add composite B-tree indexes on `(user_id, type, timestamp DESC)` to keep timeline lookups $O(\log N)$ instead of sequential table scans.
2. **Cursor-based Keyset Pagination**:
   - Replace offset pagination (`OFFSET n LIMIT m`, which becomes progressively slower as $n$ grows) with cursor-based keyset pagination using event timestamps (`WHERE user_id = :uid AND timestamp < :cursor ORDER BY timestamp DESC LIMIT :limit`).
3. **Distributed Permission Caching Layer**:
   - Cache user permission states in Redis with low TTL and cache-aside invalidation upon `PUT /permissions` to eliminate database reads for authorization checks.
4. **Asynchronous Append-Only Audit Stream**:
   - Decouple audit logging from the request-response loop using an asynchronous message broker (Kafka or AWS SQS / GCP PubSub) with worker pools batch-inserting into an analytical append-only store (ClickHouse or BigQuery).

### 5. What would you improve with one additional day?
Having completed Full Authentication & Multi-Tenancy, Date-Range & Full-Text Search, Automated Granular Privacy Rules, and GDPR/CCPA Export & Data Portability, the next engineering horizons would focus on:
1. **Client-Side Zero-Knowledge Encryption (E2EE)**:
   - Implement client-side key derivation (WebCrypto API) where event content is encrypted with a user-owned passphrase before reaching the backend. The backend would store encrypted blobs, and category tags would use homomorphic or order-revealing tokens so the server never possesses plaintext memory data.
2. **Cryptographic Audit Log Immutability (Merkle Trees / Verifiable Logs)**:
   - Implement cryptographic chaining for audit logs (similar to Certificate Transparency logs), where each audit entry contains a SHA-256 hash of the previous log entry (`prev_hash`). Daily Merkle tree roots could be signed or anchored to an external verifiable ledger to provide tamper-evident cryptographic proof of non-repudiation.
3. **Edge Processing & Enclave Execution**:
   - Deploy privacy rule evaluation inside Confidential Computing Enclaves (AWS Nitro Enclaves or AMD SEV) or on edge mobile devices, ensuring biometric signals and physiological feeds are filtered before transmitting across the WAN.
4. **Differential Privacy & Synthetic Telemetry Aggregation**:
   - Integrate differential privacy noise injection for aggregate health analytics (e.g. average weekly resting heart rate), allowing population-level medical insights without risking individual re-identification.
