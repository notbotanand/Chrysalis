# Changelog

All notable changes to Chrysalis are documented here. This project uses
[Semantic Versioning](https://semver.org/spec/v2.0.0.html):

- **MAJOR** — schema changes that require `data/` migration. Existing users
  must update `data/manifest.yaml`, card front-matter, or other structures.
  Migration notes live in `framework/MIGRATIONS/`.
- **MINOR** — new workflows, new commands, dashboard improvements. Additive.
- **PATCH** — prompt tweaks, bug fixes, documentation updates.

---

## [1.0.0] — 2026-05-31

### Added
- First public release at `https://github.com/notbotanand/Chrysalis`.
- Three-zone architecture: `framework/` (OS), `data/` (user content), `examples/` (read-only reference).
- `framework/index.yaml` as pure router (paths + schemas + rules); manifest and sweep state split into `data/manifest.yaml` and `data/state/sweep_state.yaml` respectively.
- Single-command onboarding (`Onboard me`) that chains profile setup → accounts setup → pipeline sweep.
- Workflows: profile-setup, accounts-setup, onboarding-sweep, company-research, prep-planner, debrief, schedule-advisor, morning-sweep, card-update, card-sync, pipeline-health-check, job-board-scan.
- Apple Mail MCP + Gmail MCP + Google Calendar MCP integration.
- Self-contained `dashboard.html` regenerator with kanban, prep readiness, market signals, weekly view.

### Notes
- Public repo ships with empty `data/`. Real content lives only on the maintainer's machine.
- `examples/` contains a fictional persona (Maya Patel) and two sample pipeline cards (Acme Payments, Globex Wallet) as illustrative reference — never loaded by any workflow.
