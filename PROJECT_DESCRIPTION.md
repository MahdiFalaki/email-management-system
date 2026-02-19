# Email Management System — Project Description

## What this app is
This project is a **Streamlit-based email workflow app** for managing contacts, reusable templates, outbound sends, reminders, and AI-assisted drafting support. Data is persisted locally with TinyDB (JSON file), and email delivery is done through Gmail-compatible SMTP via `yagmail`.

---

## Core architecture

- **UI Layer (Streamlit multipage app)**
  - Entry page: `src/Home.py`
  - Feature pages in `src/pages/`
- **Data Layer (`DatabaseManager`)**
  - `src/utils/db.py` wraps TinyDB tables for profiles, templates, sent emails, reminders, schedules, and a single user profile record.
- **Email Delivery Utility**
  - `src/utils/helpers.py` sends emails using env-based credentials (`EMAIL_SENDER`, `EMAIL_PASSWORD`).
- **LLM Layer (chatbot comparison)**
  - `src/llm/` provides a provider-agnostic pipeline with:
    - prompt construction
    - RAG over app data
    - safety guardrails
    - OpenAI + AWS Bedrock provider adapters
    - optional CloudWatch telemetry

---

## Available features (current, real state)

### 1) Home dashboard-like landing page
**What it does now**
- Shows static overview metrics (hardcoded values).
- Provides quick navigation buttons to Send Email, Templates, and Profiles pages.
- Displays a static "Recent Emails" table (hardcoded rows).

**What to know**
- This page is mostly **presentation/navigation**, not a live analytics dashboard yet.

**Main packages/skills involved**
- `streamlit` for layout, metrics, navigation.

---

### 2) Profiles management
**What it does now**
- Add contact profiles (name, email, title, profession).
- List all saved profiles.
- Delete existing profiles.

**Connections**
- Profiles are used as selectable recipients in the Send Email flow.

**Main packages/skills involved**
- `streamlit` forms/components.
- `tinydb` CRUD via `DatabaseManager`.

---

### 3) Email template management
**What it does now**
- Create reusable templates (name + body).
- List templates with read-only body preview.
- Delete templates.

**Connections**
- Templates feed directly into the Send Email composer as the starting body.

**Main packages/skills involved**
- `streamlit` form + text editors.
- `tinydb` CRUD via `DatabaseManager`.

---

### 4) Send Email (compose + send + schedule + reminders)
**What it does now**
- Select multiple recipients from saved profiles.
- Select one saved template.
- Optionally append saved user signature.
- Edit raw body and see live preview.
- Three actions:
  1. **Send Now** → sends immediately via `yagmail` and logs sent record.
  2. **Schedule** → stores a schedule record and sent-email metadata with future datetime.
  3. **Add Reminder** → stores reminder entries linked to sent-email records.

**Important reality checks**
- **Send Now is real** SMTP sending (if env credentials are set).
- **Schedule is storage-only right now**: there is no background worker/cron in this repo to automatically dispatch scheduled emails at due time.
- **Reminder creation is real data entry**, and reminders can be managed in the Reminders page.

**Main packages/skills involved**
- `streamlit` UI state/forms.
- `yagmail` SMTP send integration.
- `python-dotenv` for env loading.
- `tinydb` persistence for sent/scheduled/reminder data.
- `loguru` for send diagnostics.

---

### 5) Reminders page
**What it does now**
- Lists reminders from DB.
- Resolves and displays linked email subject/recipients/due date.
- Supports "Mark Done" and "Delete" actions (both remove reminder records).

**Main packages/skills involved**
- `streamlit` interactive list actions.
- `tinydb` reminder + sent email lookups.

---

### 6) User profile page
**What it does now**
- Stores one owner profile (name, degree, title, university, profession, social links, signature).
- Update existing profile or create if missing.

**Connections**
- Signature is consumed by Send Email page when "Add Signature" is toggled.

**Main packages/skills involved**
- `streamlit` forms.
- `tinydb` singleton-like profile persistence.

---

### 7) AI chatbot comparison page (OpenAI vs Bedrock)
**What it does now**
- Side-by-side chat panels for two providers:
  - OpenAI
  - AWS Bedrock (Nova Micro default model ID)
- Sends the same user prompt to both providers.
- Displays per-provider metrics: latency, token usage (if available), response chars.
- Shows delta metrics between providers.
- Includes connection test buttons for each provider.

**Built-in AI safety and grounding**
- Input guardrails detect direct action requests (send/delete/schedule/reminder execution-style prompts).
- Output guardrails block unsafe claims like "I sent it".
- Optional PII redaction (emails/URLs) in model output.
- RAG context is built from app data (profiles/templates/recent sent emails/user profile) and injected as system context.
- Fallback deterministic responses are returned when providers fail/unavailable.

**Main packages/skills involved**
- `openai` SDK integration.
- `boto3` Bedrock runtime + optional CloudWatch logs.
- Local RAG retrieval logic implemented in Python (token-overlap scoring).
- Guardrail patterns via `re` and prompt sanitization.
- `python-dotenv` env loading.

---

## Declared vs implemented pages (important)
The repository contains page files for:
- `5_📅_schedules.py`
- `6_🔍_search.py`
- `9_📊_dashboard.py`

These files are currently **empty** (no active feature implementation).

So, while database methods for schedules/search exist, the dedicated UI pages for schedules/search/dashboard are not yet implemented in this codebase.

---

## Data model snapshot
TinyDB tables currently used:
- `profiles`
- `templates`
- `sent_emails`
- `reminders`
- `schedules`
- `user_profile`

This makes the project fully local-first by default, with data saved in `email_manager.json`.

---

## Environment/config dependencies
To unlock full functionality, the app expects:
- Email sending:
  - `EMAIL_SENDER`
  - `EMAIL_PASSWORD`
- OpenAI chatbot:
  - `OPENAI_API_KEY`
  - optional `OPENAI_MODEL`
- Bedrock chatbot / telemetry:
  - AWS credentials + `AWS_REGION`
  - optional `BEDROCK_MODEL_ID`
  - optional telemetry flags (`LLM_ENABLE_CLOUDWATCH`, log group/stream env vars)

Without these, the UI still works, but provider/send capabilities degrade to safe failure messages.


---

## Suggested next steps roadmap

### Phase V1 (Local-first completion) — module-wise implementation plan
Goal: finish all local product-critical features with clear ownership by module.

---

### Module A — `src/pages/5_📅_schedules.py` (Schedules UI)
**Objective**: make scheduled emails visible and manageable.

**Implementation steps**
1. Render schedule list from `db.get_all_schedules()` with linked email details (`db.get_sent_email`).
2. Show schedule status (start with `pending`; later add `sent/failed/cancelled`).
3. Add actions per row:
   - reschedule (`db.update_schedule`) via date/time inputs,
   - cancel/delete (`db.delete_schedule`).
4. Add empty-state and validation messages.

**Definition of done**
- User can view, edit, and cancel schedules entirely from UI.

---

### Module B — `src/pages/6_🔍_search.py` (Search UI)
**Objective**: make sent-email history discoverable.

**Implementation steps**
1. Add search box wired to `db.search_sent_emails(query)`.
2. Add optional filters in UI (recipient contains / subject contains / date range).
3. Display results as cards/table with subject, recipients, sent date, excerpt.
4. Add "no results" and "missing query" UX states.

**Definition of done**
- User can reliably find prior emails by keyword and basic filters.

---

### Module C — `src/pages/9_📊_dashboard.py` + `src/Home.py` (Real metrics)
**Objective**: replace static placeholders with actual analytics from local DB.

**Implementation steps**
1. Build aggregate helpers (in page or utility):
   - total sent emails,
   - sent today / last 7 days,
   - top recipients,
   - simple daily trend.
2. Render dashboard KPIs and charts/tables from `db.get_all_sent_emails()`.
3. Update Home to show live summary metrics instead of hardcoded values.

**Definition of done**
- Metrics shown in Home/Dashboard reflect real persisted records.

---

### Module D — `src/utils/db.py` (Data model hardening)
**Objective**: support reliable execution states for local workflows.

**Implementation steps**
1. Extend schedule/reminder records with lifecycle fields:
   - `status`, `last_error`, `attempt_count`, `updated_at`.
2. Add helper methods:
   - `get_due_schedules(now)`,
   - `mark_schedule_sent(...)`,
   - `mark_schedule_failed(...)`.
3. Add lightweight idempotency key for schedule-linked sends.

**Definition of done**
- Data layer supports safe retries and clear execution visibility.

---

### Module E — Local scheduler runner (new module, e.g. `src/jobs/scheduler.py`)
**Objective**: make "Schedule" action actually execute at due time.

**Implementation steps**
1. Implement polling loop (local process) that:
   - fetches due schedules from DB,
   - sends via `send_email`,
   - updates status/attempt/error fields.
2. Add retry policy (e.g., max attempts + backoff).
3. Add simple lock/claim mechanism to avoid duplicate execution.
4. Provide local run command in README (separate from Streamlit app process).

**Definition of done**
- Due schedules are sent automatically without manual UI action.

---

### Module F — `src/pages/3_📧_Send_Emails.py` (Workflow alignment)
**Objective**: align sender UX with new schedule execution model.

**Implementation steps**
1. When scheduling, store explicit `pending` schedule records.
2. Show user-facing confirmation with schedule ID and planned send timestamp.
3. Improve validation:
   - block invalid recipient emails,
   - require non-empty subject/body semantics.
4. Ensure reminders reference stable email/schedule IDs.

**Definition of done**
- Send and Schedule flows are predictable, validated, and traceable.

---

### Module G — `src/pages/4_⏰_reminders.py` (Reminder lifecycle)
**Objective**: make reminder management complete.

**Implementation steps**
1. Add status badges (upcoming/overdue).
2. Add filter/sort controls (due soon, overdue, completed).
3. Keep current actions (done/delete) and optionally add "snooze".

**Definition of done**
- Reminder queue is actionable and easy to triage.

---

### Module H — `src/llm/*` (Assistant alignment with final V1 behavior)
**Objective**: keep assistant guidance consistent with implemented features.

**Implementation steps**
1. Update fallback/help messaging to mention real Schedules/Search/Dashboard pages.
2. Keep guardrails that prevent false action-claiming.
3. Add test coverage for guardrail and RAG retrieval behavior against new data fields.

**Definition of done**
- Chat assistant accurately describes what app can/cannot do locally.

---

### Module I — Testing and quality gates
**Objective**: stabilize V1 before considering hosted migration.

**Implementation steps**
1. Unit tests:
   - `DatabaseManager` CRUD + search + schedule status transitions,
   - guardrails (`is_action_request`, `contains_unsafe_action_claim`),
   - RAG chunk build/retrieval.
2. Integration tests (mocked SMTP):
   - send now,
   - schedule then dispatcher execution,
   - reminder creation and completion.
3. CI checks:
   - `ruff`,
   - test run,
   - optional type checks.

**Definition of done**
- Green automated checks with coverage on core workflows.

---

### Module J — Local operations (`.env.example`, docs, scripts)
**Objective**: ensure reproducible local setup for contributors.

**Implementation steps**
1. Add `.env.example` for sender, OpenAI, Bedrock, telemetry toggles.
2. Add seed/init script for TinyDB demo data.
3. Add runbook:
   - start Streamlit app,
   - start scheduler worker,
   - validate with a quick end-to-end local scenario.

**Definition of done**
- New contributor can run full V1 flow locally without guesswork.

---

### Suggested delivery sequence (sprint order)
1. **Data + execution core first**: Module D → Module E → Module F.
2. **Feature completion pages**: Module A → Module B → Module C → Module G.
3. **Assistant + quality**: Module H → Module I → Module J.

This order reduces rework: build reliable execution primitives first, then UI layers, then polish and verification.

---

### V2 decision checkpoint (after V1)
Once V1 acceptance criteria above are complete, moving to V2 hosted AWS architecture is the right next step.
- Keep Streamlit for quick operator workflows initially.
- Migrate persistence and scheduling to managed AWS services.
- Move production sending to SES and add observability/security baselines.
