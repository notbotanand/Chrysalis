# Chrysalis Job Board Scan Workflow

## Purpose
Run a targeted search across job boards to surface new role postings that
match the user's target criteria. Write results to the market digest for
review in the morning brief.

## When to Run
- Daily as part of the morning sweep (Step 5)
- Can also be triggered manually when the user wants a fresh scan mid-week
- After updating data/profile/me.md with new target role criteria

## Executed by
Claude Code

## Inputs
- data/profile/me.md (for target role titles, industries, location, stage preferences)
- data/manifest.yaml (to check if spotted companies already have pipeline cards)
- data/market/digest.md (to write results)

---

## Steps

### Step 1 — Read the user's search criteria

Read data/profile/me.md. Extract:

- **Target role titles** (e.g. Senior PM, Director of Product, Head of Product)
- **Target industries** (e.g. AI/ML, enterprise SaaS, fintech, healthtech)
- **Company stage preferences** (e.g. Series A–C, growth stage, enterprise)
- **Geographic constraints** (city, region, remote/hybrid/in-office stance)
- **Non-negotiables** (industries or role types to exclude)

Use this criteria to construct targeted search queries for each platform.

### Step 2 — Search LinkedIn Jobs

Run 2–3 searches on LinkedIn Jobs using combinations of:
- Target role title + location or "Remote"
- Target role title + target industry keyword
- Seniority filter (Senior, Staff, Director, Principal) where applicable

For each relevant result, capture:
- **Role title**
- **Company name**
- **Location / remote status**
- **Date posted** (skip roles posted more than 14 days ago unless a strong match)
- **Fit signal** (one sentence on why this could be relevant)
- **Link to posting**

### Step 3 — Search Indeed

Run 1–2 searches on Indeed using the same criteria.
Prioritize roles not already found on LinkedIn.

Apply the same capture format: title, company, location, date, fit signal, link.

### Step 4 — Search role-specific boards (if applicable)

Based on the user's target role and industry, check relevant niche boards:

- **Product roles:** Product Hunt Jobs, Lenny's Newsletter job board
- **AI/ML companies:** ai-jobs.net, ML-focused company career pages
- **Startups:** Wellfound (formerly AngelList), YC jobs board
- **Other:** Any board specifically mentioned in data/profile/me.md

Run 1 search per relevant board. Capture the same fields.

### Step 5 — Cross-reference with existing pipeline

For each role found, check data/manifest.yaml:

- Does this company already have a card in the pipeline?
  - If yes: note the connection. Flag if it's a new role at an existing tracked company.
  - If no: treat as a new lead.

If a new role appears at a company with an existing card:
- Note it in the digest entry
- Create a temp card entry for the Open Roles section of that company's card

### Step 6 — Filter and score

Before writing to the digest, filter the results:

- Remove roles that clearly don't match the non-negotiables from data/profile/me.md
- Flag the 1–3 strongest matches with a note on why they stand out
- Keep the list to a maximum of 10 roles per scan. Prioritize recency and fit signal.

### Step 7 — Write results to data/market/digest.md

Prepend a new dated entry under "New Roles Spotted" in data/market/digest.md:

```markdown
### YYYY-MM-DD
| Role | Company | Fit Signal | Link |
|---|---|---|---|
| [Title] | [Company] | [One-sentence fit signal] | [URL] |
```

If any result is a new role at an existing pipeline company, add a note
below the table:

```markdown
**Note:** [Company] (already in pipeline, stage: [stage]) posted a new
[role title] — review and decide if this changes your next action.
```

---

## Notes
- Do not add every job posting found. The digest is a curated signal, not a raw dump.
  The user should be able to scan the "New Roles Spotted" table in under 2 minutes.
- If a role is very strong and the company has no card yet, consider creating a
  temp stub card immediately and flagging it for research.
- Job board results change quickly. If a posting was spotted more than 14 days ago
  and is not already in the pipeline, it may already be filled — deprioritize it.
- Update last_job_scan in data/state/sweep_state.yaml under `sweep_state:` after the scan completes.
