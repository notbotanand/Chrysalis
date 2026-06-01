# Chrysalis Examples — Read-Only Reference

This directory contains **fully populated reference files** showing what a
working Chrysalis setup looks like. Everything in here is fictional —
the persona, the companies, the recruiters, the dates.

## What you'll find

| Path | What it demonstrates |
|---|---|
| `profile/me.md` | A complete profile after onboarding — what every section should contain |
| `pipeline/acme-payments.md` | A fully-researched, interview-active company card |
| `pipeline/globex-wallet.md` | An earlier-stage card at the recruiter-screen stage |
| `config/accounts.yaml` | The shape of a configured accounts file |
| `manifest.yaml` | What `data/manifest.yaml` looks like populated |

## Important — do not edit these files

These files are **not loaded** by any workflow. They're documentation
in file form. Editing them won't change anything in your Chrysalis,
and any changes will be overwritten by framework updates.

**To populate your real Chrysalis:** run `Onboard me` in Claude Code.
Your data lives under `data/`, not here. See the main `README.md`
in the repo root.

## Why fictional?

The framework ships publicly. If `examples/` held real data,
every clone would carry someone else's career history. The fictional
persona is detailed enough to be useful as a reference and clearly
fictional enough that no one mistakes it for their own profile.

If you find anything in here that looks like a real person or company,
that's coincidence — these are composite illustrations.
