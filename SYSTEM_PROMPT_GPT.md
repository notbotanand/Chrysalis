# Chrysalis — System Prompt for ChatGPT Custom GPT

## Status: Phase 2 — Not Yet Implemented

This file is a placeholder for a future ChatGPT custom GPT variant of Chrysalis.

The Claude Project system prompt (SYSTEM_PROMPT.md) is the current
working implementation. Use that for now.

---

## What Will Go Here (Phase 2)

A ChatGPT-compatible system prompt and custom GPT configuration that
implements the same Chrysalis behavior for users who prefer ChatGPT.

Key differences from the Claude version will need to be addressed:
- GitHub connector (Claude native) → GitHub API via custom action
- Gmail connector (Claude native) → Gmail API via custom action
- Google Calendar connector (Claude native) → Google Calendar API via custom action
- Temp card write-back model → same (CoWork handles this independently)

The workflow files in framework/workflows/ are AI-platform-agnostic and will
work without modification.

---

## Contributing

If you have implemented a working ChatGPT variant, please open a pull
request with:
1. The custom GPT system prompt
2. Any custom action schemas (OpenAPI format)
3. Notes on what differs from the Claude version

See README.md for contributing guidelines.
