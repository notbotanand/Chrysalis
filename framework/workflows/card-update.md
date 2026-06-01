# Chrysalis Card Update Workflow

## Purpose
Apply new information gathered during a Claude Project session to the
relevant knowledge card(s). This is the standard handoff from a Claude Project
conversation to the local knowledge base.

## When to Run
- At the end of any Claude Project session where meaningful new information
  was discussed, discovered, or decided about a company, learning track, or
  the user's profile
- When the user says "save this" or "update the card" during a session
- When Claude Project identifies that a card is stale or missing new signals

## Executed by
Claude Code (supervised write) or user manually.
Claude Project initiates but cannot write directly — it presents the update,
and the user applies it via Claude Code or by editing the file manually.

## Inputs
- The card to update (identified during the session)
- New information from the session (specific sections to update)
- data/profile/me.md (if profile-aware analysis needs to be regenerated)
- data/manifest.yaml (to update updated field, next_action, and any other manifest fields)

---

## Steps

### Step 1 — Identify what changed

At the end of a Claude Project session, review what was discussed:

- Was new information learned about a company? (news, funding, culture, roles, contacts)
- Did the pipeline stage change? (e.g. applied, got a screening call, rejected)
- Was a next_action completed or updated?
- Were interview notes taken that should be logged?
- Were learning session notes worth capturing?
- Was a new contact added?

List each piece of new information and the card and section it belongs in.

### Step 2 — Check for existing temp card

Check data/pipeline/_temp/ for an existing temp card for this company.

- If one exists: add new information to the temp card (append, do not overwrite)
- If none exists: create a new temp card using the temp card format from Section 4.5

Temp card front-matter fields:
- card_id: must match the main card exactly
- is_temp: true
- source: claude_session
- created: current timestamp (ISO 8601)
- sections_updated: list of sections with new content

Include only sections that have new content. Omit all others.

### Step 3 — Prepare the update content

For each section with new information, format the content correctly:

**Recent News & Performance (prepend, newest first):**
```
- **YYYY-MM-DD:** [Summary of the new signal — one sentence]
```

**Pipeline Stage History (append):**
```
| YYYY-MM-DD | [new stage] | [brief note on what changed] |
```

**Contacts (add new row):**
```
| [Name] | [Role] | [How Connected] | [Notes] |
```

**Interview Notes (add dated entry):**
```
### [Round Name] — YYYY-MM-DD
- Format: [behavioral / technical / panel]
- Interviewer(s): [Name, role]
- Themes covered: [list]
- What went well: [notes]
- What to improve: [notes]
```

**Next Actions (update top item):**
Replace the top item with the new most-important next step.
Keep previous items below it (unless they are completed — then remove them).

**Open Roles (add new row):**
```
| [Role title] | [URL] | [YYYY-MM-DD] |
```

### Step 4 — Evaluate profile-aware analysis trigger

Check whether the new information warrants a regeneration of the
Profile-Aware Analysis section. See Section 10 of the technical design doc.

Significant triggers:
- New funding round
- Major product announcement or launch
- Leadership change at C-suite or VP level
- The user's assessment of the role has meaningfully shifted based on new info

If triggered: regenerate the Profile-Aware Analysis section using current
card content and data/profile/me.md. Update last_analysis_updated in the front-matter.

### Step 5 — Update the card

**If using Claude Code:**
Open a Claude Code session in the local repo directory.
Apply the changes to the appropriate card file.
Update data/manifest.yaml:
- Set updated to today's date
- Update next_action if it changed
- Update summary if the company's status has changed meaningfully
- Set has_temp: false if you wrote directly to the main card
  (or true if you wrote a temp card for sync later)

Commit with message: "update: [card-id] [brief reason]"
e.g. "update: data/pipeline/aether-labs screening call completed"

Push to GitHub.

**If applying manually:**
Claude Project presents the exact formatted content to paste.
The user opens the file, pastes in the right section, saves, and commits.

### Step 6 — Confirm

After the update is committed, verify:
- The card reflects the new information
- The data/manifest.yaml updated field is current
- The next_action in both the card and data/manifest.yaml is accurate
- Any completed next actions are removed from the list

---

## Notes
- If the session produced information for multiple companies: create one temp card
  per company. Do not combine multiple companies into a single card.
- If in doubt about which section to update: add a new dated entry to
  "Recent News & Performance" — it is the catch-all section.
- Do not paraphrase or compress interview notes. Log them close to verbatim —
  the detail matters for future prep sessions.
- Profile changes (new skills, updated target role, change in geographic preference)
  should be applied directly to data/profile/me.md, not a temp card.
