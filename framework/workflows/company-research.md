# Chrysalis Company Research Workflow

## Purpose
Build a fully populated company card from scratch using web research.
This is a one-time foundational requirement for every new company that
enters the knowledge base, and an on-demand refresh thereafter.

## When to Run

**Mandatory — run once at card creation:**
- When a new company card is created via onboarding sweep or manually
- The card is not considered research-complete until this workflow has run
- A card with `last_user_research_updated: null` in its front-matter is
  incomplete — treat it as a stub, not a source of truth

**On-demand — run to refresh:**
- When the user says "Research [company]" or similar
- When a company moves to `screening` or `interviewing` stage and the
  card has not been researched in the last 60 days
- When a major trigger event occurs (new CEO, funding round, product launch)

## Executed by
Claude Code

## Inputs
- data/manifest.yaml (to check if a card already exists)
- data/profile/me.md (for professional lens and fit assessment)
- Web search (company website, news, funding, Glassdoor, LinkedIn,
  careers page, earnings calls if public)

---

## Steps

### Step 0 — Note Role Context (do not block on this)

Check whether the specific role is known before starting research.
**Research runs regardless.** Role clarity sharpens the analysis — it does not gate it.

**Check the existing card (if any) and the current request:**
- Does the front-matter contain `role_targeted`?
- Is there a job description link or role title in the Open Roles section?
- Did the user mention the role in the current request?

**If role is known:** proceed to Step 1 with full role context in hand.
The Profile-Aware Analysis (Step 3) will be anchored to this specific role and team.

**If role is not yet known:**
Proceed to Step 1 anyway. Do not stop, do not ask, do not wait.
- Run the full company research (all steps below)
- In the Profile-Aware Analysis section, use the user's professional lens
  from `data/profile/me.md` to generate a general-purpose PM-lens analysis
  of the company — assess the most likely role surface areas, product teams
  they'd target, and fit signals, without pinning to a specific JD
- Add a note at the top of the Profile-Aware Analysis section:
  `_Role not yet confirmed. Analysis uses PM lens from profile. Update this section when role_targeted is set._`
- Set `role_targeted: null` in front-matter

**When role becomes known later:**
Re-run Step 3 only (Profile-Aware Analysis) and update the card.
The base research (Steps 2a–2g) does not need to be repeated unless the card
is older than 60 days.

---

### Step 1 — Check for existing card

Read data/manifest.yaml. Does a card already exist for this company?

**If yes:**
- Load the existing card
- Check `last_user_research_updated` in front-matter
- If null or older than 60 days: run full research (all steps below)
- If recent: ask "I have a card for [Company] last updated [date].
  Do you want a full refresh, or just an update on latest news and roles?"
- Proceed accordingly

**If no:** proceed to create a new card from scratch.

---

### Step 2 — Run structured web research

**Source citation is mandatory. No exceptions.**
Every factual claim written to the card must link to the source it came from.
Format: `Claim or fact. ([Source Name, date](url))`

If a claim cannot be traced to a retrievable source URL:
- Do not write it.
- Do not paraphrase it from memory or training data.
- State "not publicly disclosed" or "not found" instead.

This rule prevents hallucination and lets the user verify and read further.
It applies to every section: Business Overview, User Base & Geography, Recent News,
Funding & Growth, Culture & People, Open Roles, and Profile-Aware Analysis.

Run the following searches in order. Synthesize findings — do not
reproduce raw content verbatim.

**2a. Business model and product**
- What does the company do?
- What is their core product or service?
- Who are their customers (segment, size, industry)?
- What is their revenue model (SaaS, usage-based, marketplace, services)?
- What is their stated mission or company vision?

**2b. User base and geography** ← required at card creation
- Who are the primary consumer or end-user segments?
  Include: age range, income level, behavior patterns, technical
  sophistication, and any notable demographic signals
- Who are the primary business or merchant segments?
  Include: company size, industry, geography, technical profile
- Which user segments are growing vs declining?
- Where are users and revenue concentrated geographically?
  Include: US vs international split if available, top markets,
  growth markets, markets under pressure
- Any notable segment the company is visibly losing to competitors?
- Search for: "[company] user demographics", "[company] annual report
  geography", "[company] customer segments", "[company] statistics users"

**2c. Product × user segment mapping** ← required at card creation
- For each major product: which user uses it, in which geography,
  at what lifecycle stage (nascent / growing / mature / declining),
  and what is its stated strategic priority?
- Flag any product that is underperforming or under strategic pressure
- Flag any product where the user segment directly overlaps with the
  user's target domain (e.g. for a PM targeting IAM, flag the auth
  product and its user segment explicitly)
- Present as a table in the card:
  | Product | Primary User | Geography | Lifecycle Stage | Strategic Priority |

**2d. Recent news (last 90 days)**
- Press releases, blog posts, product announcements
- News coverage from industry and mainstream press
- Engineering blog or design blog posts
- Earnings call highlights if public company

**2e. Funding and growth**
- Total funding, most recent round, stage
- Lead investors
- Headcount signals (LinkedIn growth, job volume)
- Valuation signals if public
- Revenue or TPV figures if disclosed

**2f. Culture and people**
- Glassdoor: overall rating, top positives, top negatives
- Leadership team: CEO, CTO, CPO — backgrounds and public communications
- How do they talk about their team and values publicly?
- Engineering or design blog tone
- Any recent leadership changes worth flagging

**2g. Open roles relevant to the user's profile**
- Search the careers page for roles matching the user's target titles
- Note: title, team, seniority level, key requirements, date posted, link

---

### Step 3 — Generate profile-aware analysis

Using the research from Step 2 and the user's profile from data/profile/me.md:

- Identify the user's professional lens (PM / Engineer / Designer / Other)
- Generate the corresponding analysis section using the lens template
  from the card template
- The analysis must be specific to this user's background and target —
  not a generic company assessment

Lens-specific outputs:
- **PM:** Product Strategy Signals, Roadmap & Direction, PM Org Signals,
  Product Gaps, Fit Assessment
- **Engineer:** Tech Stack, Architecture Signals, Engineering Culture,
  Scale Challenges, Fit Assessment
- **Designer:** Design Maturity, What is Distinctive, Design Team Structure,
  Design Culture, Fit Assessment

---

### Step 4 — Present findings to the user

Present the populated card for review. Highlight:
- The 2–3 most interesting signals about this company
- The fit assessment conclusion
- Any open roles that are strong matches
- Anything that gives pause or suggests poor fit
- Any user segment or geographic signal directly relevant to a likely
  interview question

Ask: "Does this look right? Anything to add or correct before I finalize
the card?"

---

### Step 5 — Write the card

On user confirmation, write directly to the repo:

- Write the full card to `data/pipeline/[company-name].md`
- Set `last_user_research_updated` in front-matter to today's date
- Add or update the entry in `data/manifest.yaml`:

```yaml
  - id: data/pipeline/[company-name]
    type: company_pipeline
    stage: researching
    summary: "[One-line summary: product, stage, key signal]"
    priority: high
    tags: []
    updated: "[today's date]"
    next_action: "[First action to take]"
    has_temp: false
```

- Commit and push:

```bash
  git add data/pipeline/[company-name].md data/manifest.yaml
  git commit -m "research: data/pipeline/[company-name] initial sweep"
  git push
```

---

## Notes
- `last_user_research_updated: null` means the card is a stub.
  Never treat a stub as a reliable source for interview prep.
- Prioritize information from the last 90 days. Older signals are
  background context, not current state.
- **Every factual claim must have a source link.** No source = no claim.
  Write "not publicly disclosed" or "not found in search" rather than stating
  an unsourced fact. This is not a style preference — it is a correctness requirement.
- If Glassdoor or LinkedIn data is limited: say so explicitly.
  Do not fabricate signals.
- The fit assessment must be specific to this user — not generic
  praise of the company.
- If a company has `has_temp: true` in data/manifest.yaml, check the temp
  card before generating analysis — it may contain the most recent signals.
- User base and geography research (Steps 2b and 2c) is the foundation
  for product sense interview answers. It must be populated before any
  interview prep workflow runs for this company.
