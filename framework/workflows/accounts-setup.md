# Chrysalis Accounts Setup Workflow

## Purpose
Configure the user's email and calendar accounts in `data/config/accounts.yaml`.
This is the single source of truth for every workflow that reads email or
calendar — sweeps, briefs, prep block creation. No workflow should hardcode
account names; every reference flows through this file.

This workflow is **idempotent** — runs cleanly for first-time setup AND for
updates (changing accounts, adding new ones, repointing the write calendar).

## When to Run
- During first-time onboarding (chained from "Onboard me")
- When the user says "Update my accounts", "Change my calendar", "Add an
  email account", "Set up my accounts"
- When `data/config/accounts.yaml` is missing or contains only placeholder values
- When the user changes which calendar they want prep blocks written to
- When they connect a new email MCP (e.g. Gmail) and want it picked up

## Executed by
Claude Code

## Inputs
- A short list of email accounts the user monitors for job search emails
- The user's choice of which Apple Calendar receives prep/debrief blocks
- Available MCP servers in the current Claude Code session

---

## Steps

### Step 1 — Read current state (if any)

Check if `data/config/accounts.yaml` exists.

- **If absent or contains only template/placeholder values:** First-time setup.
  Proceed to Step 2.
- **If present and populated:** Update mode. Read it, display the current
  configuration to the user as a summary table, and ask what they want to change:

  > "Here's your current setup:
  >
  > **Email accounts:**
  > - [provider, address, mcp status] (primary)
  > - [provider, address, mcp status]
  >
  > **Calendar:**
  > - Reading from: [list of read_names]
  > - Writing prep blocks to: [write_target] via [write_mechanism]
  >
  > What would you like to change?"

  Based on their answer, focus only on the affected sections. Skip steps
  for unchanged sections. Always rewrite the full file at the end (Step 5).

### Step 2 — Enumerate Apple Calendar calendars

Run this JXA via a temp file (never inline — JXA escaping breaks on special
characters):

Write to `/tmp/chrysalis_list_cals.js`:
```javascript
var app = Application("Calendar");
JSON.stringify(app.calendars().map(function(c){
  return { name: c.name(), description: c.description() };
}));
```

Run: `osascript /tmp/chrysalis_list_cals.js`
Clean up: `rm /tmp/chrysalis_list_cals.js`

Parse the JSON and present to the user as a numbered list with name +
description:

> "Here are the calendars I can see in your Apple Calendar:
>
> 1. **[name]** — [description if any]
> 2. **[name]** — [description if any]
> ..."

If the list is empty: tell the user Apple Calendar appears empty or
inaccessible, ask them to confirm Calendar.app is set up on this Mac,
and either retry or skip calendar configuration.

### Step 3 — Email accounts

Ask:

> "What email accounts do you actively check for job search emails?
> For each, tell me:
> - The provider (Outlook / Gmail / Apple Mail / Yahoo / other)
> - The email address
> - Whether it's your primary job search inbox or secondary"

Wait for the answer. For each account they name, determine the `mcp` value:

| Provider | `mcp` value | Reasoning |
|---|---|---|
| Outlook / Exchange / Outlook.com | `apple-mail` if set up in Mail.app, else `none` | Readable via Apple Mail MCP — confirm Mail.app has it |
| Apple iCloud | `apple-mail` if set up in Mail.app, else `none` | Same |
| Gmail | `gmail` if the Gmail MCP is connected in this session, else `none` | Check available tools — if `search_threads` and similar are present, MCP is live |
| Yahoo / other | `apple-mail` if set up in Mail.app, else `none` | Only readable if user added it to Mail.app |

**To check MCP availability:** look at the tools available in this session.
If Apple Mail MCP tools (`search_emails`, `get_email`, `list_mailboxes`) are
present → Apple Mail is connected. If Gmail MCP tools (`search_threads`,
`get_thread`) are present → Gmail is connected.

**For each Outlook/Apple/Yahoo account:** ask the user to confirm it's set up
in their Mac's Mail.app. If yes → `mcp: apple-mail`. If no → `mcp: none`,
and explain they can either add it to Mail.app or paste signals manually
during sweeps.

**For each Gmail account where the MCP is not connected:** explain they can
either install the Gmail MCP later (and re-run this workflow) or paste
signals manually. Set `mcp: none`.

### Step 4 — Calendar configuration

**4a. Which calendars to read from:**

Ask:

> "Which calendars from the list above should I read for interviews and
> commitments? Pick all that apply — work calendars, personal, family.
> I'll deduplicate overlaps."

Default suggestion if they're unsure: any calendar whose name suggests work,
plus their primary personal calendar. Build the `calendar.read_names` list
from their picks.

**4b. Which calendar receives prep blocks:**

Ask:

> "Of the calendars you just picked, which one should I write prep blocks
> and interview debrief blocks into? You'll see them appear automatically
> 24 hours before each interview."

This becomes `calendar.write_target`. The mechanism is `jxa` by default
(works for any Apple Calendar). If the user mentions they prefer Google
Calendar API and the Google Calendar MCP is connected, set
`write_mechanism: google_calendar_mcp` and ask for the calendar ID.

**4c. Google Calendar MCP (optional):**

If a Google Calendar MCP is connected in this session, ask:

> "I see Google Calendar is connected. Want me to use the Google Calendar
> API directly for richer event creation? (Otherwise I'll write events
> via Apple Calendar's JXA scripting, which works fine but is more limited.)"

If yes: ask for the calendar ID(s) and populate the `calendar.google_calendar`
block. If no: skip this section entirely (do not write the block).

### Step 5 — Write `data/config/accounts.yaml`

Build the file from the user's answers. Use this template:

```yaml
# Chrysalis — Account Configuration
# Generated by accounts-setup workflow. Update anytime by saying "Update my accounts".
# This file is the single source of truth for all email and calendar access.
# No workflow or sweep should hardcode account names — always read from here.
# ─────────────────────────────────────────────────────────────────────────────

email:
  accounts:
    - provider: [outlook | gmail | apple | yahoo | other]
      address: [email address]
      mcp: [apple-mail | gmail | none]
      primary: [true | false]
      notes: "[short note, e.g. 'Primary job search inbox.' or 'Secondary — not connected.']"
    # ... one block per account

# ─────────────────────────────────────────────────────────────────────────────
calendar:
  # Apple Calendar aggregates iCloud, Exchange, and Google sources.
  # List every calendar name to READ from via JXA. Deduplication handles overlaps.
  read_names:
    - "[name1]"
    - "[name2]"
    # ...

  # Optional: Google Calendar MCP block (only if user opted in)
  # google_calendar:
  #   mcp: google_calendar
  #   personal_calendar_id: "[id]"

  # Write target for prep blocks.
  write_target: "[chosen calendar name]"
  write_mechanism: jxa          # jxa | google_calendar_mcp

  # Deduplication strategy when reading from multiple source calendars.
  dedup_by: title_date          # Match on (normalized_title, start_date) — ignore source
```

Overwrite `data/config/accounts.yaml` with the populated version. If the file
existed previously, the overwrite is intentional — the rewrite is the update.

### Step 6 — Confirm

Tell the user exactly what was configured:

> "Accounts configured. Here's the summary:
>
> **Email:**
> - [address] ([provider]) — [connected via X / paste manually]
> - [address] ([provider]) — [connected via X / paste manually]
>
> **Calendar:**
> - Reading from: [list]
> - Prep blocks land in: [write_target]
>
> Run 'Update my accounts' anytime to change this."

### Step 7 — Commit

Stage and commit:

```bash
git pull
git add data/config/accounts.yaml
git commit -m "config: accounts configuration updated [YYYY-MM-DD]"
git push
```

For first-time setup, prefer the message: `init: data/config/accounts initial setup`.

---

## Notes

- Never write personal data inline as examples in this workflow — examples
  must use placeholder addresses like `you@example.com`. The framework
  ships publicly; this workflow is reference for any user.
- If the user has zero connectable accounts (no MCPs available, no Mail.app
  setup): proceed anyway with `mcp: none` for everything. Chrysalis still
  works — the user just pastes signals manually during sweeps and briefs.
  Note the gap in Step 6.
- Apple Calendar's `description()` field is often empty. Don't fail if it's
  missing — present the name alone.
- The Apple Mail MCP reads all configured accounts in Mail.app without
  filtering. Passing an `account` parameter to `search_emails` returns
  empty results — always omit it. This is a known quirk of the MCP.
- The `mcp` value is descriptive, not a directive — workflows read it to
  decide *how* to fetch from each account (which tools to call). Setting
  it to `none` doesn't disable the account; it just signals "paste required".
- If running in update mode (Step 1 found an existing file) and the user
  only wants to change one section, still rewrite the whole file in Step 5
  — partial updates risk leaving stale fields behind.
