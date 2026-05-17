# 本仓库约定（Codex）

Codex 会自动注入本文件。本项目是纯 Codex 主模板：根目录只保留 `AGENTS.md` 作为主动入口，通过 `docs/agents/` 维护项目状态、任务记录、经验沉淀和交接日志。

Claude Code / Trae rules 不在根目录长期保留；需要时通过 `python3 tools/agent_context.py export-rules` 按同一套任务记录逻辑生成到目标项目。

## 硬约束

- 沟通与注释优先用中文；发现概念混用、验收口径模糊或表述不严谨时，直接指出并给出准确表述。
- 禁止在对话、代码、文档、日志或测试输出中暴露 API Key、令牌及任何密钥；一律用占位符代替。
- 不回滚、覆盖或删除用户未授权的现有改动。
- 修改代码或文档前，确认当前任务是否已有任务记录；没有则创建。
- 每轮结束前更新任务记录和 `docs/agents/WORKLOG.md`，写清变更、验证和下一步。
- 完成前运行最相关验证；无法验证时说明原因与剩余风险。

## 任务入口

复杂任务开始前按顺序读取：

1. `docs/agents/PROJECT_STATE.md`
2. `docs/agents/WORKLOG.md`
3. `docs/agents/LESSONS.md`

轻量问答、概念解释、纯讨论不强制创建任务记录。

## 文档路由

- `docs/agents/PROJECT_STATE.md`：当前阶段目标、主线任务、活跃任务、最近交接。
- `docs/agents/WORKLOG.md`：按时间倒序记录 Codex 和按需派生 rules 的工作回合。
- `docs/agents/LESSONS.md`：长期适用的项目经验。
- `docs/agents/tasks/`：任务级记录。
- `docs/agents/README.md`：共享上下文机制说明。

## Codex 机制注意事项

- 不要把项目规则重复写入 Codex 全局 User Rules；项目规则以本文件和 `docs/agents/` 为准。
- 不要在根目录手写或长期保留 `CLAUDE.md`、`.trae/project_rules.md`；如需兼容入口，用 `export-rules` 生成到目标项目。
- 长任务可能发生上下文压缩，恢复事实必须写入共享文档，而不是只留在对话中。
