# AGENTS.md — LEOPARD Agent Operating Rules

## 1. Project Identity

Project: LEOPARD — freight transport platform for Vietnam.

LEOPARD connects:

* SME shippers.
* Individual customers.
* Freelance truck/ba-gac drivers.
* Small fleet operators.
* Admin/operator users.

Core product domains:

* Authentication.
* Driver onboarding and verification.
* Vehicle management.
* Multi-stop freight booking.
* Realtime tracking.
* ETA prediction.
* Route optimization.
* VietQR/COD payment.
* Notification.
* Admin/fleet dashboard.

This repository is documentation-first. All implementation must follow the documents under `/docs`.

---

## 2. Mandatory Reading Order

Before writing, modifying, deleting, or generating code, every agent must read the project documents in this order:

1. `/docs/srs.md`
2. `/docs/architecture-design.md`
3. `/docs/erd.md`
4. `/docs/api-contract.md`
5. `/docs/tasks-allocation.md`
6. `/docs/development-guidelines.md`
7. `/docs/test-plan.md`
8. `/docs/wireframes.md` when working on UI/UX

Agents must not implement features from assumptions, memory, or external patterns if they conflict with these documents.

---

## 3. Source of Truth Priority

When documents overlap or conflict, apply this priority order:

1. `/docs/srs.md` — product requirements and scope.
2. `/docs/api-contract.md` — API endpoint names, request/response schema, WebSocket payloads.
3. `/docs/erd.md` — database schema, naming convention, indexes, constraints, migration source.
4. `/docs/architecture-design.md` — module structure, clean architecture, service boundaries.
5. `/docs/tasks-allocation.md` — Dev A/Dev B ownership and handoff protocol.
6. `/docs/development-guidelines.md` — coding workflow, sprint structure, dev rules.
7. `/docs/test-plan.md` — quality gate and Definition of Done.
8. `/docs/wireframes.md` — screen behavior and UI flow.

If a conflict is detected, the agent must stop and report:

* Conflict location.
* Conflicting statements.
* Recommended resolution.
* Files that must be updated.

The agent must not silently choose one side and continue.

---

## 4. Actor Classification

Before any task, classify the actor:

* Dev A — Backend & AI.
* Dev B — Frontend & Web/Mobile.
* Shared — requires backend/frontend split.

The response must begin with:

```md
### Actor
Dev A / Dev B / Shared
```

If the task is Shared, split into:

```md
### Dev A Scope
...

### Dev B Scope
...

### Handoff Contract
...
```

---

## 5. Directory Ownership

### Dev A — Backend & AI

Dev A owns:

```txt
/backend/
/docs/erd.md
/docker-compose.yml
/scripts/
/.github/workflows/
```

Dev A responsibilities:

* FastAPI backend.
* PostgreSQL/PostGIS/TimescaleDB schema.
* Alembic migrations.
* Redis integration.
* Firebase Admin SDK verification.
* JWT session issuing.
* API validation.
* Business logic services.
* Repositories.
* OR-Tools VRP service.
* XGBoost ETA service.
* OpenWeather integration.
* Vietmap/OSRM backend integration.
* WebSocket backend.
* Payment backend.
* Notification backend.
* Backend tests.
* Backend CI/CD.
* Docker Compose and deployment scripts.

### Dev B — Frontend & Web/Mobile

Dev B owns:

```txt
/frontend/
```

Dev B responsibilities:

* Flutter app.
* Flutter web dashboard.
* UI/UX implementation.
* Firebase Auth client.
* FCM client.
* Vietmap Flutter SDK.
* Map UI.
* Booking UI.
* Driver UI.
* Tracking UI.
* Payment UI.
* Dashboard UI.
* Bloc/Cubit state management.
* Dio HTTP client.
* WebSocket client.
* Mock-first API integration.
* Frontend tests.
* Frontend lint/analyze.

### Shared Files

Shared files require agreement before modification:

```txt
/docs/api-contract.md
/docs/wireframes.md
/docs/srs.md
```

No agent may change shared files without explicitly stating why and what implementation impact the change creates.

---

## 6. Hard Boundary Rules

Dev B must not edit:

```txt
/backend/
/docker-compose.yml
/scripts/
/.github/workflows/
/docs/erd.md
```

Dev A must not edit:

```txt
/frontend/
```

Exception: a Shared task may require both sides, but each side must only modify its owned directories.

No agent may bypass this rule for convenience.

---

## 7. Absolute Path Policy

When referring to files in explanations, plans, patches, or commands, agents must use absolute paths.

Default Windows project root:

```txt
C:\Users\tct31\project\LEOPARD
```

Default Linux/container project root:

```txt
/workspace/LEOPARD
```

If the actual project root is different, the agent must detect it or ask the user to confirm.

Do not use ambiguous paths like:

```txt
src/...
./backend
../frontend
```

---

## 8. API Contract Rules

`/docs/api-contract.md` is the API source of truth.

Agents must not rename endpoints, fields, enum values, payload shapes, or WebSocket event schemas without updating `/docs/api-contract.md`.

Before implementing any API:

1. Verify endpoint exists in `/docs/api-contract.md`.
2. Verify request body schema.
3. Verify response body schema.
4. Verify authentication requirement.
5. Verify role requirement.
6. Verify error cases.
7. Implement backend validation.
8. Add backend tests.
9. Update API docs if behavior changes.

If another document references a different endpoint name, report the conflict before coding.

Known area to verify carefully:

* OTP verification endpoint naming.
* Booking/order endpoint naming.
* WebSocket tracking path.
* ETA endpoint naming.
* VRP/optimization endpoint naming.

---

## 9. Database & Migration Rules

`/docs/erd.md` is the database source of truth.

Only Dev A can modify database schema.

Before creating or changing a migration:

1. Read `/docs/erd.md`.
2. Check naming convention.
3. Check foreign keys.
4. Check indexes.
5. Check constraints.
6. Check enum values.
7. Check backward compatibility.
8. Update `/docs/erd.md` if schema changes.
9. Add migration tests or at least migration verification steps.

Database conventions:

* Table names: plural snake_case.
* Column names: snake_case.
* Index prefix: `IX_`.
* Foreign key prefix: `FK_`.
* Unique constraint prefix: `UQ_`.
* Check constraint prefix: `CHK_`.
* Every transactional/core table should have `created_at` and `updated_at`.
* Use PostgreSQL as source of truth.
* Use PostGIS for spatial data.
* Use TimescaleDB hypertable for GPS tracking.
* Use Redis for cache, Pub/Sub, rate limiting, and realtime presence.

No destructive migration is allowed without rollback plan and explicit approval.

---

## 10. Architecture Rules

Backend must follow FastAPI Clean Layered Architecture:

```txt
/backend/app/api/
/backend/app/schemas/
/backend/app/models/
/backend/app/services/
/backend/app/repositories/
/backend/app/core/
/backend/app/workers/
/backend/alembic/
/backend/tests/
```

Layering rule:

* API layer handles HTTP/WebSocket boundary only.
* Schema layer handles request/response validation.
* Service layer handles business logic.
* Repository layer handles database access.
* Core layer handles shared infrastructure.
* Worker layer handles background jobs.
* Model layer maps database tables.

Do not put business logic directly inside API route handlers.

Do not query the database directly from UI-facing handlers if a repository/service layer exists.

Frontend must follow feature-based Flutter architecture:

```txt
/frontend/lib/features/<feature>/data/
/frontend/lib/features/<feature>/domain/
/frontend/lib/features/<feature>/presentation/
```

State management should use Bloc/Cubit for non-trivial flows.

---

## 11. Mock-First Workflow

Frontend and backend development must follow Mock-First Workflow:

1. Dev A and Dev B agree on `/docs/api-contract.md`.
2. Dev B builds UI using mock JSON that exactly matches API contract.
3. Dev A implements real API.
4. Dev A validates API through Swagger and tests.
5. Dev B switches Dio client from mock mode to backend mode.
6. Integration testing validates the flow end to end.

Mock data must never diverge from `/docs/api-contract.md`.

Mock mode must be clearly isolated and disabled in production builds.

---

## 12. Production Code Standard

Agents must not generate:

* Placeholder code.
* TODO-only implementation.
* Fake business logic unless explicitly requested.
* Silent catch blocks.
* Hardcoded secrets.
* Unvalidated request payloads.
* API without authentication/authorization where required.
* Database writes without transaction where atomicity is required.
* Public document URLs for sensitive driver documents.
* UI screens without loading/error/empty states.
* Code that only works for happy path.

Every implementation must include:

* Validation.
* Error handling.
* Logging where relevant.
* Role/permission check where relevant.
* Tests or clear test instructions.
* Documentation update if behavior changes.
* Rollback consideration.

---

## 13. Security Rules

Sensitive files include:

* Driver license images.
* Vehicle registration documents.
* Identity documents.
* Order proof images.
* Payment records.

Sensitive files must not be exposed through unauthenticated public URLs.

Document access must enforce:

* Owner access.
* Admin/operator access where appropriate.
* Audit log for review/approval actions.

Authentication:

* Use Bearer JWT for backend session.
* Verify Firebase token on server side for Firebase-based login.
* Store refresh tokens securely.
* Apply rate limit for auth and tracking endpoints.

Payment:

* Payment status must not become `paid` unless confirmed by trusted callback or authorized admin/operator action.
* Payment webhook handling must be idempotent.

---

## 14. LEOPARD Domain Rules

### Order/Booking

Booking/order must support:

* Multi-stop route.
* Pickup and drop-off stops.
* Cargo metadata.
* Vehicle constraints.
* Pricing.
* ETA.
* Payment state.
* Tracking state.

Invalid state transition must be rejected.

### Tracking

Realtime tracking must:

* Use WebSocket for live updates.
* Use Redis Pub/Sub for fanout.
* Persist GPS ticks into TimescaleDB according to configured interval.
* Support reconnect on frontend.
* Rate-limit driver location updates.
* Restrict customer visibility to their own order.
* Allow admin/operator visibility for active trips.

### ETA

ETA must:

* Use XGBoost service when available.
* Include weather, distance, time, vehicle, and traffic-related features when supported.
* Provide fallback to rule-based/provider ETA if ML inference fails.
* Log prediction inputs and outputs for evaluation.
* Track actual duration after trip completion.

### Route Optimization

Route optimization must:

* Use OSRM or Vietmap distance matrix where applicable.
* Use OR-Tools VRP for multi-stop optimization.
* Respect capacity constraints and time windows where defined.
* Return ordered stops and route metadata.
* Reject invalid/duplicate stops.

---

## 15. Testing Rules

Before claiming completion, run or specify exact tests.

Backend quality gates:

**Prerequisites:**
* Windows: `venv\Scripts\activate`
* Linux/macOS: `source .venv/bin/activate`
* Ensure dev dependencies are installed: `pip install -r requirements.txt -r requirements-dev.txt`
* Ensure PostgreSQL and Redis are running: `docker compose up -d postgres redis`

```txt
cd C:\Users\tct31\project\LEOPARD\backend
pytest
pytest --cov
```

Expected backend target:

* Service layer unit test coverage: at least 70%.
* Critical auth/order/payment/tracking tests must pass.
* OR-Tools route optimization benchmark must meet documented target.
* ETA evaluation must meet documented target when dataset exists.

Frontend quality gates:

**Prerequisites:**
* Ensure dependencies are retrieved: `flutter pub get`

```txt
cd C:\Users\tct31\project\LEOPARD\frontend
flutter analyze
flutter test
```

Expected frontend target:

* No new analyzer errors.
* No new linter warnings.
* Bloc/domain logic coverage target: at least 60%.
* Critical booking/tracking/payment UI flows must be tested.

Integration targets:

* API CRUD P95 under documented threshold.
* WebSocket supports documented concurrent connections.
* Payment flow is idempotent.
* Tracking reconnect works under simulated network interruption.

If tests cannot be run, the agent must clearly state why and provide the exact command the user should run. Do not claim completion if tests fail or if the testing environment is blocked without explicitly reporting the block.

---

## 16. Documentation Update Rules

When implementation changes behavior, update the relevant docs:

* API changed → update `/docs/api-contract.md`.
* DB schema changed → update `/docs/erd.md`.
* Architecture changed → update `/docs/architecture-design.md`.
* Task ownership changed → update `/docs/tasks-allocation.md`.
* Test strategy changed → update `/docs/test-plan.md`.
* UI flow changed → update `/docs/wireframes.md`.
* Setup/deployment changed → update README or `/docs/development-guidelines.md`.

Never let docs and implementation drift silently.

---

## 17. Conflict Detection Rules

Before coding, agents must check for contract conflicts.

Examples of conflict:

* One document says `/auth/verify`, another says `/auth/phone/otp-verify`.
* One document says `/orders`, another says `/bookings`.
* One document says Socket.IO, another says native WebSocket.
* One document says local upload public URL, another requires private document access.
* One document says cost-constrained MVP, another says production-first without cost constraint.

When conflict exists:

1. Stop implementation.
2. Report the conflict.
3. Recommend a resolution.
4. Ask for confirmation if the change affects API, DB, architecture, or scope.

---

## 18. Response Format for Agents

For every task, respond using:

```md
### 1. Actor
Dev A / Dev B / Shared

### 2. Mục tiêu
...

### 3. Tài liệu đã kiểm tra
- Absolute paths only.

### 4. Phân tích hiện trạng
...

### 5. Kế hoạch triển khai
...

### 6. File sẽ đọc
- Absolute paths only.

### 7. File sẽ thay đổi
- Absolute paths only.

### 8. Acceptance Criteria
- Measurable criteria.

### 9. Test Plan
- Exact commands when possible.

### 10. Risks & Mitigation
...

### 11. Rollback Plan
...

### 12. Next Action
...
```

Do not produce vague implementation plans.

---

## 19. Completion Checklist

A task is complete only when:

* Correct actor was identified.
* Required docs were read.
* Directory ownership was respected.
* API contract was respected.
* DB schema was respected.
* Implementation compiles.
* Lint passes.
* Tests pass or exact reason is reported.
* No placeholder code remains.
* No hardcoded secret exists.
* Error handling exists.
* Validation exists.
* Auth/role check exists when required.
* Documentation is updated when needed.
* Acceptance criteria are satisfied.
* Risks and rollback plan are documented.

If any item fails, the agent must not claim completion.

---

## 20. Recommended First Implementation Order

Since LEOPARD has two developers working in parallel (Dev A — Backend & AI; Dev B — Frontend & Web/Mobile), the implementation order is split into two parallel tracks.

### Track A: Dev A (Backend & AI)

```
Phase 1 — Foundation (Week 1-2)
  1. Repository skeleton & directory structure verification.
  2. Docker Compose validation (postgres + redis + backend containers).
  3. PostgreSQL/PostGIS/TimescaleDB migration baseline (Alembic init).
  4. FastAPI application skeleton (main.py, config.py, core modules).

Phase 2 — Core API (Week 3-6)
  5. Auth API (OTP request/verify, Google sign-in, JWT issuing).
  6. User/profile API.
  7. Driver/vehicle/document API.
  8. Booking/order API.
  9. Pricing API.
 10. VietQR payment API.
 11. WebSocket tracking API (Redis Pub/Sub + real-time location).

Phase 3 — AI & Integration (Week 7-9)
 12. ETA baseline (XGBoost model training pipeline + inference API).
 13. OR-Tools VRP optimization (background Celery worker).
 14. Notification API (FCM dispatch).
 15. Admin/fleet dashboard API.

Phase 4 — Hardening (Week 10-13)
 16. Production hardening (rate limiting, security audit, backup).
 17. Load testing & performance tuning.
```

### Track B: Dev B (Frontend & Web/Mobile)

```
Phase 1 — Skeleton (Week 1-2)
  1. Flutter project skeleton (clean architecture, directory structure).
  2. Theme, routing (GoRouter), core widgets (Dio client, WebSocket client).
  3. Firebase project setup (Auth SDK, FCM, crashlytics).

Phase 2 — Auth & Mock-First UI (Week 3-6)
  4. Auth UI (OTP login page, Google sign-in, role selection).
  5. Driver onboarding UI (document upload, vehicle registration).
  6. Booking UI (multi-stop address input, vehicle selection, fare display).
  7. Payment UI (VietQR code display, payment confirmation).

Phase 3 — Real-time & Dashboard (Week 7-9)
  8. Tracking UI (real-time map with driver marker, ETA countdown, chat).
  9. Driver navigation UI (truck-friendly routing map).
 10. Fleet dashboard (Flutter Web — charts, driver list, revenue).
 11. Admin portal (document approval, user management, pricing config).

Phase 4 — Integration & Polish (Week 10-13)
 12. Switch from mock data to real backend API.
 13. End-to-end integration testing.
 14. Offline caching polish, UI refinement.
 15. APK/IPA build and deploy.
```

### Integration Checkpoints

| Milestone | Track A must have | Track B must have | Integration point |
|---|---|---|---|
| **M1** (Week 3) | Auth API (real endpoints) | Auth UI (mock → real) | `/auth/*` contract verified |
| **M2** (Week 7) | Booking + Payment + Tracking APIs | Booking + Payment + Tracking UIs | E2E order creation flow |
| **M3** (Week 9) | ETA + VRP + Notification APIs | Dashboard + Navigation UIs | Full feature integration |
| **M4** (Week 13) | Production deployment | Final build + docs | System sign-off |

---

## 21. Error Recovery Protocol

When an AI agent makes a mistake (e.g., creates a file in the wrong directory, writes an incorrect migration, or modifies code outside its ownership scope), follow this protocol:

### 21.1. Wrong Directory — Agent created files outside its ownership

1. Stop immediately.
2. Report the misplaced files with absolute paths.
3. Use `git checkout -- <file>` to restore original state (if file was modified) or `git clean -fd <path>` (if new files were created).
4. Re-assess the task with correct directory ownership.

### 21.2. Incorrect Migration — Migration has already been applied

1. Do **not** modify the already-applied migration file.
2. Create a **new** migration to correct the schema change (`alembic revision -m "fix_<issue>"`).
3. If the incorrect migration must be dropped entirely:
   - Rollback: `alembic downgrade -1`
   - Delete the migration file.
   - Re-verify the current database state matches `/docs/erd.md`.

### 21.3. API Contract Violation — Endpoint or schema changed without doc update

1. Revert the implementation to match `/docs/api-contract.md`.
2. If the change is intentional and requested by the user, update `/docs/api-contract.md` **first**, then redo the implementation.
3. Notify the cross-track developer (Dev A ↔ Dev B) that the contract changed.

### 21.4. Test or Lint Failure After Code Change

1. Read the full error output.
2. Fix the error in the same file that was changed (do not widen the scope).
3. Re-run the failing test/lint command.
4. If the fix requires changes in files outside your ownership, **stop** and request a Shared task.

### 21.5. Scope Creep — Agent modified more files than needed

1. Use `git diff --name-only` to list all changed files.
2. Identify files that were changed but do not belong to the task.
3. Revert those files with `git checkout -- <file>`.
4. Review why the scope expanded and add a constraint to the task description.

### 21.6. Migration Downgrade Procedure

```txt
cd C:\Users\tct31\project\LEOPARD\backend
alembic downgrade -1          # Roll back the most recent migration
alembic current               # Verify current revision
# Delete the incorrect migration file from alembic/versions/
# Fix and regenerate: alembic revision --autogenerate -m "corrected_migration"
alembic upgrade head          # Re-apply corrected migration
```

### 21.7. Container / Environment Error

1. If Docker containers fail to start: `docker compose logs <service>` and report the error.
2. If environment variables are missing: check `.env.example` for required keys, report which key is missing.
3. If port conflicts exist: use `docker compose down` before `docker compose up -d`.

### 21.8. Agent Stuck or Uncertain

1. State clearly what is unclear.
2. List the exact files read so far.
3. Ask a specific clarifying question (not "what should I do?" but "should I use approach A (direct SQL) or approach B (ORM query) for this spatial search?").

---

## 22. AI Agent Behavior & Interaction Rules

### 22.1. What Agents CAN Do Autonomously

- Read project documentation (mandatory).
- Read any code file in the repository.
- Plan implementation and present it for review.
- Generate code within their owned directories.
- Run lint, analyze, and tests on their own code.
- Create feature branches following naming conventions.
- Commit code after the developer has reviewed and approved the plan.

### 22.2. What Agents MUST NOT Do Autonomously

- **Commit code** without the developer's explicit approval or instruction.
- **Push code** to remote (`origin`) without the developer's explicit instruction.
- **Merge** Pull Requests without the developer's explicit instruction.
- **Create branches** with names that deviate from the naming convention (`feature/xxx`, `bugfix/xxx`).
- **Modify shared files** (`/docs/api-contract.md`, `/docs/wireframes.md`, `/docs/srs.md`) without explicit permission.
- **Modify files outside** their ownership directory.
- **Delete branches** (even local ones) without confirmation.
- **Run destructive commands** (`git reset --hard`, `git push --force`, `docker compose down -v`) without confirmation.
- **Access external APIs** (Vietmap, Firebase, OpenWeather) using real credentials in test environments without developer confirmation.

### 22.3. Branch Naming Convention

- New features: `feature/<short-description>` (e.g., `feature/auth-otp`, `feature/vietmap-routing`).
- Bug fixes: `bugfix/<short-description>` (e.g., `bugfix/ws-reconnect-loop`).
- Documentation updates: `docs/<short-description>` (e.g., `docs/update-api-contract-v2`).
- Do not create generic branch names like `feature/new`, `fix/bug`, or `test`.

### 22.4. Commit Message Convention

Use Conventional Commits format:

```
feat(<scope>): <short description>
fix(<scope>): <short description>
docs(<scope>): <short description>
test(<scope>): <short description>
refactor(<scope>): <short description>
chore(<scope>): <short description>
```

Scopes: `auth`, `booking`, `tracking`, `payment`, `eta`, `vrp`, `driver`, `dashboard`, `admin`, `db`, `ci`, `docs`.

### 22.5. Pull Request Requirements

Before marking a PR as ready for review:

1. All CI checks must pass (lint + test).
2. PR title must follow Conventional Commits.
3. PR description must include:
   - What was changed.
   - Which actor (Dev A / Dev B / Shared).
   - Which docs were updated.
   - Testing evidence (screenshot or test run output).
   - Rollback steps if applicable.
4. PR must not contain merge conflicts with `dev`.

### 22.6. When to Escalate

Stop and escalate to the developer when:

- A document conflict is detected (see Section 17).
- The task requires modifying files outside your ownership.
- The task requirements are ambiguous and could be interpreted in multiple conflicting ways.
- The implementation would break backward compatibility.
- A security concern is identified that is not addressed in the documentation.
- A dependency or external service is unavailable and the fallback is not specified.
