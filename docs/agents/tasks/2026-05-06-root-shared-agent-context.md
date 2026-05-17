# 任务记录：根模板三工具共享上下文改造

## Metadata

- 任务 ID：2026-05-06-root-shared-agent-context
- 负责 Agent：Codex
- 最近接手 Agent：Codex
- 状态：已完成
- 创建时间：2026-05-06
- 最近更新：2026-05-06
- 关联状态：`docs/agents/PROJECT_STATE.md`
- 关联工作日志：`docs/agents/WORKLOG.md`

## Request

```text
把 Cursor_Kit 根目录改造成唯一主模板，用于在同一个项目中切换 Trae、Claude Code、Codex 工作。删除旧 codex-kit / claude-kit，新增共享状态文档、三工具入口和轻脚本。
```

## Goal

交付一个根级三工具共享上下文模板，让 Trae、Claude Code、Codex 都通过 `docs/agents/` 了解彼此做过什么。

## Acceptance Criteria

- [x] 根目录存在 `AGENTS.md`、`CLAUDE.md`、`.trae/project_rules.md`。
- [x] 根目录存在 `docs/agents/PROJECT_STATE.md`、`WORKLOG.md`、`LESSONS.md` 和任务模板。
- [x] `tools/agent_context.py status/validate/new-task` 可运行。
- [x] 旧 `codex-kit/`、`claude-kit/` 和混合工作流实验文档已移除。
- [x] 根级测试通过。

## Decisions

- 不保留 `legacy/` 或 `kits/`；旧单工具版本通过 Git 历史追溯。
- 不做 MCP、本地服务或自动化同步。
- Trae 项目入口采用 `.trae/project_rules.md`。

## Session Notes

### 2026-05-06 - Codex

- 做了什么：先写根级测试并确认失败，再开始新增三工具入口和共享文档。
- 关键文件：`tests/test_agent_context.py`、`docs/agents/`。
- 验证：先运行 `python3 -m unittest tests/test_agent_context.py` 确认红灯；实现后重新运行并通过。另运行 `python3 tools/agent_context.py validate` 和 `python3 tools/agent_context.py status`。
- 下一步：如继续迭代模板，先运行 `python3 tools/agent_context.py status`。

## Handoff

- 给下一个 Agent 先看：`docs/agents/PROJECT_STATE.md` 和 `docs/agents/WORKLOG.md`。
- 当前风险：README、入口规则和脚本输出需要保持一致，避免三处描述漂移。
- 建议下一步：修改前创建或复用任务记录，完成前运行根级验证。
