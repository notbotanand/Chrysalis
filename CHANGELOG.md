# Changelog

All notable changes to Chrysalis are documented here. This project uses
[Semantic Versioning](https://semver.org/spec/v2.0.0.html):

- **MAJOR** — schema changes that require `data/` migration. Existing users
  must update `data/manifest.yaml`, card front-matter, or other structures.
  Migration notes live in `framework/MIGRATIONS/`.
- **MINOR** — new workflows, new commands, dashboard improvements. Additive.
- **PATCH** — prompt tweaks, bug fixes, documentation updates.

---

## [1.1.0] — 2026-06-20

### Added
- **Dashboard generator CLI flags.** `framework/tools/generate_dashboard.py`
  gained `--data-dir`, `--output`, and `--no-open`. Lets dashboard
  generation target any data root and any output path without touching
  the canonical `data/` tree or `dashboard.html`. Useful for testing
  or running side-by-side dashboards.
- **`final_round` and `offer` kanban columns.** The pipeline kanban
  now shows companies that have reached final round or have an offer
  outstanding as their own columns, instead of bucketing them with
  `interviewing`.

### Changed
- **Manifest-first dashboard data loading.** Companies are now driven by
  `data/manifest.yaml` first; per-card files are read only for enrichment
  (full overview, contacts, prep notes). Manifest summary alone is enough
  to render the kanban — degrades gracefully if a card file is missing.
- **Stale-card badge shows day count.** Cards untouched for more than
  the `stale_card_days` threshold (default 7) now display the actual
  age (e.g. `stale · 9d`) instead of a binary flag.

### Notes
- No `data/` schema changes. No migration required.

---

## [1.0.2] — 2026-06-02

### Fixed
- **Empty dashboard after onboarding.** Card templates (`framework/templates/pipeline-card.md`, `framework/templates/profile.md`) and the workflows that write the manifest (`onboarding-sweep.md`, `profile-setup.md`, `card-sync.md`) all documented `card_id: data/pipeline/<slug>` and `id: data/pipeline/<slug>`. The dashboard generator (`framework/tools/generate_dashboard.py`) skips any manifest entry whose `id` doesn't start with exactly `pipeline/` — so every newly created card was silently dropped. Fixed by stripping the `data/` prefix from all template / workflow examples and adding an explicit note in `framework/index.yaml → schemas.manifest_entry` and `CLAUDE.md → Card update rules` that IDs are logical, not filesystem paths. Existing user manifests (which already used the correct format) are unaffected.

### Added
- **`Onboard me` now runs the first Brief automatically.** New Step 4 in the `Onboard me` chain in `CLAUDE.md` fires the full Brief flow as soon as the onboarding sweep commits — validates plumbing end-to-end, populates `dashboard.html`, and surfaces the day-one next action without the user having to ask.

### Notes
- No `data/` schema changes. The fix is purely in the framework prose Claude reads to know what to write. Users on 1.0.0 / 1.0.1 with already-correct manifests need no migration; users whose Claude wrote `data/`-prefixed IDs should run a one-shot rewrite: `sed -i '' 's|id: data/pipeline/|id: pipeline/|g; s|id: data/profile/|id: profile/|g' data/manifest.yaml` and the equivalent for `card_id:` / `linked_cards:` in card front-matter.

---

## [1.0.1] — 2026-06-02

### Added
- **Repository safety gate.** New top-of-CLAUDE.md guard runs `git remote get-url origin` before any write. If `origin` points at the public template (`notbotanand/Chrysalis`), Chrysalis hard-stops and offers three resolution paths (fork on GitHub, local-only mode, custom remote). Defense-in-depth check also added at the top of `profile-setup.md` Step 1 so the first writable step in the `Onboard me` chain catches gate violations even if a workflow is run directly.
- **Connection smoke test in `accounts-setup`.** New Step 7 verifies email read, calendar read, and a throwaway calendar write+delete against the configured `write_target` for each account before committing the config. `accounts.yaml` now carries a `verification:` block with `last_verified` + per-test pass/fail state. Failures hard-stop with the most likely fix path.
- **Auto-discovery onboarding sweep.** `onboarding-sweep.md` Step 3 now pulls the user's pipeline from a 14-day email back-sweep and a (−14, +30)-day calendar window instead of asking the user to list companies. User confirms/extends; the sweep is the primary intake.

### Changed
- **`accounts-setup` is now provider-first and OS-agnostic.** Workflow starts by asking "which providers?" instead of enumerating Apple Calendar. Host OS is detected via `uname -s`; JXA and Mail.app paths only offered on Darwin.
- **Connector preference order is now an explicit 5-tier rule** carried in CLAUDE.md, accounts-setup, and README:
  1. First-party provider MCP (Gmail, Google Calendar, MS Graph)
  2. Aggregator MCP (Composio — licensed, supported)
  3. Community single-provider MCP (Apple Mail MCP — open source, no warranty)
  4. OS scripting (JXA on Mac)
  5. Paste mode
- **Composio is now the recommended path for consumer Outlook `@outlook.com`** — verified working in 1.0.1 (MS Graph search rejects consumer accounts). New `mcp:` values `composio-gmail` and `composio-outlook`; new `write_mechanism:` values `composio_outlook` and `composio_google_calendar`.
- **README Setup step now mandates a user-owned fork** (or explicit local-only mode) before any writes happen. The `[yourname]` placeholder is replaced with concrete fork-or-localize instructions.

### Notes
- No `data/` schema changes. Existing users on 1.0.0 can pull and continue — no migration required.
- Public repo `notbotanand/Chrysalis` rebuilt from the cut tool. History is single-commit by design (`init: Chrysalis v1.0.1 — first public release` per the cut tool's commit message format).

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
