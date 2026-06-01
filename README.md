# Chrysalis

A personal AI operating system for job search and career transition.
Built entirely on Claude Code — one tool, local files, no connectors required.

Chrysalis keeps your pipeline, research, interview prep, and market signals
organized in a private GitHub repo. Claude Code reads and writes directly.
Every session starts informed. Every insight gets saved. Every interview
makes the next one better.

---

## How it works

```
~/chrysalis-kb/                              ← your private repo, cloned locally
    CLAUDE.md                                ← read by Claude Code at startup
    README.md, USER_GUIDE.md                 ← human-facing docs
    framework/                               ← the OS — same for every user
        index.yaml                           ← router + schema, read first every session
        workflows/                           ← plain-English instructions Claude follows
        templates/                           ← skeletons for new cards
        tools/generate_dashboard.py          ← regenerates dashboard.html
    data/                                    ← YOUR data — populated by onboarding
        profile/me.md                        ← always loaded: background, targets, constraints
        pipeline/                            ← one card per company
        config/accounts.yaml                 ← email + calendar configuration
        market/digest.md                     ← signals from job scans
        logs/today/, logs/weekly/            ← daily brief + weekly reflections
    examples/                                ← read-only reference: fictional persona + sample cards
    dashboard.html                           ← generated on each Brief (gitignored)
```

You run `claude` in the repo directory. Claude Code reads `CLAUDE.md`,
loads the index, and is immediately ready. No connectors, no accounts,
no external services required.

---

## Setup (~20 minutes)

### 1 — Fork and clone

```bash
git clone https://github.com/[yourname]/[repo-name] ~/chrysalis-kb
cd ~/chrysalis-kb
claude
```

### 2 — Run onboarding

```
"Onboard me."
```

This single command runs a three-step chain:

1. **Profile** — attach your resume. Claude extracts your background, asks 4–5
   clarifying questions, and writes `data/profile/me.md`.
2. **Accounts** — Claude lists the calendars on your Mac and asks which email
   accounts you check for job-search mail, then writes `data/config/accounts.yaml`.
   This is what lets Chrysalis read interview signals and write prep blocks.
3. **Pipeline** — tell Claude about the companies you're currently in process
   with (paste recruiter emails if you have them). Claude creates a card per
   company, auto-researches any with an active interview process, and updates
   the index.

Everything is committed to your repo as it's written. Total: about 20 minutes.

> **Running individual steps later?** Each step has its own command:
> `Set up my profile`, `Update my accounts`, `I'm ready to start`.
> Use these when you want to refresh one piece without re-running the rest.

### 3 — Start using it

Say `Brief` each morning. Claude reads your cards, searches for news on your
target roles and companies, flags anything stale, and gives you a structured briefing.

---

## Commands

| Say this | What happens |
|---|---|
| `Brief` | Morning briefing — pipeline health, industry news, what needs attention today. Writes signals to digest and opens dashboard. |
| `Research [company]` | Web research → profile-aware analysis → card written and committed |
| `Prep for [company] interview` | Research the company's interview process, build round-specific prep plan, study schedule |
| `Debrief [company]` | Post-round capture — what happened, what to fix, next round intel. Run within 2 hours. |
| `When can I schedule [company]?` | Scheduling recommendation with prep load, downstream commitment, calendar analysis |
| `Am I over-scheduled?` | Pipeline density report — interview count, prep coverage, what to prioritize |
| `Where do I stand` | Weekly pipeline summary and reflection |
| `Scan job boards` | Targeted search based on your profile, results written to digest |

---

## Dashboard

Every morning brief generates `dashboard.html` — a self-contained visual overview
that opens automatically in your browser. No server, no login, no dependencies.

| Section | What it shows | Interactive |
|---|---|---|
| Header | Your name, date, week of search, active process count | — |
| Upcoming calls | Interviews in the next 3 days with time and round type | — |
| Week strip | Mon–Fri with call density (blue = calls, amber = heavy day) | Click a day → overlay listing all scheduled calls |
| Pipeline | Kanban view: Interviewing / Screening / Applied | Tier 1 badge, prep bar, next action per card |
| Industry pulse | Latest signals from `data/market/digest.md`, newest first | Click → opens source article in new tab |
| Prep readiness | Progress bar for every active company, ⚠ if under 40% | Click → overlay showing what's done, what's missing, next action |

Regenerate at any time without running a full brief:

```bash
python3 framework/tools/generate_dashboard.py
```

The dashboard reads directly from the repo — pipeline cards, `data/market/digest.md`,
and `data/profile/me.md` (for your name in the header). It reflects current state
every time it's generated.

---

## The interview lifecycle

The real value of Chrysalis is that it compounds. Each interview makes the next one better.

```
Company enters pipeline
        ↓
Research [company] → card populated with profile-aware analysis
        ↓
Prep for [company] interview →
    Phase 1: Research this company's actual interview process (not a template)
             Confirm with you → written to company card permanently
    Phase 2: Round-specific prep — stories mapped to what THIS round tests
    Phase 3: Dated study plan built around your calendar
        ↓
Interview happens
        ↓
Debrief [company] →
    What came up, what landed, what to fix
    Next round details captured → card updated
    Prep for next round offered immediately
        ↓
Repeat for each round → card gets richer → prep gets sharper
```

The company card is the long-term memory. After a debrief, the next prep run
already knows what round is coming, what the interviewer cares about, and what
you said in the last round.

---

## How the knowledge base works

### Cards

Every file is a "card" — a Markdown file with YAML front-matter. Claude reads
only the cards relevant to your request. It never reads the whole repo.

| Card type | Location | Contains |
|---|---|---|
| Personal profile | `data/profile/me.md` | Background, target role, constraints. Always loaded. |
| Company pipeline | `data/pipeline/[company].md` | Research, contacts, interview process, round notes |
| Market digest | `data/market/digest.md` | Job scan results, market signals |
| Weekly log | `data/logs/weekly/[YYYY-WNN].md` | Weekly reflections |

### The index

`framework/index.yaml` is read first, every session. It has a one-line summary of every
card and controls which ones Claude loads for a given request. Stage, next action,
and priority are tracked here so the morning brief is fast and focused.

### The Interview Process section

Every company card has an **Interview Process** section. It starts empty.
The first time you run `Prep for [company]`, Claude researches what that company
actually does for your role profile — web searches, Glassdoor, Blind, community posts.
It presents the findings, you confirm or correct them, and they're written to the card.

This section is the source of truth for that company's process. It gets updated after
every debrief as new round details emerge. By the time you're in final rounds, it's
a complete picture built from research plus direct recruiter intelligence.

### Writes

Claude Code writes directly to the repo, commits, and pushes after every significant
action. You don't edit files manually unless you want to.

---

## Adding a company

**The fast way:** Say `Research [company]` — Claude does full web research,
generates a profile-aware analysis, writes the card, and updates the index.

**The manual way:**
1. Copy `framework/templates/pipeline-card.md` to `data/pipeline/[company-name].md`
2. Add an entry to `framework/index.yaml`
3. Fill in what you know — Claude will fill the rest on the next research run

---

## Email and calendar

**Apple Mail MCP connector** — if you use Apple Mail, install
`falconbradley/claude-connector-apple-mail` and configure it in `~/.claude.json`.
Claude Code will use it to sweep recent recruiter emails and update pipeline cards.

**Calendar** — Claude reads Apple Calendar via JXA (JavaScript for Automation)
to check your schedule when building prep study plans and answering scheduling
questions. No special setup needed.

**Fallback** — if neither is connected, Claude asks you to paste or describe what's
relevant and incorporates what you share.

---

## Workflow reference

| Workflow file | What it does |
|---|---|
| `profile-setup.md` | Populate `data/profile/me.md` from a resume |
| `onboarding-sweep.md` | One-time setup — extract pipeline from user input and email |
| `morning-sweep.md` | Daily sweep (runs as part of the Brief command) |
| `company-research.md` | Deep web research on a company |
| `prep-planner.md` | Three-phase prep: process research → round prep → study plan |
| `debrief.md` | Post-round capture — update card, assess signals, offer next prep |
| `schedule-advisor.md` | Chief of Staff scheduling — calendar density, downstream load |
| `job-board-scan.md` | Scan job boards for matching roles |
| `pipeline-health-check.md` | Flag stale cards and missed follow-ups |

All workflows are plain English. Claude Code reads and executes them.
You can read and edit them — they are just text files.

---

## Git commit convention

| Action | Commit message |
|---|---|
| Initial setup | `init: onboarding sweep YYYY-MM-DD` |
| Profile update | `update: data/profile/me [what changed]` |
| New company card | `add: data/pipeline/[company] initial research` |
| Card update | `update: data/pipeline/[company] [what changed]` |
| Debrief | `update: data/pipeline/[company] debrief round N YYYY-MM-DD` |
| Morning brief | `sweep: YYYY-MM-DD morning run` |
| Weekly log | `log: YYYY-WNN weekly reflection` |

---

## FAQ

**Do I need any connectors or external services?**
No. Claude Code reads and writes local files directly. No connectors, no APIs,
no accounts beyond GitHub for hosting the repo. Email and calendar access
are optional enhancements, not requirements.

**Is my data private?**
Your knowledge base is a private GitHub repo on your own account. Claude Code
runs locally. Do not store passwords, API keys, or financial data in cards.

**Can I use this with Claude.ai (browser) instead of Claude Code?**
The primary experience is Claude Code. A system prompt variant for Claude.ai
Projects is in `SYSTEM_PROMPT.md` for reference, but the browser interface
cannot write to your local repo directly.

**What if I'm interviewing for engineering or design roles, not PM?**
The profile-aware analysis section in `framework/templates/pipeline-card.md` includes
Engineer and Designer lens templates. The prep-planner workflow adapts
to your professional lens automatically — set it in `data/profile/me.md`.

---

## Contributing

Most useful contributions:
- Workflow templates for new scenarios (take-home assessments, offer comparison,
  salary negotiation, executive screen prep)
- Industry-specific research patterns (fintech, healthtech, security, AI)
- Role-specific prep templates for Engineers or Designers

Fork → add to `framework/workflows/` → pull request.
Format: `Purpose / When to Run / Executed by / Inputs / Steps / Notes`

See `USER_GUIDE.md` for a complete walkthrough of how the system works.
