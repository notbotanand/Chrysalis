# Chrysalis User Guide

This is the complete guide to using Chrysalis — not just what commands to type,
but how the system thinks, why it works the way it does, and how to get the
most out of it across a real job search.

---

## The mental model

Chrysalis behaves like a Chief of Staff who has read every email in your inbox,
every recruiter conversation, every company's last 12 months of news — and
who is thinking about your pipeline strategically, not just tactically.

The difference between a Chief of Staff and a calendar app:
- A calendar app tells you "Tuesday at 2PM is free."
- A Chief of Staff says "Tuesday works, but you have a Acme Payments HM on Thursday
  and no prep day between now and then. If you take this call Tuesday, what's
  your prep plan for Thursday?"

That's the bar Chrysalis tries to meet.

**The three core ideas:**

1. **Cards are long-term memory.** Every company, every round, every signal
   gets written to a card. Nothing lives only in your head or in a conversation.
   The next session picks up exactly where the last one left off.

2. **The system compounds.** Each interview round makes the next prep smarter.
   Each debrief adds intel to the company card. By Round 3 at a company,
   Chrysalis knows what that company's interviewers care about, what landed in
   prior rounds, and what topics are likely to recur.

3. **Strategic, not just operational.** Chrysalis doesn't just answer "what
   interview do I have next?" It thinks about: Are you over-scheduled? Is the
   prep load realistic? If this company moves to final rounds in 3 weeks, what
   does that mean for the two other final rounds likely happening at the same time?

---

## Setup (one time)

### Step 1 — Fork and clone

Fork the Chrysalis repo on GitHub to your own account (make it private).
Clone it locally. Run `claude` from inside the repo directory.

```bash
git clone https://github.com/[yourname]/[repo-name] ~/chrysalis-kb
cd ~/chrysalis-kb
claude
```

Claude Code reads `CLAUDE.md` automatically at startup. No configuration needed.

### Step 2 — Set up your profile

Say: `"Set up my profile — I have a resume."`

Attach your resume when prompted. Claude extracts your background automatically
and then asks 4–5 questions your resume won't answer:

- What's your actual target role and level?
- Which companies are Tier 1 for you — and why?
- What are your location and visa constraints?
- What are your non-negotiables?
- Is there anything about your search that context alone won't capture?

Your profile is written to `data/profile/me.md` and committed. It is loaded at the
start of every session, forever. Get it right the first time — it shapes every
piece of analysis Chrysalis generates.

### Step 3 — Onboarding sweep

Say: `"I'm ready to start."` or `"Run the onboarding sweep."`

Claude will ask you to describe where you stand with each company currently in
play. You can also paste recruiter emails directly — Claude will extract
company names, roles, stages, and upcoming dates from them.

At the end of the sweep, Claude creates all card stubs, populates `framework/index.yaml`,
and commits everything. Your pipeline is now in the system.

### Step 4 — Connect email and calendar

Run: `"Update my accounts"`

This is the one-time setup for email and calendar access. Claude will:
1. Enumerate every calendar in your Apple Calendar and present the list
2. Ask which email accounts you monitor for job-search emails (provider + address)
3. Ask which calendar you want prep blocks written to
4. Write everything to `data/config/accounts.yaml`

This file is the single source of truth for all email and calendar access.
No credentials are stored — Chrysalis reads through your existing app connections.

**Email connectors supported:**
- **Apple Mail MCP** — reads Exchange, Outlook, iCloud, and any account configured
  in Mail.app. Install `falconbradley/claude-connector-apple-mail` and configure
  it in `~/.claude.json` under `mcpServers`.
- **Gmail MCP** — reads Gmail directly via Google's API. Install and configure
  the Gmail MCP connector for your account.
- **Not connected** — Chrysalis will ask you to paste signals manually and notes
  the gap in the brief.

**Calendar:** Apple Calendar is read via JXA (JavaScript for Automation) — no
setup needed. Chrysalis reads from every calendar you specify in `data/config/accounts.yaml`,
including iCloud, Exchange, and Google calendars that Apple Calendar aggregates.
Prep and debrief blocks are written to whichever calendar you designate as the
write target.

**Fallback:** If no email is connected, Claude will ask "Anything from email
or calendar I should factor in?" at the start of a Brief. Paste or describe
what's relevant and it incorporates what you share.

To change accounts later: say `"Update my accounts"` at any time.

---

## The daily loop

### Morning Brief

Say: `"Brief"` or `"Morning brief"` or `"What's up"`

This is the start of every day. Claude:
1. Reads `framework/index.yaml` and loads all high-priority pipeline cards
2. Does 2–3 web searches relevant to your target roles and industries
3. Checks for news on any high-priority company not updated in 5+ days
4. Audits every high-priority card for research completeness — flags any card
   at screening or above with missing research as a blocker (not a suggestion)
5. **Runs a proactive email sweep** — checks every connected inbox for recruiter
   signals, interview confirmations, follow-ups, and ATS emails since the last sweep.
   If a signal is from a company not yet in the pipeline, it auto-creates the card
   and runs full research inline.
6. Reads your calendar for the next 14 days — surfaces all upcoming interviews,
   calls, and deadlines
7. Asks if there's anything else from email or calendar to factor in
8. Delivers a structured briefing:
   - **This week** — upcoming interviews, calls, deadlines
   - **New signals from email** — every job-search relevant email found in the sweep
   - **Industry pulse** — 2–3 web search findings relevant to target roles
   - **Pipeline health** — stale cards, suggested next actions
   - **One focus for today** — the single most important thing right now
9. Writes today's signals to `data/market/digest.md` so they accumulate over time
10. Writes the full brief to `data/logs/today/brief.md` and clears `data/logs/today/updates.md`
11. Regenerates `dashboard.html` — the Today tab opens automatically

The Brief is also when the system prompts you toward next actions — "Acme Payments HM
is in 3 days and no prep plan is logged. Want to run the prep planner now?"

### Background Sweep

Say: `"Sweep"` or `"Run sweep"`

A lighter, faster version of the email + calendar check — runs between briefs
to catch anything that arrived since this morning.

What it does:
- Sweeps every connected inbox for new recruiter signals
- Reads the next 30 days of calendar events and detects anything new
- Creates prep and debrief blocks for any newly found interviews (see below)
- Appends real signals to the Updates section of the Today tab
- Regenerates `dashboard.html`

If there's nothing new, the sweep writes nothing. The Updates section stays clean.

### Automatic Sweep (set-and-forget)

Say: `"Enable automatic sweep"` or `"Set up automatic sweep"`

Runs the sweep on a recurring schedule automatically — no manual trigger needed.
This is a one-time setup step. Once enabled, it runs in the background without
you doing anything.

**Prerequisites:** Profile configured (`data/profile/me.md`) and accounts set up
(`"Update my accounts"` completed so `data/config/accounts.yaml` exists with at
least one connected email account).

**Setup flow:**
1. Say `"Enable automatic sweep"`
2. Claude reads your current interval from `framework/index.yaml` (default: 3 hours) and asks if you want to change it
3. You confirm or pick a new interval (1, 2, 3, 4, 6, or 12 hours)
4. Claude creates a scheduled background task — done

**How it runs:**
- Fires automatically every N hours while Claude Code is open
- If the app is closed when a sweep is due, it runs on next launch (no signals are missed)
- Reads all config from `data/config/accounts.yaml` and `framework/index.yaml` at runtime — nothing is hardcoded
- Runs silently — no notifications unless there are real signals

**What each sweep does:**
1. Checks every connected inbox (Apple Mail, Gmail) for recruiter emails, ATS messages, interview confirmations, and follow-ups since the last sweep
2. Reads your calendar for the next 30 days and detects any new events not seen before
3. For any new interview, recruiter screen, or panel: automatically creates a 🟡 PREP block (24 hrs before) and a 📝 DEBRIEF block (immediately after) in your calendar
4. Appends real signals to `data/logs/today/updates.md` — visible in the Today tab's Updates section
5. Updates `sweep_state.last_sweep` in `framework/index.yaml`
6. Regenerates `dashboard.html` — the Today tab reflects the new state within 5 minutes (auto-refresh)

**If nothing is found:** The sweep writes nothing. The Today tab is unchanged. This is correct — silence means no signals, not a failure.

**First-run permission step (important):**
After enabling, find the `chrysalis-sweep` task in the **Scheduled** section of the Claude Code sidebar and click **"Run now"** once. This lets you approve any permission prompts (email access, calendar access, file writes) while you're watching — those approvals are saved and all future automatic runs proceed without interruption.

**Checking sweep status:**
Say: `"Check sweep status"` or `"Is the sweep running?"` — Claude will list the scheduled task, show the last run time, and confirm the next scheduled run.

**Changing the interval:**
Say: `"Change sweep to every 4 hours"` — Claude updates the schedule.

**Disabling:**
Say: `"Disable automatic sweep"` — Claude turns off the scheduled task. Re-enable anytime with `"Enable automatic sweep"`.

---

## The Dashboard

Every brief regenerates `dashboard.html` — a self-contained visual overview of your
entire search. It opens automatically in your browser. No server needed. The page
auto-refreshes every 5 minutes to pick up any sweep updates.

The dashboard has three tabs: **Today**, **Overview**, and **Companies**.

### Today tab (default)

The first thing you see every time you open the dashboard.

**Updates** — a numbered list of signals captured since the morning brief.
Each sweep appends real signals here: new recruiter emails, new calendar events
found, prep blocks created, company research completed. Nothing is written if
there are nothing new — the section simply stays empty until something happens.

**Daily Brief** — the full morning brief, formatted for reading. Sections,
bullets, and all — no scrolling back through Claude chat to find what was said.

Use the Today tab as your home base. The brief tells you the context for the day;
the updates section tells you what changed since.

### Overview tab

**Header** — your name (from `data/profile/me.md`), today's date, week of search,
and count of active processes.

**Upcoming calls** — interviews in the next 3 days, listed with time and round type.

**Week strip** — Monday through Friday showing call density. Blue days have calls,
amber days are heavy (3+). Click any day with calls and an overlay shows every
interview scheduled that day — time, company, Tier 1 status, round type, and
the current next action from the card.

**Pipeline kanban** — your companies grouped by stage: Interviewing, Screening,
Applied. Each card shows the next interview date, next action, tags, and a prep
readiness bar. Tier 1 companies have an amber left border.

**Industry pulse** — the last 10 signals from `data/market/digest.md`, newest first.
Signals with source URLs show "Open source →" and open the article in a new tab
when clicked. Signals accumulate across briefs — the panel gets richer over time.

**Prep readiness** — a progress bar for every company in screening or interviewing.
The bar is amber if prep is partial, red if it's low (under 40%), green when solid.
Click any company to see the detail overlay: what components are done (green ✓),
what's missing (red ✗ with the specific workflow to run), and the current next action.

### Companies tab

A full-detail view of every company in your pipeline.

**Left nav** — alphabetical list of all companies with a colored stage indicator
dot and a ★ for Tier 1. Search box filters the list in real time. The first
company is selected by default.

**Right panel** — selecting a company shows:
- Stage badge, tags, prep readiness bar, and next action
- **Business Overview** — the first paragraph from the card's Business Overview section
- **Open Roles** — table of roles spotted and applied for
- **Interview Process** — each round with ✅ (completed), 🔴 (upcoming), or ⬜ (TBD),
  plus format, duration, interviewer, and focus areas
- **Prep Plan** — the full Interview Notes section from the card, rendered as readable text
- **Contacts** — each contact with avatar initials, role, and how connected
- **Timeline** — stage history in reverse chronological order
- **Improve this research** — a collapsible section at the bottom of every company
  card with a pre-filled Claude prompt you can copy and paste to correct or extend
  the research. One click copies. One paste in Claude Code updates the card.

### Regenerating manually

The dashboard is regenerated automatically at the end of every brief and sweep.
To regenerate at any other time — after updating a card, after debriefing, after research:

```bash
python3 framework/tools/generate_dashboard.py
```

### How prep readiness is scored

| What's present in the card | Score |
|---|---|
| Base (any active company) | 10% |
| Interview process table populated | +20% |
| Prep plan written (opening, positioning, stories) | +40% |
| Questions to ask the interviewer | +15% |
| Company knowledge section populated | +15% |

A score under 40% triggers the ⚠ warning. The prep detail overlay tells you
exactly which components are missing and what to run to fix it.

---

## Automatic calendar blocks

When the morning brief or a sweep detects a new interview on your calendar,
Chrysalis automatically creates two calendar events — no prompt needed.

### 🟡 Prep block (24 hours before)

A time-blocked prep session created in your designated write calendar.

- **Title:** `🟡 PREP: [Company] — [Round Type]`
- **Duration:** 1 hr for recruiter screens, 2 hrs for interviews, 3 hrs for panels
- **Description:** includes a ready-to-paste Claude prompt to kick off the full
  prep-planner workflow, plus a checklist of what to cover

When you sit down to prep, open this event, copy the prompt, paste it into Claude.
The prep-planner picks up exactly where your card and profile left off.

### 📝 Debrief block (immediately after the interview ends)

A 15-minute block created right when the interview ends.

- **Title:** `📝 DEBRIEF: [Company] — [Round Type]`
- **Duration:** 15 minutes (fixed)
- **Description:** includes a ready-to-paste Claude prompt to start the debrief
  workflow, plus a capture checklist (questions asked verbatim, stories told,
  interviewer signals, next steps, what you'd do differently)

**Do not skip this block.** Debrief quality degrades rapidly within hours of an
interview. The block is there because memory fades — use it.

End time is calculated from interview duration defaults (recruiter screen = +30 min,
interview = +60 min, panel = +90 min). If the calendar event has an explicit end
time, that is used instead.

Exception: offer calls do not get a debrief block.

---

## The interview lifecycle

This is the core of how Chrysalis works. Understanding this loop is the key
to getting the most out of the system.

```
New company / opportunity arrives
          ↓
Research [company]
  → Web research + profile-aware analysis → card written
          ↓
Interview scheduled
  → Sweep detects it → 🟡 PREP block + 📝 DEBRIEF block auto-created
  → Prep for [company] interview (full planner)
          ↓
Interview happens
  → Open 📝 DEBRIEF block → paste prompt → Debrief [company]
          ↓
Next round scheduled → repeat from Prep
          ↓
Offer or close → card archived, outcome logged
```

### Phase: Research

Say: `"Research [company]"`

Claude does full web research — business model, funding, recent news,
culture signals, product strategy — and generates a Profile-Aware Analysis
section tailored to your professional lens (PM, engineer, or designer).

The analysis is not generic. For a PM, it covers: product strategy signals,
roadmap direction, PM org structure, product gaps, and a fit assessment
calibrated to your specific profile and target role.

The card is written to the repo and committed. Future research runs update the
card with new signals without overwriting prior intel.

**Source citation is mandatory.** Every factual claim in a company card links
to its source. If a claim can't be sourced, it isn't written — "not publicly
disclosed" or "not found" is used instead. This prevents hallucination.

### Phase: Prep (three phases, do not skip)

Say: `"Prep for [company] interview"` or `"Prep for [company] [round name]"`

**This is not a template. It adapts to each company and each round.**

#### Prep Phase 1 — Know the Process

Claude checks the company card for an Interview Process section.

If it doesn't exist (first prep for this company): Claude runs targeted web
searches — Glassdoor, Blind, community posts — to research what THIS company
actually does for your role profile. Not a generic PM interview template.
What does THIS company's process look like for THIS role level?

Claude presents the findings in a structured table:

```
| # | Round Name | Format | Duration | Focus |
|---|---|---|---|---|
| 1 | Recruiter Screen | Phone | 30 min | Background, fit, comp |
| 2 | Hiring Manager | Video | 60 min | Product sense, strategy |
| ...
```

You confirm or correct based on what the recruiter has told you. Any corrections
are incorporated — recruiter intelligence always overrides web research.

The confirmed process is written to the company card. This is permanent.

If it already exists (subsequent rounds): Claude reads the process section
and proceeds immediately to Phase 2.

#### Prep Phase 2 — Round-Specific Prep

Claude builds prep specific to the current round at this company:

- **What this round tests:** Based on the confirmed process, what is the
  interviewer actually assessing? (Product sense vs. behavioral vs. technical
  vs. executive fit — each is different.)
- **Company-specific patterns:** What do people who have interviewed at this
  company for this type of round actually report? Claude searches for this.
- **Prior round intelligence:** If this is Round 2+, what did the debrief
  from Round 1 tell you? What topics came up? What did the recruiter reveal?
- **Stories mapped to this round:** 3–5 situations from your profile that
  are most relevant to what THIS round tests, with specific guidance on how
  to frame each one for this company.
- **What to lead with:** A specific opening positioning statement for this round.
- **Questions to ask:** 4–5 questions calibrated to this exact round and interviewer.

#### Prep Phase 3 — Study Plan

Claude reads your calendar and builds a dated, hour-level study plan for the
time between now and the interview:

```
Study Plan: Acme Payments Round 2 — HM Product Sense
Interview: May 28 2PM PDT (5 days away)

May 24 (Sunday) — 3 hrs
  [ ] 1.5 hrs  Research Acme Payments billing platform product and passkeys strategy
  [ ] 1.5 hrs  Practice 3 lead stories for product sense frame

May 25 (Monday) — 1.5 hrs (afternoon, after your 4 morning calls)
  [ ] 1.5 hrs  Product sense framework practice — Acme Payments-specific scenarios

May 26 (Tuesday) — 2 hrs (morning, before Northwind call at 12PM)
  [ ] 2 hrs    Mock product sense session

Night before (May 27):
  [ ] 30 min   Re-read Acme Payments card: Product Gaps + Profile-Aware Analysis
  [ ] 15 min   Review your 3 lead stories out loud
  [ ] 10 min   Prepare your 5 questions for Mahendar
```

Claude also flags calendar conflicts — if you have 4 other interviews the same
week, it says so explicitly and prioritizes the study plan accordingly.

After Phase 3, Claude offers to run a mock interview in the format that company
uses for that round type.

The prep plan is logged to the company card.

### Phase: Debrief

Say: `"Debrief [company]"` or `"Log my [company] interview"`

**Run this within 2 hours of any completed interview round. Memory degrades fast.**

The 📝 DEBRIEF calendar block created automatically before the interview contains
the exact prompt to paste. Open it, copy it, paste it — that's the trigger.

Claude asks you questions in sets — not all at once:

1. **What happened:** Walk through the flow. What came up? Anything that surprised you?
2. **Performance:** What felt strong? What was uncertain? Any question you'd answer differently?
3. **Next steps:** What did they say happens next? Timeline, format, who you'll talk to?
4. **Recruiter signals:** Any explicit feedback? Enthusiasm? Hesitation?

Claude synthesizes your account into:
- What to carry forward (topics and stories that landed well)
- What to fix (questions that were weak → better answers logged)
- Next round intelligence (what this round revealed about what comes next)

Then Claude updates the company card:
- Marks the round as completed with date
- Adds any new round details the recruiter revealed
- Writes a dated Interview Notes entry with the full debrief
- Updates `stage`, `next_action`, and `last_updated`
- Commits and pushes

Finally, Claude gives you an honest assessment — positive signals, neutral, or
concerning — and offers to start prep for the next round immediately.

**The debrief is how the system compounds.** Everything learned in Round 1
becomes context for Round 2 prep. The company card gets richer with each round.

---

## When prep gets triggered

Prep isn't only triggered when you explicitly ask for it. Chrysalis surfaces it
proactively whenever the conditions are right. Here's every trigger:

### You ask for it
- `"Prep for [company] interview"` — the explicit command
- `"I have an interview at [company] in 3 days"` — same trigger, different phrasing

### Morning brief detects an upcoming interview with no prep logged
If an interview is within 5 days and no prep plan is on the card, the morning
brief will flag it and offer to run the planner immediately. Don't wait until
the night before.

### A debrief completes
The most important trigger. At the end of every debrief, Chrysalis offers to
start prep for the next round right then — while the recruiter's intel about
what comes next is freshest. This is when the handoff from "what just happened"
to "what do I need to do next" is most valuable.

### A new interview appears in email or calendar
When the email sweep finds a confirmed interview date that wasn't in the system,
Chrysalis flags it and offers to run prep if the date is within 5 days.

### You share new intel that changes the picture
This is the most underused trigger. Prep should be re-run or updated any time
you learn something that changes what to expect in the interview:

**Inside contact conversation:**
You talk to someone who knows the company, the team, or the interviewer.
Tell Claude what you learned. It will extract the signal, update the card,
and update the Phase 2 prep accordingly — sharpening the stories, reframing
the opening, adjusting the questions.

Example: *"I just talked to Amit. He said Mahendar cares most about product
taste and doesn't love over-structured STAR answers. He also said the team
is building toward agentic checkout auth."*
→ Claude updates the prep plan: lead with instinct not framework, add the
agentic checkout angle to relevant stories, update questions.

**Recruiter updates the format or focus:**
*"They just told me Round 3 will be a live case study instead of behavioral."*
→ Claude updates the Interview Process section and rebuilds Phase 2 for the
new format.

**Interviewer changes:**
*"I found out the HM interview is actually with the VP, not the director."*
→ Claude researches the VP, updates the company card, adjusts the prep
framing for a more senior audience.

**Any information that changes the answer to "what will they test you on?"**
→ Phase 2 should be updated. Don't walk in with a stale prep plan when you
have better information.

### What Chrysalis will say when it surfaces prep proactively

It won't wait quietly. It will say:

- *"Your Globex Wallet interview is in 4 days and no prep plan is logged. Want me
  to run the prep planner now?"*
- *"You just debriefed Round 2 at Acme Payments. The recruiter confirmed Round 3 is
  a panel with engineering. Want me to start that prep while the context is fresh?"*
- *"You shared intel from Amit that changes the Acme Payments prep. Want me to update
  Phase 2 with that information?"*

The bar for proactive surfacing is: if you walked into this interview right
now with what's on the card, would you be prepared for what's actually coming?
If the answer is no, prep gets triggered.

---

## Scheduling intelligence

Chrysalis treats scheduling as a strategic decision, not a calendar lookup.

### "When can I schedule [company]?"

Say: `"When can I schedule [company]?"` or `"When can I fit in a [company] call?"`

Claude loads all active pipeline cards and reads your calendar for the next
30 days. Then it answers with:

- **What type of interaction this is** — recruiter call, HM intro, technical screen, panel
- **Prep required** before the interview — and how much is already logged
- **Downstream commitment** — if this process continues, how many more rounds
  are likely? What's the total time commitment over the next N weeks?
- **Available windows** with reasoning — not just "Tuesday is free" but
  "Tuesday works because it's 3 days before your next interview, giving you
  prep time, and Wednesday is clear for any follow-up research"
- **Dates to avoid** — "The week of June 9 is risky; you're likely in Acme Payments
  final rounds and that prep cannot be bumped"
- **A specific recommendation**
- **Debrief block** — confirmed or offered immediately after every interview slot

### "Am I over-scheduled?"

Say: `"Am I over-scheduled?"` or `"How's my pipeline density?"`

Claude produces a density report:
- Active processes by stage (screening, interviewing, final_round)
- A week-by-week map of upcoming interviews and whether prep is logged
- Prep coverage assessment — any interview within 3 days with no prep flagged
- An honest recommendation: which to prioritize, which to consider rescheduling

For strategic pacing, Claude can project a 4-week outlook: "At current pace,
you'll likely be in final rounds at 2–3 companies simultaneously around
[date]. That's when prep discipline matters most."

---

## Company tiers and prioritization

Your `data/profile/me.md` defines Tier 1 and Tier 2 companies. This matters for:

- **Scheduling conflicts:** When prep time is scarce, Tier 1 prep takes priority.
  Claude will say so explicitly rather than letting a Tier 2 commitment crowd out
  a Tier 1 interview.
- **Prep depth:** Tier 1 companies get full Phase 1–3 prep. Tier 2 recruiter
  screens may get a lighter version.
- **Morning brief priority:** Tier 1 news signals surface first.

Update your tier assignments as the search evolves. A company that was Tier 2
can become Tier 1 when you learn the HM is a domain expert you'd genuinely
want to work for. Say `"Update my profile"` to adjust.

---

## What good usage looks like week to week

**Sunday night:**
- Say `"Brief"` to see what's coming this week
- Check if any upcoming interviews lack prep
- If yes: `"Prep for [company] interview"` now while you have time

**Every interview morning:**
- Open the company card — re-read Interview Notes and Profile-Aware Analysis
- Review your lead stories

**Within 2 hours of each interview:**
- Open the 📝 DEBRIEF calendar block → copy the prompt → paste into Claude
- Or say: `"Debrief [company]"` — while it's fresh

**End of week:**
- `"Where do I stand"` — weekly pipeline health check
- Reflect on what's working and what to change

**When a new company arrives:**
- `"Research [company]"` — get the card populated before the first call

**When something changes (new round confirmed, offer received, process paused):**
- Tell Claude — it updates the card and index immediately

---

## Command reference

| Say this | What it does |
|---|---|
| `"Brief"` / `"Morning brief"` | Full daily brief + email sweep + calendar read |
| `"Sweep"` / `"Run sweep"` | Background email + calendar check between briefs |
| `"Enable automatic sweep"` | Creates a scheduled sweep that runs every N hours automatically |
| `"Disable automatic sweep"` | Turns off the scheduled sweep |
| `"Check sweep status"` | Shows last run time, next scheduled run, and whether the task is active |
| `"Research [company]"` | Full web research → company card written |
| `"Prep for [company] interview"` | Three-phase prep planner |
| `"Prep for [company] [round]"` | Same, anchored to a specific round |
| `"Debrief [company]"` | Post-interview debrief → card updated |
| `"When can I schedule [company]?"` | Strategic scheduling advisor |
| `"Am I over-scheduled?"` | Pipeline density report |
| `"Where do I stand"` | Weekly pipeline health review |
| `"Set up my profile"` | One-time profile setup from resume |
| `"Update my accounts"` | Reconfigure email + calendar connections |
| `"I'm ready to start"` | Onboarding sweep — creates all initial cards |

---

## Tips for getting the most out of Chrysalis

**Be specific in debriefs.** "It went well" tells the system nothing.
Walk through the questions that came up. Claude will ask follow-up questions
to pull out what matters. The more specific the debrief, the sharper the
next round prep.

**Give the recruiter's exact words.** When a recruiter tells you what the next
round tests, or who the interviewer is, or what the HM cares about — paste it
verbatim into the debrief. That information is worth more than any Glassdoor post.

**Use inside contacts.** Before a high-stakes round, say "I'm going to talk to
[Name] who is ex-[Company] before this interview." Claude will log the contact,
tell you what intel to extract from that conversation, and build the next
prep run around what you bring back.

**Let Chrysalis push back.** If the answer to "Am I over-scheduled?" is yes,
the right response isn't to add more to the calendar. The whole point of the
scheduling advisor is to tell you when to slow down — listen to it.

**Prep Phase 1 is one-time per company.** Once the Interview Process section
is confirmed on the card, it stays there. Subsequent prep runs skip directly
to Phase 2. The investment in researching the company's process pays off
across every round.

**Use the "Improve this research" button.** On every company card in the
Companies tab, there's a collapsible section at the bottom with a pre-filled
prompt. If you spot something wrong or missing — a stale funding figure, a
missed product line, a wrong team org — click Copy, paste into Claude, done.
Two steps. No manual card editing.

---

## Keeping this guide current

As Chrysalis evolves — new workflows, new commands, new patterns learned from
actual use — this guide should be updated to match. At the end of any session
where a meaningful new pattern is established, say:

`"Update the user guide with what we just built."`

Claude will add the relevant section or update what's stale. The goal is that
this file always reflects how the system actually works, not how it worked six
months ago.
