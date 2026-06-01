# Chrysalis Onboarding Sweep Workflow

## Purpose
Get a brand-new user fully operational in one session. Extract the current
state of their job search, structure it into Chrysalis pipeline cards, and
write everything to the repo in one go.

This is a one-time workflow. Run it once after profile setup. After this,
daily "Brief" sessions handle ongoing updates.

## When to Run
- Right after data/profile/me.md has been filled in
- When the user says "I'm ready to start", "set me up", "run the onboarding
  sweep", or any variant suggesting they want to get their pipeline structured

## Executed by
Claude Code (direct read/write access to local repo)

---

## Steps

### Step 1 — Check the profile

Read `data/profile/me.md`. Confirm it has been filled in — not still a blank template.

If the profile is still blank: tell the user to run the profile setup workflow
first (`"Set up my profile — I have a resume"`), then come back here.

If the profile has content: extract the following to use throughout this workflow:
- Target role titles
- Target companies (if any already mentioned)
- Pipeline companies already listed in the profile notes
- Geographic constraints
- Professional lens (PM / Engineer / Designer)

### Step 2 — Check data/manifest.yaml for existing cards

Read `data/manifest.yaml`. Note any company cards that already exist.
Do not create duplicate cards for companies already tracked.

### Step 3 — Gather the pipeline picture

The goal is to understand every company currently in play. Use three sources:

**Source A — the profile**
The user may have listed active companies directly in `data/profile/me.md`.
Extract: company name, current status, any contacts or dates mentioned.

**Source B — user input**
Ask the user:

> "To build out your pipeline, tell me about the companies you're currently
> in process with. For each one: company name, where you are in the process
> (applied / recruiter call / interviews / final round), and any upcoming
> dates I should know about.
>
> You can also paste any recent recruiter emails or calendar invites and
> I'll extract the details."

Wait for the user's response. This is the primary data source.

**Source C — web search for companies mentioned**
For each company identified, do a quick search to confirm:
- What the company does (if not already in a card)
- Any recent news that's relevant (funding, layoffs, product launches)
This is a light scan — full research happens later via "Research [company]".

### Step 4 — Map each company to a pipeline stage

For each company identified, determine the Chrysalis stage:

| User's description | Chrysalis stage |
|---|---|
| "Found it / thinking about it" | `identified` |
| "Looking into it / researching" | `researching` |
| "Applied" | `applied` |
| "Had a recruiter call / scheduled one" | `screening` |
| "In interviews / HM call done" | `interviewing` |
| "Final round / last interview" | `final_round` |
| "Got an offer / deciding" | `decision` |
| "Rejected / withdrew" | `closed_lost` |
| "On hold / paused" | `closed_paused` |

Also set priority:
- `high` — active process (screening through decision) or strong interest
- `medium` — early stage or passive interest
- `archive` — closed

### Step 5 — Present the pipeline picture for confirmation

Before writing anything, present a clean summary:

> "Here's what I've got. Does this look right?
>
> | Company | Stage | Priority | Next Action |
> |---|---|---|---|
> | [Company] | [stage] | [priority] | [action] |
> ...
>
> Let me know if anything is wrong, missing, or if the stage or priority
> needs adjusting."

Wait for the user to confirm or correct. Adjust before proceeding.

### Step 6 — Write all card stubs

For each confirmed company, create `data/pipeline/[company-name].md`.

Use this stub structure (fill in what is known, leave research sections blank):

```markdown
---
card_id: data/pipeline/[company-name]
card_type: company_pipeline
stage: [stage]
priority: [priority]
tags: []
last_updated: "[today YYYY-MM-DD]"
last_analysis_updated: null
last_user_research_updated: null
next_action: "[next action]"
linked_cards: [data/profile/me]
has_temp: false
---

# [Company Name]

## Business Overview
_Not yet researched. Say "Research [Company]" to populate this section._

## User Base & Geography
_Not yet researched._

## Recent News & Performance
_Not yet researched._

## Funding & Growth
_Not yet researched._

## Culture & People Signals
_Not yet researched._

## Open Roles
_Not yet researched._

## Profile-Aware Analysis
_Not yet generated. Will be created when company research is run._

## Pipeline & Interview Notes

### Stage History
| Date | Stage | Notes |
|---|---|---|
| [today] | [stage] | Added via onboarding sweep |

### Contacts
| Name | Role | How Connected | Notes |
|---|---|---|---|
[extract from user input if any contacts were mentioned]

### Interview Notes
[any interview dates, formats, or interviewers mentioned by user]

## Next Actions
1. Run company research to populate this card
```

Write each file directly to `data/pipeline/[company-name].md`.

### Step 6b — Auto-research for companies in active stages

Immediately after writing all stubs, run the full company-research workflow
(`framework/workflows/company-research.md`) for every company at stage `screening`,
`interviewing`, `final_round`, or `decision`.

**Do not wait for the user to ask. Run it automatically, in priority order
(soonest interview or call first).**

For companies at `identified`, `researching`, or `applied`: skip auto-research
here. Flag them in the Step 9 orientation so the user knows they still need it.

This is non-negotiable: a card with `last_user_research_updated: null` and
an active interview process is a liability. The user cannot prep without it.

When auto-research is complete:
- Set `last_user_research_updated` to today's date in each card's front-matter
- Set `last_analysis_updated` to today's date
- Update `next_action` to reflect what comes after research (e.g. run prep planner)

### Step 7 — Update data/manifest.yaml

Add an entry for each new company card. Insert under the existing `cards:` list,
after `data/profile/me` and before any existing pipeline cards:

```yaml
  - id: data/pipeline/[company-name]
    type: company_pipeline
    stage: [stage]
    summary: "[One-sentence summary: what they do + where the process stands]"
    priority: [priority]
    tags: []
    updated: "[today]"
    next_action: "[next action]"
    has_temp: false
```

Also update `data/profile/me` entry: set `updated` to today's date.

### Step 8 — Commit and push

Stage all new and modified files:

```bash
git pull
git add data/pipeline/*.md data/manifest.yaml
git commit -m "init: onboarding sweep [YYYY-MM-DD]"
git push
```

Confirm the push succeeded.

### Step 9 — Orient the user

Once everything is committed, give a clear orientation:

> "You're set up. Here's where things stand:
>
> **Active pipeline ([N] companies):**
> [List each company with stage and next action]
>
> **Research status:**
> ✅ Fully researched: [companies where last_user_research_updated is set]
> ⚠️ Needs research: [companies still at null — these are stubs, not reliable for prep]
>
> **This week:**
> [Any interviews or calls the user mentioned with dates]
>
> **Suggested next steps:**
> 1. [Most urgent — e.g. "Prep for Acme Payments HM interview Apr 22: say 'Prep for Acme Payments'"]
> 2. [Second — e.g. "Research Globex Wallet: say 'Research Globex Wallet'"]
> 3. [Third]
>
> From here, say 'Brief' each morning. I'll check your pipeline, search
> for relevant news, and tell you what needs attention."

---

## Notes
- Card stubs are thin by design — they capture structure fast. But any
  company at `screening` or above gets immediate full research (Step 6b).
  Never leave an active-stage company as a stub.
- A card with `last_user_research_updated: null` at screening or above is
  a blocked prep path. Flag it on every brief until it is resolved.
- If the user already has some cards in data/manifest.yaml: check whether those
  cards have been researched. If `last_user_research_updated: null` and
  stage is screening+, run research immediately — don't skip it just
  because the card exists.
- If the user mentions more than 10 active companies: flag it. That's
  usually a sign the pipeline needs pruning, not more cards.
- The profile may already contain a pipeline snapshot (if the user wrote it
  in during setup). Use that as Source A — it saves time.
