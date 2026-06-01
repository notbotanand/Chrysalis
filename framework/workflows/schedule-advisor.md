# Chrysalis Schedule Advisor Workflow

## Purpose
Answer scheduling questions strategically — not just "when is a free slot"
but "here is what this commitment means for your time, prep load, and pipeline
health over the next 4 weeks." Behaves like a Chief of Staff managing a
high-stakes calendar.

## When to Run
- When the user says "When can I schedule [company / interview type]?"
- When the user says "Am I over-scheduled?" or "Is my calendar too full?"
- When the morning brief detects calendar density that risks prep coverage
- When a new opportunity arrives and the user needs to decide when to engage

## Executed by
Claude Code

## Inputs
- data/manifest.yaml (pipeline state — all active companies and stages)
- data/pipeline/[all active company cards] (Interview Process sections — to assess
  how many rounds are likely remaining for each)
- data/profile/me.md (for any scheduling constraints — location, travel, timezone)
- Calendar (read via AppleScript for next 30 days)

---

## Steps

### Step 0 — Classify the Interaction Type

Before producing any slot recommendations, identify what type of interaction
is being scheduled. This determines slot duration, prep time required, and
downstream commitment. Never answer a scheduling question without first
classifying the interaction.

| Type | Slot Duration | Prep Required Before | Debrief Block After | Downstream |
|---|---|---|---|---|
| Recruiter screen | 30 min | ~30 min (quick company scan) | Optional | 2–5 more rounds |
| HM intro / phone screen | 45–60 min | 2–3 hrs | Yes — 15 min | 2–4 more rounds |
| Technical / product screen | 60–90 min | 4–6 hrs | Yes — 15 min | 2–3 more rounds |
| Panel / loop (full day) | 3–5 hrs | 8–12 hrs | Yes — 15–30 min | 1–2 more rounds |
| Final / exec round | 45–60 min | 2–3 hrs | Yes — 15 min | Decision |
| Reference / offer call | 30 min | None | None | Negotiation |

**If the type is unclear, ask before proceeding:**
> "Is this a recruiter call, an HM intro, a technical screen, or a panel?
> The prep time and slot recommendation differ significantly."

**Check preparation readiness:**
- Is the company card research-complete? (`last_user_research_updated` is set and not null)
- Is there an existing prep plan for this round?
- If research is thin or prep plan is absent AND the interview is within 5 days:
  Ask: "How prepared do you feel going into this [Company] round?
  I want to make sure the slot I recommend leaves enough prep time before it."
- If research is thin, flag it: "The [Company] card hasn't been fully researched yet.
  I'd recommend running company research before we lock in a slot."

---

### Step 1 — Read the full picture

Before answering any scheduling question, load the full context:

**From data/manifest.yaml:**
- All active pipeline companies and their current stage
- Upcoming next_actions with any dates

**From active company cards (Interview Process sections):**
- For each active company: how many rounds are confirmed or likely remaining?
- What is the prep time required for each upcoming round?
- Example: Acme Payments at HM round → likely 2-3 more rounds if they proceed
  (panel + possibly exec screen) = significant downstream commitment

**From calendar (AppleScript):**
```javascript
// JXA — read all calendar events for next 30 days
const Calendar = Application('Calendar');
const now = new Date();
const future = new Date();
future.setDate(future.getDate() + 30);
// [read events, filter noise, return interview events + busy blocks]
```

If calendar is not accessible: ask the user for their schedule overview.

Build a mental model:
- Which days have confirmed interviews?
- Which days have prep committed (study plan blocks)?
- Which days are genuinely free?
- What is the prep backlog — interviews with no prep plan logged yet?

### Step 2 — Assess current pipeline density

**Interview density:** How many live processes are active right now?
Count companies at stage: screening, interviewing, final_round.

**Prep coverage:** For each upcoming interview within 14 days:
- Is a prep plan logged?
- Is there enough time between now and the interview to prep?
- Does the prep compete with other interview prep in the same window?

**Downstream load:** For each active company, estimate total remaining time commitment:
- Remaining rounds × prep time per round + interview time
- Example: Globex Wallet at round 1 of likely 3 rounds = ~8-12 hrs total remaining commitment
  (2 hrs round 1 prep already done + 4-6 hrs for HM prep + 6-8 hrs for panel prep)

**Flag over-scheduling if:**
- More than 2 active interview processes with upcoming rounds in the same week
- An interview is within 3 days with no prep plan logged
- The calendar shows back-to-back interviews with no prep gaps
- Total estimated remaining prep hours exceed available free hours in the next 7 days

### Step 3 — Answer the scheduling question

**If the question is: "When can I schedule [new opportunity]?"**

Determine what type of interaction this is:
- Recruiter screen: lowest commitment (30 min interview + 1-2 hrs prep)
- HM intro: medium commitment (60 min + 3-4 hrs prep)
- Multi-round process: significant downstream commitment

Produce a specific recommendation:

---
"For a [type] with [company], here's the picture:

**Prep required:** [X hours] before the interview
**Downstream:** If this progresses, expect [N rounds] more after this —
rough total commitment of [Y hours] spread over [Z weeks]

**Available windows:**
- [Date/time]: [Why this works — what's before/after, prep gap available]
- [Date/time]: [Why this works]
- [Date/time]: [Why this is possible but tighter]

**I'd avoid:**
- [Date range]: [Why — e.g., Acme Payments HM is the day after, no prep buffer]

**My recommendation:** [Specific date + reasoning]

**One thing to consider:** You currently have [N] active processes.
Adding [company] means [specific implication — e.g., 'you'll be in prep
mode every day next week with no buffer if anything slips.']"
---

**If the question is: "Am I over-scheduled?"**

Produce a density report:

---
**Pipeline density as of [date]:**

Active processes: [N companies in screening/interviewing/final_round]

**This week:**
| Day | What's happening | Prep logged? |
|---|---|---|
| Mon Apr 20 | Globex Wallet 10AM, Stratify Bio 10:30AM, Halcyon Health 11:30AM, Initech 12:30PM | [status] |
| Tue Apr 21 | Northwind CEO 12PM | [status] |
| Wed Apr 22 | Verifibase phone screen 3PM | [status] |
| Thu Apr 23 | Acme Payments HM 2PM (Product Sense) | [status] |

**Assessment:** [honest read]
- "This week is extremely dense. 4 interviews Monday is not a prep problem —
  it's a performance problem. You cannot be sharp in interview 4 if you started
  at interview 1 at 10AM. Consider: which of Monday's calls can move?"
- "Acme Payments HM (Apr 23) is the highest-stakes event this week and there is no prep
  day before it. Wednesday is Verifibase, Tuesday is Northwind. When does Acme prep happen?"

**Recommendation:**
[Specific, honest advice — which interviews to prioritize prep for, which to
consider rescheduling, what the minimum viable prep scenario looks like]
---

**If the question involves strategic pacing (not just scheduling):**

Go further: "You have 11 active companies. Here is what this realistically
looks like over the next 4 weeks if all of them proceed to next rounds..."

Produce a 4-week outlook:
- Week 1: [confirmed interviews + likely next rounds from companies in screening]
- Week 2: [projected based on typical process timelines]
- Week 3: [projected]
- Week 4: [projected]

Identify: "At current pace, you'll likely be in final rounds at 2-3 companies
simultaneously around [date]. That is when scheduling discipline matters most.
I'd recommend [specific advice — e.g., 'slow the top of funnel now' or 'prioritize
Tier 1 companies for final round timing']."

### Step 4 — Surface prep gaps

After answering the scheduling question, always surface prep coverage:

"One thing to flag: you have [interview] in [X days] with no prep plan logged.
Want me to run the prep planner for that one now?"

Prioritize by: interview date (soonest first), stakes (HM+ rounds over recruiter screens),
and domain fit (Tier 1 companies over Tier 2).

### Step 5 — Offer to write calendar blocks

If the user confirms a scheduling decision:

"Want me to note these prep blocks in the study plan? I can add them to the
[company] card so they show up in your morning brief."

Write the blocks to the card's Interview Notes under a "Study Plan" entry.

If Apple Calendar write access is available via AppleScript:
"Want me to add the prep blocks directly to your calendar?"
Only do this with explicit confirmation — never write to calendar without asking.

**Debrief block — always offer this:**
Whenever a specific interview time is confirmed, recommend a 15-minute debrief
window immediately after the interview ends. Debrief quality degrades fast —
within 2 hours the texture of what happened is gone.

Say:
> "I'd also recommend blocking [interview end time] – [end + 15 min] right after
> for a quick debrief while it's fresh. Want me to note that in the [Company] card?"

Apply this to: HM intros, technical screens, panels, final rounds.
For recruiter screens: offer it, but it's optional.
For offer/reference calls: skip.

Do not wait for the user to remember to debrief. Surface this every time
a confirmed interview slot comes up in a scheduling conversation.

---

## Notes

- **Never just answer "Tuesday at 2PM is free."** That is a calendar app, not a Chief
  of Staff. The answer always includes context: what else is happening, what prep is needed,
  what the downstream commitment looks like.

- **Be honest about over-scheduling.** If the user has too many active processes to
  prep for properly, say so. The goal is not to fill the calendar — it's to perform
  well in the right interviews.

- **Respect the user's actual constraints.** Read data/profile/me.md for location, visa status,
  family commitments mentioned, or any constraints that affect scheduling.
  Don't suggest 8AM calls if the user hasn't mentioned being an early riser.

- **Strategic pacing is the real value.** The most important scheduling questions are not
  "when is a free slot" but "should I be in this process at all right now" and "if I
  accelerate Company A, what does that mean for Company B's timeline." Surface these
  when relevant.

- **Pipeline prioritization context:** Always keep the user's Tier 1 vs. Tier 2
  company distinctions in mind (from data/profile/me.md). When scheduling conflicts arise,
  Tier 1 prep takes priority over Tier 2 prep. Never let a generic role bump a Tier 1
  interview prep.
