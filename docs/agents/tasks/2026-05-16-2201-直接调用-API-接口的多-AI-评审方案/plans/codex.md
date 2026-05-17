# Codex Plan

## 目标理解

本任务不是现在直接调用外部 API，而是为 Cursor_Kit 多 AI 评审流程设计下一版“可直接调用 API 的多模型评审方案”。当前 v1 是 prompt-only：生成 prompt、人工粘贴外部模型输出、再由 Codex 裁决。目标 v2 应在不暴露密钥、不破坏人工确认门禁的前提下，把外部模型调用从人工粘贴升级为受控的 API 编排。

说明：本方案由 Codex 在当前会话中生成；由于本轮已读取 Qwen 和 DeepSeek 方案，本文定位为 Codex 集成方案，不标记为严格隔离的独立方案。

## 关键约束

- 不得在仓库、日志、对话、artifact 中保存 API Key 或访问令牌；密钥只能来自环境变量或系统密钥管理。
- API 调用能力必须默认关闭，不能改变 v1 prompt-only 的安全默认值。
- 所有真实外部调用必须支持 dry-run、成本预估、超时、重试上限和失败可恢复。
- Codex 内置方案可以直接生成 `plans/codex.md`，不需要走“生成 prompt 再人工粘贴”的外部模型路径。
- Qwen 更适合作为 API 编排和结构化输出方案补强模型；DeepSeek 更适合作为反方审查模型，重点查风险、成本和过度设计。
- P0/P1、密钥处理、资金/生产/安全相关调用、执行分派必须保留人工确认门禁。
- API 方案应兼容多供应商，但 v2 不应一次性追求完整平台化；先实现最小可用闭环。

## 推荐方案

采用“分层执行器 + 模型适配器 + artifact 驱动状态机”的 v2 方案。

第一层是任务 artifact 层，继续沿用 `docs/agents/tasks/<task-id>/`，保留 `prompts/`、`plans/`、`reviews/`、`adjudication.md`、`human-decisions.md`、`verification.md`。这样 v1 和 v2 能共享同一套交接机制。

第二层是模型适配器层，为 `codex`、`qwen`、`deepseek` 等模型定义统一接口：输入 prompt、模型配置、超时、最大 token、温度、输出路径；输出必须是 markdown artifact，不允许只存在内存或控制台。

第三层是调用执行器层，负责 dry-run、真实调用、错误分类、成本记录、速率限制和重试策略。真实调用仅在用户显式启用后执行，例如 `--execute` 或配置项 `api_calls: enabled`，默认只生成 prompt。

第四层是裁决层，由 Codex 汇总三方结果。裁决不做多数决，而是按证据、风险等级和人工确认要求处理。Qwen 的方案偏 API/结构化设计，DeepSeek 的方案偏反方风险，Codex 负责落地到本仓库协议和任务文件。

## 执行步骤

1. 保留 v1 prompt-only 命令语义。
   - `multi-review plan-prompts` 继续只生成 prompt。
   - 不改变默认安全边界。

2. 增加 v2 API 调用配置文件。
   - 建议路径：`docs/agents/config/model-providers.example.md` 或后续 `model-providers.example.json`。
   - 只记录 provider、base_url、model、timeout、max_tokens、rate_limit 等非密钥信息。
   - 密钥字段只允许写环境变量名，例如 `OPENAI_API_KEY`、`DASHSCOPE_API_KEY`、`DEEPSEEK_API_KEY`，不能写实际值。

3. 增加模型适配器抽象。
   - 统一输入：`task_id`、`phase`、`model_key`、`prompt_path`、`output_path`。
   - 统一输出：markdown 文件、调用元数据、错误状态。
   - Codex 适配器可以是 local/direct writer，不需要 API 调用。

4. 增加 dry-run 优先的执行命令。
   - 示例：`multi-review run-plans --task <id> --models qwen,deepseek --dry-run`。
   - dry-run 只展示将调用哪些模型、读取哪些 prompt、写入哪些文件、预计最大 token，不发起网络请求。
   - 真实调用必须显式加 `--execute`，且命令输出不能打印密钥。

5. 增加调用记录和成本记录。
   - 建议生成 `api-calls.md` 或 `cost-log.md`。
   - 记录时间、provider、model、phase、输入 prompt 路径、输出 artifact、token 用量、估算成本、状态。
   - 记录失败原因时只写错误类别和供应商返回摘要，不写敏感 header 或 request body。

6. 增加失败恢复策略。
   - 网络错误、429、5xx 可有限重试。
   - 4xx 参数错误不自动重试，应标记为配置错误。
   - 超时、半写入、空输出必须保留 `.partial` 或错误 artifact，方便恢复。

7. 调整默认三方角色。
   - `codex`：直接生成仓库集成方案和最终裁决。
   - `qwen`：API 编排、结构化输出、中文工程完整性。
   - `deepseek`：反方审查、成本、边界条件、失败模式。

8. 保留人工确认门禁。
   - API 调用能力上线前必须确认密钥来源、日志脱敏、成本上限、允许调用的 provider/model。
   - 涉及生产、资金、安全、隐私数据的任务默认不允许自动执行外部调用。

## 验收标准

- v1 prompt-only 流程不受破坏；不配置 API 时，所有命令仍只生成 artifact，不联网。
- Codex 可以直接生成 `plans/codex.md`，不要求用户手动粘贴 Codex prompt。
- Qwen 和 DeepSeek 的模型角色在协议或任务模板中有明确分工。
- API 调用配置不包含任何真实密钥，只包含环境变量名或占位符。
- dry-run 能展示调用计划、输入输出路径、模型列表和风险提示。
- 真实调用必须由显式参数触发，且失败时不会污染已有 plan/review 文件。
- 每次真实调用都有成本和状态记录，便于审计。
- P0/P1 和人工确认项不会被 API 自动化绕过。

## 风险与边界

- 如果过早实现多供应商完整抽象，容易把简单流程做成平台工程；v2 应先支持最小闭环。
- 如果真实调用默认开启，会破坏当前项目的安全边界；必须默认关闭。
- 如果日志记录 request body，可能泄露用户数据或密钥；日志必须脱敏并可配置关闭敏感内容。
- 如果 Codex 直接生成方案但仍被当作“隔离模型输出”，会污染评审证据；需要在 artifact 中标记 Codex 是内置/集成方案。
- 如果 Qwen、DeepSeek 均作为完整 plan 生成模型，可能导致三份方案重复；更合理的是 Qwen 主方案补强、DeepSeek 反方审查。
- 如果没有成本上限，full 模式可能在低风险任务上浪费 token 和人工时间。

## 需要人工确认的问题

1. v2 是否允许真实调用外部模型 API，还是先只实现 dry-run 和配置校验？
2. API Key 来源是否统一限定为环境变量，是否允许接入系统 keychain 或其他密钥管理？
3. 是否接受 `Codex` 在流程中作为内置集成模型，而不是隔离外部模型？
4. 默认三方是否正式改为 `Codex + Qwen + DeepSeek`，并把 DeepSeek 设为反方审查位？
5. 是否需要在 v2 中记录 token/cost，如果需要，成本估算精度要求到什么程度？
6. 真实调用失败时，是否允许覆盖旧 artifact，还是必须生成带时间戳的新 artifact？
