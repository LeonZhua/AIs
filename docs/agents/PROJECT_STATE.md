# Project State

> 本文件是 Codex 主模板的项目状态入口（轻量入口）。只记录恢复上下文所需的事实，不写长篇过程。

## Current Focus

- 名称：AIs-test 多 AI 评审试验项目
- 成功判断：本项目已部署 Cursor_Kit v2.2.0；根目录保留 Codex 主动入口；多 AI 评审作为 prompt-only 高级流程由 `docs/agents/protocols/`、`templates/`、`skills/` 和 `multi-review` 命令承载。
- 最近更新：2026-05-16

## Main Task

- 任务名称：直接调用 API 接口的多 AI 评审方案
- 任务文件：`docs/agents/tasks/2026-05-16-2201-直接调用-API-接口的多-AI-评审方案/task.md`
- 状态：已实现并验证 API-runner 多 AI 评审与验收入口，包含 dry-run、双重开关、输入脱敏、人工拆分声明、Qwen/DeepSeek API 调用、Codex 裁决和 API 验收。
- 下一步：如需验证，运行 `python3 tools/agent_context.py multi-review api-plan --task <task-id>` 做 dry-run；真实调用需 `MULTI_REVIEW_API_CALLS=enabled` 和 `--execute`。

## Active Tasks

- `2026-05-16-2201-直接调用-API-接口的多-AI-评审方案`：API 版本多 AI 评审方案；当前状态 `verified`，实现入口为 `multi-review api-plan` 和 `multi-review api-accept`。

## Recent Handoff

- 2026-05-16 Codex：从 `/Library/Developer/Cursor_Kit` 同步 v2.2.0 到 `/Library/Developer/AIs-test`，排除 `.git`、本地设置和缓存文件。
- 2026-05-16 Codex：AIs-test 当前不是 git 仓库；如需要版本管理，后续可在本目录单独 `git init`。
