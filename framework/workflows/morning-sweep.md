# Chrysalis Morning Sweep Workflow

## Purpose
Run the automated daily sweep to gather new signals since the last sweep
and pre-populate the market digest before the user's working day begins.

**Note:** This workflow is for CoWork (automated, scheduled). If you are
not using CoWork, you do not need this workflow. Claude Project handles
email, calendar, and web search live during each "Brief" session using
native connectors — no pre-sweep required.

## When to Run
Daily, on a schedule. Ideally before the user's working day begins (e.g. 7am).
Can also be triggered manually from CoWork at any time.

## Executed by
Claude CoWork (desktop agent) — optional advanced setup

## Inputs
- data/state/sweep_state.yaml (for sweep state timestamps)
- data/manifest.yaml (for the card list)
- data/profile/me.md (for target roles, industry, location)
- Email access (Gmail connector or Outlook.com in browser)
- Calendar access (Google Calendar connector or desktop Calendar app)

---

## Steps

### Step 1 — Read sweep state
Read data/state/sweep_state.yaml. Note the following timestamps from sweep_state:
- last_sweep
- last_gmail_sync
- last_calendar_sync
- last_outlook_sync (if configured)
- last_job_scan

These define the "since" window for all subsequent steps.

If any timestamp is null (first ever run): default the "since" window to 7 days ago.
This gives a reasonable backfill on first run without overwhelming output.

### Step 2 — Email scan
**If Gmail connector is active:**
Read emails received since last_gmail_sync.

**If Outlook personal (no connector):**
Open Outlook.com in browser. Filter to emails since last_outlook_sync.

For all email sources, identify and summarize:
- Recruiter outreach (new, not seen before)
- Referral introductions
- Replies from companies in the pipeline
- Interview scheduling or confirmation emails
- Any other signals relevant to the job search

Do not reproduce email content verbatim. Summarize each signal in one sentence.

Write findings to data/market/digest.md under "Recruiter & Inbound Signals > [today's date]".

### Step 3 — Calendar scan
**If Google Calendar connector is active:**
Read events created or updated since last_calendar_sync.

**If using desktop Calendar app:**
Open the Calendar application. Review events for the next 7 days.

Identify:
- New interview invites or confirmations
- Networking calls or coffee chats
- Any deadline-related events

Write findings to data/market/digest.md under a new dated entry in the relevant section.

### Step 4 — Market intelligence
Run 2–3 web searches on topics derived from data/profile/me.md:
- The user's target industry (e.g. "enterprise AI product news [current month]")
- The user's target role type (e.g. "PM hiring trends 2026")
- Any companies in the pipeline with priority: high that have not been updated
  in 5+ days — check for recent news specifically for those companies

Write findings to data/market/digest.md under "Technology & Industry Pulse > [today's date]".

### Step 5 — Job board scan
Run targeted searches for new job postings matching:
- Target role titles from data/profile/me.md
- Target industries and company stage preferences
- Geographic constraints from data/profile/me.md

Search LinkedIn, Indeed, and any role-specific boards.

For each match: capture title, company, location, fit signal, link.

Write to data/market/digest.md under "New Roles Spotted > [today's date]".

If any matching company already exists in data/manifest.yaml, note the connection.

### Step 6 — Pipeline health check
Read all cards in data/manifest.yaml with priority: high or medium and
stage not in [closed_won, closed_lost, closed_paused].

Flag any card where:
- updated date is more than 7 days ago AND
- no next_action is logged

Write flagged companies to data/market/digest.md under "Pipeline Attention Items > [today's date]".

### Step 7 — Write temp cards for companies with new signals
If new information was found in Steps 2–4 for a specific company that has
a card in data/manifest.yaml, create a temp card at data/pipeline/_temp/[company-name].md
with only the new sections populated.

Set has_temp: true in data/manifest.yaml for that company.

See the temp card format in the framework/templates/pipeline-card.md for structure.
Temp cards include only sections with new content — omit sections with no updates.

### Step 8 — Update sweep state in data/state/sweep_state.yaml
Update the following fields under `sweep_state:` to the current timestamp (ISO 8601, local time):
- last_sweep
- last_gmail_sync (if Gmail was read)
- last_calendar_sync (if calendar was read)
- last_outlook_sync (if Outlook was read)
- last_job_scan

Increment sweep_count by 1.

**Partial sweep handling:** If a step fails (e.g. Outlook is unreachable),
only update the timestamps for sources that were successfully read.
Do not update last_sweep if the sweep did not complete all steps.

### Step 9 — Commit and push
Stage all modified files:
- data/state/sweep_state.yaml
- data/manifest.yaml (if any card stage/next_action changed)
- data/market/digest.md
- Any new temp cards in data/pipeline/_temp/

Commit with message: "sweep: [YYYY-MM-DD] morning run"

Push to GitHub.

```
cd ~/chrysalis-kb    # Update this path to match your local clone location
git pull
# ... files have been written above ...
git add .
git commit -m "sweep: [YYYY-MM-DD] morning run"
git push origin main
```

---

## Notes
- The repo must be cloned locally for CoWork to write and push.
- CoWork should never run concurrent sweeps. The sweep_count field helps detect this.
- If a conflict occurs on push: git will flag it. The main card is always the trusted version.
