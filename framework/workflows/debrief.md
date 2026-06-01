# Chrysalis Debrief Workflow

## Purpose
Capture what happened in a completed interview round, update the company card,
and set up the next round. The debrief is how the system compounds — each round's
notes become inputs for the next prep plan. Don't skip it.

## When to Run
- Immediately after any interview round (while it's fresh — ideally within 2 hours)
- When the user says "Debrief [company]" or "Log my [company] interview"
- When the morning brief detects a completed interview with no debrief logged

## Executed by
Claude Code

## Inputs
- data/pipeline/[company-name].md (the company card — required)
- data/profile/me.md (for context)
- User's verbal account of what happened

---

## Steps

### Step 1 — Identify the round

Read the company card. Identify which round just completed:
- Which round number (based on the Interview Process section)?
- Who was the interviewer?
- What was the confirmed format and focus?

If the Interview Process section is empty or the round isn't listed: ask the user
to clarify which round this was and add it to the process section as part of this debrief.

### Step 2 — Ask debrief questions

Ask the following, one set at a time (not as a wall of questions):

**On what happened:**
- "How did it go overall — what's your gut read?"
- "What topics or questions came up? Walk me through the flow."
- "Was there anything that surprised you — something you didn't expect them to ask?"

**On performance:**
- "What felt strong? What did you land well?"
- "What felt uncertain or weak? Anything you'd answer differently?"
- "Were there any questions you didn't have a great answer for?"

**On next steps:**
- "What did they tell you about what happens next?"
- "Do you know who conducts the next round, what the format is, or when it'll happen?"
- "Did they give you any explicit feedback or signal during the call?"

**On comp / logistics (if recruiter round):**
- "Did comp come up? If so, what range did they mention or ask about?"
- "Any logistical details to note (location, timeline, start date expectations)?"

Listen carefully. Ask follow-up questions if the user's account is vague on
something that will matter for the next round.

### Step 3 — Synthesize the debrief

From the user's account, extract:

**What to carry forward:**
- Topics or themes that are likely to recur in future rounds
- Stories or framings that landed well (use them again)
- Signals about what the company values (explicit or implied)

**What to fix:**
- Questions that landed poorly — identify the better answer and note it
- Gaps in knowledge that surfaced — flag for study before next round
- Framing choices that weakened the narrative — suggest the correction

**Next round intelligence:**
- What is the next round? Format, interviewer, timing?
- What does this round's debrief tell you about what the next round will test?

### Step 4 — Update the company card

Write to the company card:

**Interview Process section:**
- Mark this round as Completed with the date
- Update any round details that became clearer (e.g., Round 2 details revealed by recruiter)
- Add any new rounds the recruiter described
- Update `user-confirmed: yes` and `last-updated` date

**Interview Notes section:**
Add a dated entry:

```markdown
### Round [N] — [Round Name] — [Date]
**Interviewer:** [Name, Title]
**Format:** [Video / Phone / Onsite] | [Duration]
**Overall:** [User's gut read — 1 sentence]

**What came up:**
- [Topic/question and how it went]
- [Topic/question and how it went]

**What landed:**
- [Story or framing that worked well]

**What to fix:**
- [Question that was weak → better answer]

**Next round:**
- Format: [what they said]
- Interviewer: [who they said]
- Timeline: [when they said]
- Focus: [any hints given]

**Recruiter signals:** [Anything notable — enthusiasm, hesitation, timeline urgency]
```

**Front-matter:**
- Update `stage` if it changed (e.g., screening → interviewing after HM confirmation)
- Update `next_action` to reflect the next round or follow-up action
- Update `last_updated`

**data/manifest.yaml:**
- Update `stage`, `next_action`, and `updated` to match the card

### Step 5 — Assess and advise

After logging, give a brief honest read:

**Signal strength:** Based on what the user described, how does this look?
- Strong positive signals (they asked about start date, expressed enthusiasm, fast next steps)
- Neutral / standard (normal process, no read either way)
- Concerning signals (long silence, vague next steps, interviewer seemed disengaged)

Be honest. Don't manufacture optimism.

**What the next round demands:**
Based on the updated Interview Process section, what does the next round test?
How does what just happened change the prep approach for it?

"Based on what you told me, Round 2 (HM Product Sense with Mahendar Madhavan)
will likely focus on [X]. The fact that you mentioned [Y] in Round 1 means
you should be ready to go deeper on [Z]."

### Step 6 — Offer next round prep

"Do you want me to start building the prep plan for Round [N+1]?
I can do it now while the context is fresh, or flag it for the next session."

If yes: hand off to prep-planner.md for the next round.
If no: log a note that prep for Round N+1 is pending and surface it in the next morning brief.

### Step 7 — Commit and push

Stage and commit all changes to the company card and data/manifest.yaml.
Commit message: `update: data/pipeline/[company] debrief round [N] [date]`

---

## Notes

- The debrief is the most time-sensitive workflow. Memory of exactly what was asked
  and how it felt degrades fast. Run it within 2 hours of the interview if possible.
- If the user says "it went fine" without detail: push gently. "Fine" doesn't help
  prep the next round. Ask specifically about the hardest question they faced.
- Recruiter rounds often reveal the most about the actual process — pay close attention
  to what the recruiter says about upcoming rounds, timelines, and what the HM cares about.
- A negative signal is useful data. Log it honestly. It helps the user decide whether
  to invest more prep time in this pipeline or shift attention elsewhere.
