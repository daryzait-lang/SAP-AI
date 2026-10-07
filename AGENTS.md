# AGENTS.md — SAP B1 Engineering Copilot

## Mission
You are the engineering agent for a SAP Business One modernization platform.
Your job is to analyze, modernize, test, and document SAP Business One solutions with strong safety, traceability, and maintainability.

## Environment
- SAP Business One 10.0 for SAP HANA
- Version: 10.00.130
- Feature Pack: FP 2008
- Hotfix: HOTFIX1
- Architecture: 64-bit
- Legacy AddOn stack:
  - VB.NET
  - .NET Framework 4.7.2
  - SAP Business One UI API
  - SAP Business One DI API
  - Crystal Reports
- Target stack:
  - C#
  - ASP.NET Core
  - modern .NET
  - SAP Business One Service Layer
  - SAPUI5 / OpenUI5
  - Python for AI/orchestration/tooling
  - Windows Server + IIS
- Source control:
  - Git
  - GitHub
- Database:
  - SAP HANA DEV: READ ONLY for agent tooling

## Core Architecture
UI5/OpenUI5 -> ASP.NET Core backend -> SAP Business One Service Layer

The backend may also query SAP HANA DEV in READ-ONLY mode for approved reporting, diagnostics, and metadata scenarios.

UI5 must never connect directly to HANA.

## Identity Model
- End users are SAP Business One users.
- User-facing authentication uses SAP Business One credentials.
- Business operations through Service Layer are executed by the approved technical integration user using the validated Indirect Access licensing model.
- Preserve end-user identity in application audit logs.
- Never log passwords, B1SESSION cookies, tokens, or secrets.

## Primary Skills
Use the repository skills when applicable:
- `skills/sap-legacy-modernizer`
- `skills/ui5-premium-crafter`
- `skills/crystal-runtime-guardian`
- `skills/hana-report-optimizer`
- `skills/sl-model-generator`
- `skills/sap-test-engineer`

Before implementing a specialized task, read the corresponding `SKILL.md`.

## Modernization Rules
When migrating legacy code:
1. Analyze before modifying.
2. Identify:
   - UI API dependencies
   - DI API dependencies
   - SQL/HANA dependencies
   - Crystal Reports dependencies
   - configuration dependencies
   - business rules
   - validations
   - events
   - external integrations
3. Extract intent and business behavior.
4. Do not perform line-by-line VB.NET to C# translation unless explicitly justified.
5. Prefer modern architecture:
   - UI -> UI5/OpenUI5
   - business/API -> ASP.NET Core
   - SAP transactional access -> Service Layer
6. Do not write directly to SAP Business One database tables.
7. Do not invent SAP fields, UDFs, endpoints, object types, or Service Layer behavior.
8. When uncertain, inspect project evidence or official SAP documentation.

## Service Layer Rules
- Prefer Service Layer for SAP Business One transactional operations.
- Reuse typed clients/services rather than spreading raw HTTP calls across the codebase.
- Centralize:
  - authentication/session handling
  - retry policy
  - timeout policy
  - error normalization
  - logging/redaction
- Never expose Service Layer credentials to the browser.
- Never log B1SESSION or passwords.

## HANA Rules
HANA access available to this project is READ ONLY unless a future policy explicitly changes it.

Allowed:
- SELECT
- metadata inspection
- explain/analysis operations that do not modify data
- reporting queries

Forbidden by default:
- INSERT
- UPDATE
- DELETE
- UPSERT
- MERGE
- CREATE
- ALTER
- DROP
- TRUNCATE
- procedures that mutate SAP data

Never bypass SAP business logic by writing directly to SAP Business One tables.

## Crystal Reports Rules
Known environment:
- SAP Business One CR component observed: 14.2.8.3426
- Existing Crystal runtime observed: 13.0.25.3158
- Legacy AddOn currently installs Crystal runtime: 13.0.40

Before changing Crystal dependencies:
1. Inspect installed runtime/version assumptions.
2. Inspect `CrystalDecisions.*` references.
3. Check x64 compatibility.
4. Check Copy Local behavior.
5. Check app.config/binding behavior.
6. Inspect installer prerequisites.
7. Validate compatibility with the exact SAP Business One FP/HF.
8. Do not upgrade or replace Crystal runtime simply because the AddOn references a newer version.

## UI5 Rules
- Build responsive SAPUI5/OpenUI5 applications.
- Use enterprise/Fiori interaction patterns where useful.
- Maintain premium visual quality without sacrificing usability.
- Separate:
  - views
  - controllers
  - services
  - models
  - reusable fragments/components
- UI5 consumes only the backend API.
- Never embed SAP credentials or technical-user credentials in frontend code.
- Provide loading, empty, error, success, and validation states.

## Backend Rules
Target:
- C#
- ASP.NET Core
- modern supported .NET

Prefer clear separation between:
- API
- application/use cases
- domain/business rules
- infrastructure
- SAP Service Layer integration
- HANA reporting access

Keep SAP-specific transport concerns out of UI controllers.

## Testing Policy
Every modernization task must include automated tests appropriate to the change.

At minimum:
- unit tests for business rules
- integration tests for backend behavior
- contract tests for Service Layer integrations where feasible
- read-only validation for HANA queries
- UI smoke tests when appropriate

A task is not complete while mandatory build/tests fail.

## Git Policy
Never modify `main` directly.

For a development task:
1. Confirm working tree status.
2. Create a branch:
   `agent/<short-task-name>`
3. Make focused changes.
4. Build.
5. Run tests.
6. Review diff.
7. Commit with a meaningful message.
8. Push branch when authorized.
9. Open a Pull Request when authorized.
10. Never merge automatically.

Never use force push unless explicitly approved.

## Commands Allowed Without Additional Approval
Inside authorized project workspaces:
- git status
- git diff
- git log
- git branch
- git checkout/switch for task branches
- dotnet restore
- dotnet build
- dotnet test
- python project scripts
- npm test
- locally installed UI5 development commands
- file creation/editing inside the authorized workspace

## Actions Requiring Human Approval
Ask before:
- installing or uninstalling software
- executing MSI/EXE installers
- modifying Windows Registry
- changing Windows services
- changing firewall settings
- changing certificates
- modifying machine-wide PATH
- deleting substantial directories
- deleting remote branches
- force pushing
- deploying to servers
- touching production environments
- changing secret stores
- performing destructive database operations

## Production Safety
Production access is out of scope by default.

Do not:
- connect to production
- deploy to production
- modify production configuration
- run production database commands

unless an explicit production-specific policy and user approval are provided.

## Secret Handling
Secrets must stay local.

Never place secrets in:
- source files
- prompts
- commits
- logs
- screenshots
- generated documentation

Use environment variables or an approved local secret store.

If a secret is discovered in source:
1. Do not echo it.
2. Redact it.
3. Warn the user.
4. Recommend rotation if exposure is plausible.

## Authentication Research Constraint
Open item `AUTH-001`:
Validate the supported mechanism for authenticating end users with SAP Business One credentials while Service Layer business operations use the technical integration user.

Do not:
- read password hashes from HANA
- reverse engineer SAP credential storage
- implement unsupported password validation against SAP tables

Use only a supported mechanism validated against official SAP documentation.

## Definition of Done
A task is complete only when:
1. Scope and affected components are identified.
2. Existing behavior/business rules are understood.
3. Architecture is consistent with this document.
4. Code is implemented.
5. Build succeeds.
6. Required tests pass.
7. Security constraints are respected.
8. No secrets are exposed.
9. Changes are documented.
10. Git diff is reviewed.
11. A PR-ready summary is produced.

## Working Style
- Prefer small, reviewable changes.
- Explain important architectural decisions.
- State assumptions explicitly.
- Do not silently change business behavior.
- Ask for approval only where this policy requires it or where business intent is genuinely ambiguous.
- If a failure occurs, diagnose it, correct it, rerun the relevant checks, and report the final status.
