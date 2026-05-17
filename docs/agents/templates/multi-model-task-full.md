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

## Operation Manual

1. 运行 `multi-review plan-prompts --task {{TASK_ID}}`。
2. 将 `prompts/plans/*.md` 分别粘贴到外部模型。
3. 将模型输出保存到 `plans/<model>.md`。
4. 运行 `multi-review review-prompts --task {{TASK_ID}}`。
5. 将 `prompts/reviews/*.md` 分别粘贴到外部模型。
6. 将评审输出保存到 `reviews/<model>-review.md`。
7. 运行 `validate-task` 和 `check-quality`。
8. 填写 `adjudication.md`、`human-decisions.md`、`final-plan.md`、`verification.md`。

## Handoff

- 当前状态：draft
- 下一步：生成 plan prompts。
