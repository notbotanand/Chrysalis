# Chrysalis Prep Planner Workflow

## Purpose
Build a precise, round-specific preparation plan for an upcoming interview.
Researches the company's actual interview process for this role profile,
confirms it with the user, stores it on the card, then generates prep
for the specific round at hand — not a generic template.

## When to Run

### User-initiated
- When the user says "Prep for [company] interview" or similar
- When the user says "I have an interview at [company] in [N] days"

### System-triggered (proactive)
- When the morning brief detects an upcoming interview within 5 days with no prep logged
- When a new interview is found in an email or calendar sweep and is within 5 days
- When the user moves to a new round at a company already in the pipeline

### After a debrief
- Immediately after any debrief completes — the debrief workflow offers to hand off
  to prep-planner for the next round. This is the most important trigger.
  The debrief has just captured what the company cares about, what round is next,
  and what the interviewer revealed. Running prep immediately while that context
  is fresh produces the sharpest plans.

### When the user shares new intel
Run prep (or re-run Phase 2 if prep already exists) whenever the user shares
information that meaningfully changes what to expect in the round:

- **Inside contact conversation:** "I just talked to [person] who knows the team —
  here's what they said." Extract the signal, update the card, re-run Phase 2
  with the new context incorporated.
- **Recruiter update:** Round format changed, interviewer changed, focus area
  confirmed. Update the Interview Process section and rebuild the prep.
- **Process change:** "They told me Round 3 will be a case study, not behavioral."
  Update the process table, flag what prep material changes as a result.
- **Anything that changes the answer to "what will they test you on?"**

### What NOT to wait for
Do not wait for the user to explicitly ask. If any of the above conditions are
met, surface it: "Your [company] interview is in 3 days and no prep plan is
logged — want me to run it now?" or "You just shared new intel on [company]
that changes the prep — want me to update Phase 2?"

## Executed by
Claude Code

## Inputs
- data/pipeline/[company-name].md (the company card — required)
- data/profile/me.md (always loaded)
- Web search (company-specific interview process research)
- Calendar (for study plan scheduling — read via AppleScript if available)

---

## Phase 1 — Know the Process

### Step 1.1 — Load and assess

Read the company card and data/profile/me.md.

Identify:
- **The role being interviewed for** (title, team, level)
- **The current round** (what interview is coming up — recruiter screen, HM, panel, etc.)
- **What round number this is** (first contact, or Nth round?)
- **What is already known** from prior rounds (check Interview Notes section)

Check the card's **Interview Process** section:
- Does it exist for this role?
- Was it user-confirmed?
- Is it stale (last updated before the most recent round)?

If the Interview Process section is populated and confirmed: skip to Phase 2.
If it is empty, incomplete, or not yet confirmed: proceed to Step 1.2.

### Step 1.2 — Research the company's interview process

Do NOT use generic assumptions about what a PM interview looks like.
Research what THIS company actually does for THIS role profile.

Run the following searches (adapt queries to the user's lens — PM / Engineer / Designer):

```
Search 1: "[company] [role type] interview process [year]"
Search 2: site:glassdoor.com "[company]" interview "[role type]"
Search 3: "[company] PM interview rounds reddit OR blind"
Search 4: "[company] product manager interview experience"
Search 5 (if HM or later round): "[company] [role type] interview questions"
```

Synthesize findings:
- How many rounds does this company typically run for this role?
- What is each round's format, duration, and focus?
- Who typically conducts each round (recruiter, HM, peer PM, exec, panel)?
- Are there any company-specific signals (take-home, case study, BrightHire recording,
  loop format, written exercise, technical screen, etc.)?
- How recent is this information? Flag if sources are older than 18 months.

If sources are thin or conflicting: say so explicitly.
Do not fabricate rounds. Present what is known, mark the rest as TBD.

### Step 1.3 — Present findings and confirm with user

Present the researched process clearly:

---
"Here's what I found about [Company]'s [Role Type] interview process:

**Typical process (based on [sources, dates]):**
| Round | Format | Duration | Focus |
|---|---|---|---|
| 1 — Recruiter Screen | Phone/Video | 30 min | Background, role fit, comp |
| 2 — Hiring Manager | Video | 60 min | Product sense, strategy, leadership |
| 3 — Panel | Video loop | 3-4 hrs | Behavioral, domain depth, cross-functional |
| 4 — Executive Screen | Video | 30-45 min | Values, vision alignment |

**Company-specific notes:** [Anything distinctive found]
**Source confidence:** [High / Medium / Low — and why]

You're currently preparing for Round [N]: [Round Name].

Does this match what you know? The recruiter may have given you more specific
information — correct anything that's wrong before I build the prep plan."
---

Wait for confirmation. Do not proceed to Phase 2 until the user confirms or corrects.

### Step 1.4 — Write process to company card

Once confirmed:
- Write the Interview Process section to the company card
- Include: round table, process notes, sources, user-confirmed: yes, date
- Update `last_updated` in front-matter
- Commit and push

If the user made corrections: incorporate them and note what was changed from
the researched version vs. what the user confirmed from direct recruiter context.

---

## Phase 2 — Build Round-Specific Prep

The prep plan is specific to the current round. It must reference:
- What this particular round tests (from the confirmed process)
- What this company specifically looks for (from research + card)
- What happened in previous rounds (if any — from Interview Notes)
- What the user's profile offers that maps to this round's criteria

### Step 2.1 — Characterize this round

Based on the confirmed round details:

**What is being assessed?**
- Recruiter screen: background coherence, role fit, enthusiasm, comp alignment
- HM / intro call: product thinking, leadership signals, culture fit
- Product Sense: product design, metrics, strategy, analytical rigor
- Behavioral / leadership: STAR stories, cross-functional influence, conflict resolution
- Technical / domain: depth of technical knowledge, architecture judgment
- Case study: structured problem-solving, business acumen, communication
- Executive screen: strategic vision, company mission alignment, leadership philosophy
- Panel: breadth across multiple dimensions — often a mix of the above

**Company-specific patterns for this round type:**
Search specifically: "[company] [this round type] interview questions 2024 2025"
Synthesize: what do people report being asked in this exact type of round at this company?

**What prior rounds revealed:**
If this is Round 2+, read the Interview Notes from prior rounds:
- What topics came up that are likely to continue?
- What did the company signal they care about?
- Any explicit feedback received?
- What did the user flag as uncertain or weak?

### Step 2.2 — Map profile to this round

Read data/profile/me.md and identify:

**Stories to use for this round:**
Identify 3-5 situations from the user's background that are most relevant
to what this round tests. For each story:
- **Label** (e.g. "Scaling OpenPass from 0 to 150K users")
- **Why it fits this round** (specific to what this company/round tests)
- **What to tighten** (specifics, metrics, outcome, framing for this audience)
- **What to cut** (what makes this story weaker — don't lead with it)

**Technical/domain positioning for this round:**
If this is a domain-heavy round: identify which parts of the user's expertise
are most directly relevant and what vocabulary to use.

**Questions to ask:**
Generate 4-5 questions calibrated to this specific round and interviewer.
A recruiter screen gets different questions than a panel with engineers.
Questions should reflect genuine curiosity AND demonstrate knowledge of the company.

### Step 2.3 — Compile the prep output

Produce:

**Round context**
One paragraph summarizing what this round is, what it tests, and what
this specific company's version of it looks like. No fluff.

**What to lead with**
The single clearest positioning statement for this round:
"In this round, your most powerful opening is: [specific framing].
This is because [reason tied to what this company/round values]."

**Stories sharpened for this round** (3-5)
See Step 2.2 format above.

**Company-specific prep items**
Anything distinctive to this company's version of this round type.
E.g.: "Acme Payments Product Sense is known to focus on their existing product
portfolio — be ready to redesign an Acme Payments feature, not just a generic app."

**Questions to ask** (4-5, calibrated to this round)

**What to re-read on the card**
The 1-2 most important sections of the company card to review the night before.

---

## Phase 3 — Study Plan + Calendar

### Step 3.1 — Estimate prep time needed

Based on round type and what was found in Phase 2:

| Round type | Typical prep time |
|---|---|
| Recruiter screen | 1-2 hours |
| HM intro / values | 2-4 hours |
| Product Sense / case | 1 full day (4-6 focused hours) |
| Behavioral / leadership | 3-4 hours |
| Technical / domain | 1-2 days |
| Panel / loop | 2-3 days |
| Executive screen | 2-3 hours |

Adjust based on: how much company research exists already on the card,
how well-worn the user's stories are for this domain, round complexity.

### Step 3.2 — Read the calendar

Read the next 7 days of calendar via AppleScript if available:
```javascript
// JXA — get events between now and interview date
const Calendar = Application('Calendar');
// [read events in range]
```

If calendar is not accessible: ask the user "What does your schedule look like
between now and [interview date]? I'll build the study plan around your free time."

Identify:
- Hours available between now and the interview
- Other interviews in that window (and their own prep needs)
- Non-negotiable blocks (other meetings, personal commitments)

### Step 3.3 — Build the dated study plan

Produce a specific, hour-level plan for the time available.
Do not produce a generic checklist. Every item has a day, a time estimate,
and a specific output or action.

Example format:
---
**Study Plan: [Company] Round [N] — [Round Name]**
Interview: [Date, Time, Format]
Total prep time available: [X hrs across Y days]

**[Day, Date] — [total hrs]**
- [ ] [Time estimate] [Specific task] → [What done looks like]
- [ ] [Time estimate] [Specific task] → [What done looks like]

**[Day, Date] — [total hrs]**
- [ ] [Time estimate] [Specific task] → [What done looks like]

**Night before:**
- [ ] 30 min Re-read: [specific card sections]
- [ ] 15 min Review your 3 lead stories out loud
- [ ] 10 min Prepare your 5 questions for the interviewer
---

### Step 3.4 — Offer mock session

After presenting the study plan:

"Want to do a mock run for this round now or after you've done the prep reading?
I'll simulate the interview in the format [company] uses for this round and give
feedback after each answer."

If now: run the mock immediately in the confirmed round format.
If later: note in the card that a mock session is planned.

### Step 3.5 — Log the prep plan to the card

Write to the company card:
- Add a dated prep plan entry to the Interview Notes section
- Format: "**[Date] Prep plan generated — Round [N] [Round Name]:** [key themes, study plan summary]"
- Update `next_action` to the first item on the study plan
- Commit and push

---

## Notes

- **Never hardcode interview stages.** The process comes from research + user confirmation,
  not from a template. Two companies hiring for "Senior PM" have completely different processes.

- **The process section compounds over time.** After Round 1 is complete and debriefed,
  the recruiter will have told you about Round 2. That information updates the process section
  and becomes the input for the next prep run. Run `Debrief [company] round` after each
  interview to capture this before it's forgotten.

- **If the interview is under 24 hours away:** Skip Phase 3 in full. One sharp story,
  three good questions, and clear positioning beats a panicked five-hour study session.
  Triage ruthlessly.

- **If company research card is thin:** Before building prep, check whether the
  company-research workflow should run first to populate the Profile-Aware Analysis section.
  Prep built on a shallow card will be shallow.

- **Calendar density matters:** If the user has multiple interviews in the same week,
  note explicitly which prep items to prioritize if time is cut short. The study plan
  should have a "minimum viable prep" tier and a "full prep" tier.
