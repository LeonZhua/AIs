# Codex 主模板上下文机制

Cursor_Kit 是一个纯 Codex 主模板。Codex 通过根目录 `AGENTS.md` 工作，`docs/agents/` 只保存恢复上下文所需的项目状态、任务记录、长期经验和交接日志。

Claude Code / Trae rules 是按需生成的兼容入口，不是根模板默认文件。生成后的 rules 也读取同一组 `docs/agents/` 文档。

## 工作方式

1. 开始复杂任务前，先读 `PROJECT_STATE.md`、`WORKLOG.md`、`LESSONS.md`。
2. 修改代码或文档前，确认是否已有任务记录；没有则从 `tasks/TEMPLATE-task.md` 创建。
3. 工作过程中把关键决策和执行结果写入任务记录。
4. 每轮结束前更新 `WORKLOG.md`，说明做了什么、验证结果和下一步。
5. 只有稳定、长期适用的经验才写入 `LESSONS.md`。

## 文件职责

| 文件 | 职责 |
|------|------|
| `PROJECT_STATE.md` | 当前阶段目标、主线任务、活跃任务、最近交接 |
| `WORKLOG.md` | Codex 和按需派生 rules 的回合记录 |
| `LESSONS.md` | 长期适用的项目经验 |
| `archive/` | `PROJECT_STATE.md` / `WORKLOG.md` 的历史快照与归档说明 |
| `protocols/` | 可选高级协作协议，例如多 AI 计划评审 |
| `templates/` | 可实例化的任务、方案、评审、裁决和验证模板 |
| `skills/` | 项目随附的 Codex Skill 使用说明 |
| `tasks/` | 每个独立任务的过程记录 |

## 轻量入口与归档

- `PROJECT_STATE.md` 应保持轻量入口，只放恢复当前上下文必须的事实。
- `WORKLOG.md` 允许保留当前工作回合，但不应长期堆积完整历史正文。
- 当入口文件明显膨胀时，优先将旧内容归档到 `docs/agents/archive/`，再把入口重写回轻量形态。

## 本地辅助命令

```bash
python3 tools/agent_context.py status
python3 tools/agent_context.py validate
python3 tools/agent_context.py new-task --title "任务标题"
python3 tools/agent_context.py multi-review init --title "多 AI 任务" --mode light
python3 tools/agent_context.py export-rules --agent all --target-root /path/to/project
```

这些命令只维护上下文文件或生成兼容 rules，不启动或调用任何 AI 工具。

`multi-review` 是 prompt-only 的高级评审流程。v1 只生成任务 artifact 和外部模型 prompt；DeepSeek、GLM、Kimi 等模型输出需要人工粘贴回任务文件，Codex 再负责裁决、人工门禁、最终计划、验证和 `WORKLOG.md` 更新。
