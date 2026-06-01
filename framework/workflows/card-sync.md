# Chrysalis Card Sync Workflow

## Purpose
Merge temp cards into their corresponding main cards.
This is the only workflow that modifies main pipeline cards.

## When to Run
- At the end of any meaningful Claude Project session where new
  company information was gathered
- Once daily as part of the morning sweep (after Step 7)

## Executed by
Claude Code

## Inputs
- data/pipeline/_temp/ (all temp cards pending merge)
- data/pipeline/[company-name].md (the main card to merge into)
- data/manifest.yaml (to update has_temp and updated fields)
- data/profile/me.md (for profile-aware analysis regeneration, if triggered)

---

## Steps

### Step 1 — Find all temp cards
List all files in data/pipeline/_temp/ except .gitkeep.

If none exist, the workflow is complete — exit.

### Step 2 — For each temp card:

**2a. Locate the main card**

The card_id in the temp card front-matter identifies the main card.

e.g. card_id: data/pipeline/aether-labs → main card is data/pipeline/aether-labs.md

If the main card does not exist: create it from framework/templates/pipeline-card.md first,
then proceed with the merge.

**2b. Merge sections**

For each section present in the temp card:
- If the section exists in the main card: prepend new entries (newest first)
- If the section does not exist in the main card: append the entire section

Rules:
- Never delete existing content in the main card
- Timestamp all new entries as YYYY-MM-DD
- Preserve all existing entries unchanged
- If the same event appears in both temp and main (same date + same signal): skip the duplicate

**2c. Check profile-aware analysis update triggers**

Evaluate whether the new information warrants a refresh of the
Profile-Aware Analysis section. See Section 10 of the technical design doc.

Triggers that require regeneration:
- New funding round or extension announced
- New product launch or major feature release
- Acquisition, merger, or major restructuring
- C-suite or VP-level leadership change
- Significant layoff announcement
- IPO filing or public market activity

Triggers that do NOT require regeneration:
- Routine news coverage or minor blog posts
- Small feature updates
- Job postings with no strategic signal

If triggered: regenerate the Profile-Aware Analysis section using current
card content and data/profile/me.md. Use the user's lens (PM / Engineer / Designer)
to determine which template to apply.

Update last_analysis_updated in the front-matter.

**2d. Update front-matter**

- Set last_updated to today's date
- Update next_action if the sync introduced a clearer next step
  (e.g. a new open role, a new event that suggests outreach)

**2e. Update data/manifest.yaml**

- Update the updated field for this card to today's date
- Set has_temp: false
- Update the summary if it has changed meaningfully (e.g. stage changed,
  or a major signal like a funding round is now the lead context)
- Update next_action in data/manifest.yaml to match the card's updated next_action

**2f. Delete the temp card**

Remove data/pipeline/_temp/[company-name].md

### Step 3 — Commit and push

Stage all modified files:
- data/pipeline/[all synced company cards]
- data/manifest.yaml
- (temp files are deleted, so they will be staged as removals)

Commit with message: "sync: merged temp cards [YYYY-MM-DD]"

Push to GitHub.

```
cd ~/chrysalis-kb    # Update this path to match your local clone location
git pull
# ... files have been merged above ...
git add .
git commit -m "sync: merged temp cards [YYYY-MM-DD]"
git push origin main
```

---

## Notes
- If a conflict is detected during git pull: stop and alert the user. Do not force-push.
- The main card is always the trusted version. If in doubt, preserve the main card content.
- Sync should run after every sweep that produced temp cards. Do not let temp cards accumulate.
