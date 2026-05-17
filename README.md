# Cursor_Kit

Cursor_Kit 是一个纯 Codex 主模板。根目录只保留 Codex 主动入口 `AGENTS.md`，项目状态、任务记录、经验沉淀和交接日志统一放在 `docs/agents/`。

Claude Code / Trae 不是根模板的默认入口；需要时可以通过 `export-rules` 按同一套任务记录逻辑生成兼容 rules 到目标项目。

## 快速开始

1. 把本仓库作为项目模板复制到新项目。
2. 让 Codex 读取根目录 `AGENTS.md`。
3. 开始复杂任务前查看 Codex 上下文：

```bash
python3 tools/agent_context.py status
```

4. 修改代码或文档前，确认是否已有任务记录；没有则创建：

```bash
python3 tools/agent_context.py new-task --title "任务标题"
```

5. 每轮结束前更新任务记录和 `docs/agents/WORKLOG.md`。
6. 如目标项目确实要让 Claude Code 或 Trae 接手，按需生成兼容 rules：

```bash
python3 tools/agent_context.py export-rules --agent claude --target-root /path/to/project
python3 tools/agent_context.py export-rules --agent trae --target-root /path/to/project
```

## 目录结构

```text
.
├── AGENTS.md
├── docs/agents/
│   ├── README.md
│   ├── archive/
│   │   └── README.md
│   ├── PROJECT_STATE.md
│   ├── WORKLOG.md
│   ├── LESSONS.md
│   ├── protocols/
│   │   └── multi-model-review.md
│   ├── templates/
│   │   └── multi-model-task-light.md
│   ├── skills/
│   │   └── multi-model-review/
│   │       └── SKILL.md
│   └── tasks/
│       └── TEMPLATE-task.md
├── tools/
│   └── agent_context.py
├── tests/
│   └── test_agent_context.py
└── .cursor-kit-version
```

## 共享上下文

- `docs/agents/PROJECT_STATE.md`：当前阶段目标、主线任务、活跃任务、最近交接。
- `docs/agents/WORKLOG.md`：按时间倒序记录 Codex 和按需派生 rules 的工作回合。
- `docs/agents/LESSONS.md`：长期适用的项目经验。
- `docs/agents/archive/`：`PROJECT_STATE.md` / `WORKLOG.md` 的历史快照与归档说明。
- `docs/agents/protocols/`：可选高级协作协议，例如多 AI 计划评审。
- `docs/agents/templates/`：可实例化的任务、方案、评审、裁决和验证模板。
- `docs/agents/skills/`：项目随附的 Codex Skill 说明，不是全局安装目录。
- `docs/agents/tasks/`：每个独立任务的过程记录。

## 本地工具

```bash
python3 tools/agent_context.py status
python3 tools/agent_context.py validate
python3 tools/agent_context.py new-task --title "示例任务"
python3 tools/agent_context.py multi-review init --title "示例多 AI 任务" --mode light
python3 tools/agent_context.py export-rules --agent all --target-root /path/to/project
```

`status` 用于快速恢复上下文，`validate` 用于检查纯 Codex 模板完整性，`new-task` 用于创建任务记录，`export-rules` 用于按需生成 Claude Code / Trae 兼容 rules。

`multi-review` 是可选高级流程：v1 只生成 prompt 和 artifact，不自动调用外部 API，也不保存任何密钥。用户需要把外部模型输出手动粘贴回任务文件，再由 Codex 进行裁决、验证和日志更新。

常用流程：

```bash
python3 tools/agent_context.py multi-review init --title "复杂任务" --mode full
python3 tools/agent_context.py multi-review plan-prompts --task <task-id>
python3 tools/agent_context.py multi-review review-prompts --task <task-id>
python3 tools/agent_context.py multi-review adjudication --task <task-id>
python3 tools/agent_context.py multi-review validate-task --task <task-id>
python3 tools/agent_context.py multi-review check-quality --task <task-id>
python3 tools/agent_context.py multi-review status --task <task-id>
```

生成目标已存在时默认拒绝覆盖；确实需要替换时显式传入 `--force`：

```bash
python3 tools/agent_context.py export-rules --agent all --target-root /path/to/project --force
```

## 验证

```bash
python3 -m unittest tests/test_agent_context.py
python3 tools/agent_context.py validate
```

## 版本

- 当前版本：`v2.2.0`（见 `.cursor-kit-version`）
