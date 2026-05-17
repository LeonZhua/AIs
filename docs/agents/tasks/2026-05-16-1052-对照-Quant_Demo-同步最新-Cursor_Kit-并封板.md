# 任务记录：对照 Quant_Demo 同步最新 Cursor_Kit 并封板

## Metadata

- 任务 ID：2026-05-16-1052-对照-Quant_Demo-同步最新-Cursor_Kit-并封板
- 负责 Agent：codex
- 最近接手 Agent：codex
- 状态：进行中
- 创建时间：2026-05-16 10:52
- 最近更新：2026-05-16 10:52
- 关联状态：`docs/agents/PROJECT_STATE.md`
- 关联工作日志：`docs/agents/WORKLOG.md`

## Request

```text
检查 Quant_Demo 里的项目结构和本地文件，输出现在最新版本的 codex-kit 内容并封板。
```

## Goal

基于 Quant_Demo 当前已落地的纯 Codex 模板用法，回流通用结构到 Cursor_Kit，完成验证并封板当前版本。

## Acceptance Criteria

- [x] 已核对 Quant_Demo 当前本地结构、共享文档和 `tools/agent_context.py`，区分出可回流模板的通用部分与业务特有部分。
- [x] Cursor_Kit 模板显式包含 `docs/agents/archive/` 说明文件，并在 README/共享文档中写清轻量入口与归档约定。
- [x] 相关测试与模板校验通过，可作为本轮封板依据。

## Decisions

- `tools/agent_context.py` 与测试主能力以 Cursor_Kit 当前工作树为准；Quant_Demo 本地同名脚本已验证无通用逻辑差异，不重复回流业务特化内容。
- 只回流 `docs/agents/archive/`、轻量入口维护和封板前文档同步这类通用约定；不把 Quant_Demo 的策略研究、发布链路、交易安全规则带进模板。
- 本轮版本号从 `2.0.0` 提升到 `2.1.0`，用于标记 archive 结构正式进入模板。

## Session Notes

### 2026-05-16 10:52 - codex

- 做了什么：
  - 读取 `Cursor_Kit` 当前 `docs/agents`、工作树 diff 和既有任务记录，确认当前未提交内容是“纯 Codex 主模板 + export-rules”版本。
  - 对照 `Quant_Demo` 的本地结构、`AGENTS.md`、`docs/agents`、`tests/test_agent_context.py` 与 `tools/agent_context.py`，确认脚本实现已一致，主要缺口在 archive 结构和轻量入口说明未模板化。
  - 先按 TDD 为 archive 说明文件补测试契约，确认失败后新增 `docs/agents/archive/README.md`，并同步更新模板文档、校验脚本和版本号。
- 关键文件：
  - `docs/agents/archive/README.md`
  - `README.md`
  - `docs/agents/README.md`
  - `docs/agents/PROJECT_STATE.md`
  - `docs/agents/WORKLOG.md`
  - `docs/agents/LESSONS.md`
  - `tests/test_agent_context.py`
  - `tools/agent_context.py`
  - `.cursor-kit-version`
- 验证：
  - 红灯：`python3 -m unittest tests.test_agent_context.AgentContextToolTest.test_validate_accepts_root_template tests.test_agent_context.RootTemplateInvariantTest.test_archive_docs_exist_for_lightweight_context_maintenance`
  - 绿灯：`python3 -m unittest tests.test_agent_context.AgentContextToolTest.test_validate_accepts_root_template tests.test_agent_context.RootTemplateInvariantTest.test_archive_docs_exist_for_lightweight_context_maintenance`
  - 全量：`python3 -m unittest tests/test_agent_context.py`
  - 全量：`python3 tools/agent_context.py validate`
  - 全量：`python3 tools/agent_context.py status`
- 下一步：
  - 无；本轮已达到封板条件。

## Handoff

- 给下一个 Agent 先看：
  - `docs/agents/tasks/2026-05-16-1052-对照-Quant_Demo-同步最新-Cursor_Kit-并封板.md`
  - `docs/agents/archive/README.md`
  - `tools/agent_context.py`
- 当前风险：
  - Quant_Demo 里还有大量业务特有的 `docs/agents` 经验和发布细节，本轮未引入；后续若再做模板抽象，仍需逐条区分“通用机制”与“业务规则”。
- 建议下一步：
  - 运行 `python3 -m unittest tests/test_agent_context.py`、`python3 tools/agent_context.py validate`、`python3 tools/agent_context.py status` 后执行封板提交。
