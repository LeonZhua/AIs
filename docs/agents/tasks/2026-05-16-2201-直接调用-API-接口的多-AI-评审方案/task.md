# 多 AI 评审任务：直接调用 API 接口的多 AI 评审方案

## Metadata

- 任务 ID：2026-05-16-2201-直接调用-API-接口的多-AI-评审方案
- 模式：full
- 状态：verified
- 创建时间：2026-05-16 22:01

## Request

开启一个 `full` 模式的多 AI 评审任务，目标是产出“直接调用 API 接口的多 AI 评审方案”。

本轮只生成三方独立方案 prompt，模型先使用 Codex、DeepSeek、Qwen；不得执行外部模型调用，不得调用真实 API，不得写入或要求 API Key。

## Context Summary

- 项目当前已部署 Cursor_Kit v2.2.0，多 AI 评审 v1 是 prompt-only 流程。
- 现有协议位于 `docs/agents/protocols/multi-model-review.md`，模板位于 `docs/agents/templates/`，CLI 位于 `tools/agent_context.py`。
- v1 的安全边界是不自动调用外部 API、不保存密钥、不自动执行外部分派。
- 本任务要求评审对象是“未来如何设计直接调用 API 的多 AI 评审方案”，当前步骤只产出隔离的三方 plan prompts。

## Operation Manual

1. 运行 `multi-review plan-prompts --task 2026-05-16-2201-直接调用-API-接口的多-AI-评审方案`。
2. 将 `prompts/plans/*.md` 分别粘贴到外部模型。
3. 将模型输出保存到 `plans/<model>.md`。
4. 运行 `multi-review review-prompts --task 2026-05-16-2201-直接调用-API-接口的多-AI-评审方案`。
5. 将 `prompts/reviews/*.md` 分别粘贴到外部模型。
6. 将评审输出保存到 `reviews/<model>-review.md`。
7. 运行 `validate-task` 和 `check-quality`。
8. 填写 `adjudication.md`、`human-decisions.md`、`final-plan.md`、`verification.md`。

## Handoff

- 当前状态：verified
- 下一步：可使用 `multi-review api-plan` 和 `multi-review api-accept` 运行 API-runner dry-run；真实调用需显式双重开关。
