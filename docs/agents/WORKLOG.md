# Worklog

> 按时间倒序记录 Codex 和按需派生 rules 的工作回合。每条记录只写事实：做了什么、关键文件、验证、下一步。
> 如日志明显膨胀，先归档到 `docs/agents/archive/`，再把本文件恢复为轻量入口。

## 2026-05-16 Codex

- 输入：开启“直接调用 API 接口的多 AI 评审方案”任务，使用 full 模式，先生成 Codex、DeepSeek、Qwen 三方方案 prompt，不执行。
- 关键文件：
  - `docs/agents/tasks/2026-05-16-2201-直接调用-API-接口的多-AI-评审方案/task.md`
  - `docs/agents/protocols/multi-model-review.md`
  - `tools/agent_context.py`
  - `docs/agents/PROJECT_STATE.md`
- 新增计划文档：
  - `docs/agents/tasks/2026-05-16-2201-直接调用-API-接口的多-AI-评审方案/api-version-plan.md`
- 当前状态：已创建 full 模式 prompt-only 任务；补充 Qwen 为支持的 prompt-only 模型键；已生成 `codex`、`deepseek`、`qwen` 三方 plan prompts；已创建 plan/review 接收文档；已读取 Qwen/DeepSeek 方案并生成 Codex 集成方案；已生成交叉评审 prompts；未调用任何外部模型或 API。
- 补充：已创建 `.env.local` 与 `.env.example` 占位文件，供用户本地填写 DeepSeek 与 Qwen/DashScope API Key；未写入真实密钥，且后续不应读取 `.env.local` 内容到对话或日志。
- API 版本计划：已按用户要求直接调用 Qwen `qwen3.6-plus` 和 DeepSeek `deepseek-v4-pro`，基于两方 API 输出和 Codex 裁决生成 `api-version-plan.md`；文档包含 API-runner 计划、Mermaid 流程图、接口、错误处理、安全边界、成本审计和验收标准。
- Codex 第一轮产出：补充 `codex-first-output.md`，明确 API-runner 的第一步是 Codex 生成本地种子包，而不是使用历史 `plans/codex.md` 集成方案。
- 完整评审流程：按用户澄清的“手动调用 API”含义，真实调用 Qwen/DeepSeek API 生成 `reviews/qwen-review.md` 和 `reviews/deepseek-review.md`，再由 Codex 写入 `adjudication.md`、`human-decisions.md`、`final-plan.md`、`verification.md`；当前任务状态为 `verified`。
- 用户决策：不设置每任务 token/cost 硬上限；实现只记录 token/cost，不因预算阈值阻断调用。
- 方案补充：新增独立多 AI 验收阶段，命令建议为 `multi-review api-accept`，由 Codex 汇总本地证据，Qwen 验收工程符合度，DeepSeek 验收安全边界和失败路径。
- 方案补充：新增任务拆分门禁；大任务必须先生成 `task-breakdown`，拆成可独立评审、实现和验收的子任务，再分别走 API 评审和 API 验收。
- 多轮评审收敛：真实调用 Qwen/DeepSeek 完成两轮评审，输出保存到 `api/multi-round-review/qwen-round1.md`、`deepseek-round1.md`、`qwen-round2.md`、`deepseek-round2.md`；Codex 合成 `api/multi-round-review/final-scheme.md` 和 `human-confirmation-checklist.md`。
- 用户决策：确认人工门禁处理方式，敏感输入禁止外发；任务仅在人工声明后拆分；Qwen/DeepSeek 不可用时等待；解析失败不合成可执行计划；其余采用默认处理。
- 实现：扩展 `tools/agent_context.py`，新增 `multi-review api-plan` 与 `multi-review api-accept`；实现 seed package、输入脱敏、人工拆分声明、dry-run、双重开关、Qwen/DeepSeek API 调用、Codex 裁决、calls log、artifact chain 和多 AI 验收报告。
- 验证：`python3 tools/agent_context.py multi-review api-plan --task 2026-05-16-2201-直接调用-API-接口的多-AI-评审方案` 输出 dry-run artifact；`python3 tools/agent_context.py validate` 通过；`python3 -m unittest tests/test_agent_context.py` 通过 19 项测试。未发起真实外部 API 调用。
- 验证：执行了 `python3 tools/agent_context.py multi-review plan-prompts --task 2026-05-16-2201-直接调用-API-接口的多-AI-评审方案 --models codex,deepseek,qwen` 和 `python3 tools/agent_context.py multi-review review-prompts --task 2026-05-16-2201-直接调用-API-接口的多-AI-评审方案`，结果为生成 plan/review prompts；未运行测试，因用户明确要求不要执行。
- 下一步：如进入实现阶段，按 `final-plan.md` 实现 API-runner 最小闭环；prompt-only review 保留为 fallback。

## 2026-05-16 Codex

- 输入：在 `/Library/Developer/AIs-test` 中部署 Cursor_Kit 多 AI 评审方案。
- 关键文件：
  - `AGENTS.md`
  - `README.md`
  - `docs/agents/`
  - `tools/agent_context.py`
  - `tests/test_agent_context.py`
  - `.cursor-kit-version`
- 当前状态：已从 `/Library/Developer/Cursor_Kit` 同步 v2.2.0 模板，包含 `multi-review` 协议、模板、项目随附 Skill 和本地 CLI；目标目录不是 git 仓库。
- 验证：
  - `python3 -m unittest tests/test_agent_context.py`
  - `python3 tools/agent_context.py validate`
  - `python3 tools/agent_context.py status`
- 下一步：使用 `multi-review init` 创建第一个 prompt-only 多 AI 评审任务。
