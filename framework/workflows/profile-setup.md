# Chrysalis Profile Setup Workflow

## Purpose
Populate data/profile/me.md from the user's resume file. Extract everything
extractable automatically, then ask targeted questions only for what a
resume won't have. Goal: a complete, useful data/profile/me.md in one pass.

## When to Run
- When a new user is setting up Chrysalis for the first time
- When the user says "set up my profile", "I have a resume", or similar
- When data/profile/me.md is still in its blank template state

## Executed by
Claude Code

## Inputs
- Resume file (PDF preferred; Word .docx also works)
- Short answers to 4–5 clarifying questions

## Related workflows
This is one of three workflows that make up first-run onboarding. The
"Onboard me" master command in CLAUDE.md chains them in order:

1. **`profile-setup.md`** (this workflow) — resume → `data/profile/me.md`
2. **`accounts-setup.md`** — Apple Calendar + email accounts → `data/config/accounts.yaml`
3. **`onboarding-sweep.md`** — pipeline cards from user input

This workflow stays focused on the profile alone. Account configuration
is handled separately by `accounts-setup.md`.

---

## Steps

### Step 1 — Request the resume file

Say exactly this to the user:

> "To set up your Chrysalis profile, please attach your resume file.
> PDF works best, but a Word doc is fine too."

Wait for the file. Do not proceed until it is attached.

### Step 2 — Read and extract from the resume

Once the file is attached, read it in full. Extract the following,
noting what is found and what is absent:

**Professional Background**
Pull: current role, company, tenure; prior roles in reverse chronological order;
total years of experience; domains and industries worked in.
Format as a short narrative paragraph, not a bullet list of job titles.

**Skills & Strengths**
Pull: technical skills, tools, methodologies; soft skills if mentioned;
any explicit "known for" or "strengths" language the user used to describe themselves.

**Professional Lens**
Infer from job titles and responsibilities:
- PM / CPM / Director of Product / Head of Product / VP Product → PM
- Engineer / SWE / Developer / Architect / CTO → Engineer
- Designer / UX / UI / Creative Director → Designer
- Anything else → Other (ask to confirm)

Note what you inferred and why — the user will confirm in Step 3.

**Geographic Constraints (partial)**
Pull: current city/region if listed on the resume.
Note: remote/hybrid preference is almost never on a resume — you will ask.

**Target Role (partial)**
Infer from career trajectory: most recent title + seniority level is
usually what they're targeting at minimum. Note the inference — the user
will confirm and add nuance in Step 3.

### Step 3 — Ask only what the resume can't tell you

Present what you extracted so far, then ask exactly these questions.
Ask them all at once — do not ask one at a time.

---

> Here's what I pulled from your resume:
>
> - **Background:** [2-3 sentence summary]
> - **Lens:** [PM / Engineer / Designer / Other] — [brief reason for inference]
> - **Location:** [city/region from resume, or "not listed"]
>
> A few quick questions to complete your profile:
>
> 1. **Target role:** What title and seniority level are you going for?
>    (e.g. "Senior PM", "Director of Product", "Staff Engineer")
>    And what kind of work excites you most right now?
>
> 2. **Target companies:** What kind of company are you looking for?
>    Think about: stage (seed / Series A–C / growth / enterprise),
>    industry, company size, culture signals that matter to you.
>
> 3. **Location & work style:** Where are you based, and what's your
>    stance on remote / hybrid / in-office? Any cities you'd relocate to?
>
> 4. **Hard constraints:** What will you not do? Industries to avoid,
>    role types that don't fit, company cultures that are a dealbreaker.
>
> 5. **Search status:** Are you actively looking, passively open, or
>    just exploring right now?

---

Wait for the user's answers before proceeding.

### Step 4 — Clarify lens if ambiguous

If the Professional Lens was unclear from the resume (e.g. the user has
a hybrid background, or titles don't map cleanly), ask:

> "Your background spans [X and Y]. For Chrysalis, your lens determines
> how company analysis gets generated. Which fits best:
> PM, Engineer, Designer, or Other?"

This is the single most important field — it controls how every company
card is analyzed. Get a clear answer.

### Step 5 — Generate the complete data/profile/me.md

Using all extracted data and the user's answers, write the complete
populated data/profile/me.md. Follow this exact structure:

```markdown
---
card_id: data/profile/me
card_type: personal_profile
priority: always_load
updated: [today's date YYYY-MM-DD]
---

# My Profile

## Professional Background
[Narrative paragraph from resume. Current role first, then career arc.
Include years of experience, domains, industries. 3–5 sentences.]

## Skills & Strengths
[What they are known for, technical and interpersonal.
Write as strengths, not a keyword dump.]

## Professional Lens
[Their confirmed lens: PM | Engineer | Designer | Other]
Lens: [PM | Engineer | Designer | Other]

## Target Role
[What they are going for: title, seniority, type of work that excites them.
Be specific — this is what Claude uses to filter opportunities.]

## Target Companies
[Stage preference, industry, size, culture signals.
Write in plain language, not bullet points.]

## Geographic Constraints
[City/region, remote/hybrid/in-office stance, relocation willingness.]

## Constraints & Non-Negotiables
[What they won't do. Industries, role types, cultures to avoid.
Be specific — this is a filter, not a formality.]

## Search Status
[Active | Passive | Exploratory]
Started: [today's date if unknown, or ask]

## Notes
[Anything else that came up in conversation that Claude should know.
If nothing, write: "None yet."]
```

### Step 6 — Present and confirm

Present the completed data/profile/me.md in full.

Then say:

> "Does this look right? Take a moment to read through it — especially
> the Target Role, Target Companies, and Constraints sections, since
> those shape how I'll analyze opportunities for you.
>
> Once you're happy with it, save it to `data/profile/me.md` in your repo.
> If you have Claude Code open in your local repo, I can write it
> directly — just say the word."

Wait for the user to confirm or request changes before finalizing.

### Step 7 — Write the file (if Claude Code is available)

If the user confirms and has Claude Code available:
- Write the final content to `data/profile/me.md`
- Update `data/manifest.yaml`: set `updated` for the `data/profile/me` card to today's date
  and update the summary to reflect the user's actual background
- Commit with message: `"update: data/profile/me initial setup from resume"`
- Push to GitHub

---

## Notes
- Do not reproduce the resume verbatim. Synthesize and rewrite in the
  user's voice — the profile should read like something they wrote, not
  like a parsed document.
- If the resume is sparse or non-standard (e.g. a consultant CV, an
  academic CV, a portfolio site PDF), adapt. Extract what's there and
  ask more questions in Step 3 to fill the gaps.
- The Lens field is non-negotiable — do not leave it blank or set it
  to Other without asking. It controls profile-aware analysis across
  the entire system.
- If the user wants to update their profile later (new role, changed
  target, updated constraints), run this workflow again from Step 3 —
  skip the resume extraction and just ask the questions fresh.
