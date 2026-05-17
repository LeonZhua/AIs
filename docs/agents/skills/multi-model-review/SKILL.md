---
name: multi-model-review
description: Use when a Cursor_Kit task needs independent plans, cross-model review, Codex adjudication, or human-gated execution decisions.
---

# Multi Model Review

## Overview

Use the Cursor_Kit protocol in `docs/agents/protocols/multi-model-review.md`. The skill drives the process; all facts and decisions are stored in task artifacts.

## Workflow

1. Check protocol and templates exist with `python3 tools/agent_context.py validate`.
2. Create or locate the task with `multi-review init`.
3. Generate plan prompts and tell the user where to paste external outputs.
4. After pasted plans, run `validate-task` and `check-quality`.
5. Generate review prompts and tell the user where to paste reviews.
6. Generate adjudication and human-decision artifacts.
7. Stop before execution until final plan and required human decisions are complete.
8. Verify, update task artifacts, update `docs/agents/WORKLOG.md`, then close or record rework.

## API-runner Workflow

1. Use `multi-review api-plan --task <task-id>` for dry-run planning.
2. Use `MULTI_REVIEW_API_CALLS=enabled ... api-plan --execute` only when the user explicitly wants real Qwen/DeepSeek API calls.
3. Add `--split-task` only when the user has explicitly declared the task should be split.
4. Use `multi-review api-accept --task <task-id>` after implementation evidence exists.
5. Use `MULTI_REVIEW_API_CALLS=enabled ... api-accept --execute` only when the user explicitly wants real acceptance API calls.
6. Treat missing Qwen/DeepSeek, sensitive input hits, parse failures, P0/P1, and static high-risk matches as blockers.

## Hard Gates

- Do not store API keys.
- Do not execute before `final-plan` exists.
- Do not execute with unresolved P0/P1 or required human decisions.
- Do not assign external execution unless file/module boundaries are explicit.
- Do not call external APIs unless `MULTI_REVIEW_API_CALLS=enabled` and `--execute` are both present.
- Do not externalize sensitive input; if sanitization hits, stop and ask for human handling.
