# 多 AI 评审任务：{{TITLE}}

## Metadata

- 任务 ID：{{TASK_ID}}
- 模式：{{MODE}}
- 状态：draft
- 创建时间：{{CREATED_AT}}

## Request

{{REQUEST}}

## Context Summary

{{CONTEXT_SUMMARY}}

## Model Prompts

{{MODEL_PROMPTS}}

## Model Plans

{{MODEL_PLANS}}

## Cross Review Prompts

{{CROSS_REVIEW_PROMPTS}}

## Cross Reviews

{{CROSS_REVIEWS}}

## Adjudication

| 建议 | 来源 | 严重级别 | 决策 | 理由 | 证据 | 是否涉及 Codex 自身方案 | 是否需人工 |
|---|---|---|---|---|---|---|---|
| {{SUGGESTION_ID}} | {{SOURCE}} | {{SEVERITY}} | {{DECISION}} | {{REASON}} | {{EVIDENCE}} | {{CODEX_BIAS}} | {{HUMAN_REQUIRED}} |

## Human Decisions

| ID | Trigger | Decision Needed | Options | Decision | Decided By | Reason | Timestamp |
|---|---|---|---|---|---|---|---|
| {{DECISION_ID}} | {{TRIGGER}} | {{DECISION_NEEDED}} | {{OPTIONS}} | {{DECISION}} | {{DECIDED_BY}} | {{REASON}} | {{TIMESTAMP}} |

## Final Plan

{{FINAL_PLAN}}

## Verification

### Verification Plan

- Commands: {{VERIFY_COMMANDS}}
- Expected Results: {{EXPECTED_RESULTS}}
- Risk Areas: {{RISK_AREAS}}

### Verification Results

| Command | Expected | Actual | Status | Verified By |
|---|---|---|---|---|
| {{COMMAND}} | {{EXPECTED}} | {{ACTUAL}} | {{STATUS}} | {{VERIFIED_BY}} |

### Failure Handling

- Failure Summary: {{FAILURE_SUMMARY}}
- Root Cause: {{ROOT_CAUSE}}
- Rework Target: {{REWORK_TARGET}}
- Next State: {{NEXT_STATE}}

### Final Status

- Result: pending
- Remaining Risks: {{REMAINING_RISKS}}
- Close Ready: no

## State Log

| Time | From | To | Actor | Summary |
|---|---|---|---|---|
| {{CREATED_AT}} | - | draft | codex | 创建多 AI 评审任务。 |

## Handoff

- 当前状态：draft
- 下一步：运行 `multi-review plan-prompts` 并粘贴外部模型输出。
