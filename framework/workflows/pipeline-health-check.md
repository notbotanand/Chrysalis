# Chrysalis Pipeline Health Check Workflow

## Purpose
Review all active pipeline cards to identify companies that have gone stale —
no recent updates, no logged next action, or no follow-up despite a clear
signal. Surface these as attention items so nothing falls through the cracks.

## When to Run
- Daily as part of the morning sweep (Step 6)
- Can also be triggered manually when the user asks "what's stale?" or
  "where do things stand across my pipeline?"
- Before weekly reviews to prepare the pipeline summary

## Executed by
Claude Code

## Inputs
- data/manifest.yaml (full card manifest with stages, priorities, updated dates, next_actions)
- data/pipeline/[company-name].md for any card that needs closer inspection
- data/market/digest.md (to write flagged items)

---

## Steps

### Step 1 — Read the full card manifest

Read data/manifest.yaml. Extract all cards where:
- type: company_pipeline
- stage is NOT in: [closed_won, closed_lost, closed_paused]
- priority is: high OR medium

These are the active pipeline cards subject to health checking.

### Step 2 — Apply staleness rules

For each active pipeline card, check the following conditions:

**Flag as stale if:**
- `updated` date is more than 7 days ago AND no `next_action` is logged
- `updated` date is more than 14 days ago regardless of next_action status
- Stage is `applied` or `screening` and updated date is more than 5 days ago
  (application windows move fast — these need more frequent attention)
- Stage is `interviewing` or `final_round` and updated date is more than 3 days ago
  (active interview processes require immediate attention if something changes)

**Do not flag if:**
- The card was deliberately paused (`closed_paused`) — already excluded above
- The stage is `researching` and updated date is within 14 days
  (research phase has a longer natural cadence)
- A has_temp: true card exists — it has pending updates that will arrive via sync

### Step 3 — Inspect flagged cards

For each flagged card, load the full card file and check:

- What was the last logged activity?
- Is there a meaningful next_action listed?
- Is the next_action specific and actionable, or vague?
- Is there a contact listed who could be followed up with?

Categorize each flagged card into one of:
- **Needs follow-up:** There's a clear contact or action — the user just hasn't done it
- **Needs decision:** Unclear if this company is still worth pursuing
- **Needs research:** Card is incomplete — next step is to research further
- **Stale, low signal:** No clear path forward; candidate for closing or archiving

### Step 4 — Write flagged items to data/market/digest.md

Prepend a new dated entry under "Pipeline Attention Items" in data/market/digest.md.

For each flagged company, write one line:

```markdown
### YYYY-MM-DD
- **[Company]** — last updated YYYY-MM-DD, stage: [stage],
  status: [Needs follow-up / Needs decision / Needs research / Stale, low signal],
  suggested action: [specific suggestion]
```

Suggested action should be specific:
- "Follow up with Jamie Chen — last outreach was 10 days ago"
- "Decide whether to apply — role closes soon and no action taken"
- "Research CPO departure from May 15 news — affects fit assessment"
- "Consider closing — no signal in 21 days and no response to outreach"

### Step 5 — Identify any cards to close

If any card is clearly dead (no response after multiple outreach attempts,
role filled, company in layoffs), flag it explicitly:

```markdown
- **[Company]** — candidate for closing. [Brief reason]. Suggest moving to
  stage: closed_lost or closed_paused.
```

Do not automatically change the stage. Present the suggestion for the user to confirm.

---

## Notes
- The goal is attention, not anxiety. Flag what needs action, not everything that
  is imperfect. The user should be able to scan this list and know exactly what
  to do next for each item.
- If the pipeline is healthy (all cards updated recently, all have next actions),
  write: "Pipeline health: all active cards up to date. No attention items."
  This is a positive signal worth surfacing.
- Staleness thresholds above are defaults. If the user has specified different
  cadences in data/profile/me.md or directly, use those instead.
- After a weekly review, the user should update next_action for any flagged card.
  The next health check will confirm whether the attention items were addressed.
