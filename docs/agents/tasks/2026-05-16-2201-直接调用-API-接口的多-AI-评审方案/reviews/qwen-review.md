# Qwen API Review

# Qwen API Review

## 被评方案核心假设
1. **单一本地种子包可完全约束多模型行为边界**：Codex 生成的结构化 JSON 能一次性定义任务目标、安全红线、模型分工与裁决规则，后续 Qwen/DeepSeek 的派生请求无需额外上下文即可严格遵循。
2. **外部模型输出具备结构确定性**：Qwen 与 DeepSeek 能稳定返回符合预设 Schema 的 JSON/结构化文本，Codex 可直接进行字段级校验与合成。
3. **默认 dry-run + 显式 `--execute` + P0/P1 阻断机制可覆盖核心安全风险**：通过环境变量隔离密钥、禁止日志落盘、高风险自动熔断，可在不依赖外部网关的情况下实现生产级安全基线。
4. **串行调用（Qwen → DeepSeek）在 v1 阶段足以平衡复杂度与质量**：避免并发带来的状态同步、日志交错与失败恢复难题，以确定性换取可维护性。
5. **Codex 作为本地裁决者具备确定性冲突消解能力**：当 Qwen 与 DeepSeek 意见冲突或一方失败时，Codex 能按预设规则（保守优先、标记缺失、降级处理）输出可审计的最终计划。

## 最强部分
- **安全基线清晰且可执行**：环境变量隔离、默认 dry-run、密钥不落盘/不打印、P0/P1 自动阻断，形成闭环防御。
- **职责解耦彻底**：Qwen 专注架构与 Schema，DeepSeek 专注反方风险，Codex 专注本地集成与裁决，避免模型角色重叠导致的决策噪音。
- **主动裁剪过度设计**：移除默认交叉评审、保留 prompt-only 作为 fallback、限制外部模型数量为 2，显著降低 Token 消耗与状态机复杂度。
- **审计字段设计完整**：脱敏摘要、Token 计量、状态追踪、`run_id` 关联，满足合规与成本核算需求。

## 检查维度
| 维度 | 评估结论 | 关键依据 |
|------|----------|----------|
| **可落地性** | 中等偏上，存在工程实现断点 | 种子包结构清晰，但 LLM 输出解析、重试策略、部分失败降级逻辑未给出确定性实现路径，直接编码易遇阻塞。 |
| **安全性** | 强，但存在输入侧盲区 | 密钥隔离与 dry-run 机制优秀，但 `task_brief`/`review_inputs` 若含未清洗的用户输入，可能引发 Prompt 注入或约束逃逸。 |
| **不过度设计** | 优秀 | 明确砍掉人工粘贴链路、默认交叉评审与冗余状态机；串行调用与双模型限制符合 v1 最小可行原则。 |
| **可审计性** | 良好，缺链路追踪标识 | 成本与状态记录完整，但缺少 `trace_id` 或种子包哈希，跨模型调用与人工确认项难以在审计日志中强关联。 |

## P0/P1/P2/P3 问题
- **P0（阻断级）**：LLM 输出解析与重试策略缺失。方案规定“输出结构不合格不进入合成”，但未定义解析容错机制（如 Markdown 代码块提取、JSON 修复、最大重试次数）。若 Qwen/DeepSeek 返回非标准格式，流水线将直接中断，不可落地。
- **P0（阻断级）**：种子包输入侧未做 Prompt 注入隔离。`task_brief` 与 `review_inputs` 直接派生自用户任务，若包含恶意指令（如“忽略安全约束”“输出完整环境变量”），将穿透 `constraints` 边界。缺乏系统提示词隔离或输入清洗层。
- **P1（高危）**：裁决规则缺乏程序化确定性。“以更保守、更少副作用的方案为默认”在代码中无法直接映射为布尔逻辑或权重矩阵。冲突消解需明确优先级（如：安全 > 成本 > 性能 > 功能），否则合成阶段易产生非确定性输出。
- **P1（高危）**：审计日志缺少强关联标识。当前 `run_id` 仅记录单次运行，未包含 `seed_package_hash` 或 `trace_id`。当 Qwen 成功、DeepSeek 超时、人工介入时，审计链路断裂，无法追溯裁决依据。
- **P2（中危）**：部分成功（Partial Success）处理逻辑模糊。若 Qwen 返回有效方案但 DeepSeek 超时/失败，方案仅提“标记缺失来源并降级”，未明确是否允许继续合成、是否强制人工确认、是否影响 P0/P1 判定。
- **P2（中危）**：CLI 参数 `--models qwen,deepseek` 与硬编码职责冲突。派生 Prompt 与裁决规则强绑定双模型角色，若用户传入 `--models qwen`，Codex 将缺失反方审查输入，但流程未定义降级策略。
- **P3（低危）**：环境变量 `MULTI_REVIEW_API_CALLS="disabled"` 与 `--dry-run` 语义重叠。双开关并存易导致状态不一致（如 `--execute` 但 env 为 disabled），建议统一由 CLI 参数控制。
- **P3（低危）**：DeepSeek `thinking.enabled` 参数兼容性未验证。OpenAI-compatible 端点可能不支持该字段，需确认 DashScope/DeepSeek 官方 SDK 的实际透传方式，否则可能触发 `400` 错误。

## 建议采纳、拒绝或修改的点
| 建议项 | 采纳/拒绝/修改 | 理由与落地方案 |
|--------|----------------|----------------|
| **采纳 DeepSeek 风险分级策略** | 采纳 | 在 `task_brief` 中增加 `risk_level: low|medium|high` 字段。低风险直接跳过 DeepSeek 调用，仅走 Qwen + 人工 Checklist，显著降低 Token 成本与延迟。 |
| **修改 LLM 输出解析机制** | 修改 | 增加 `extract_json_from_markdown()` 与 `json_repair()` 容错层；定义最大重试 2 次，失败后标记 `status: parse_failed` 并触发人工确认，避免流水线硬中断。 |
| **修改裁决规则为确定性矩阵** | 修改 | 将“保守优先”转化为可执行规则：`if deepseek.p0 > 0 → block; else if qwen.cost > threshold → warn; else → merge`。冲突时以安全边界为最高权重，功能建议次之。 |
| **采纳运行时验证脚本（沙箱）** | 采纳 | 在 `review_inputs` 中预留 `sandbox_test_output` 字段。高风险任务强制要求附带 `curl`/单元测试结果，模型评审必须引用实际响应，降低幻觉风险。 |
| **修改审计日志增加 trace_id** | 修改 | 在 Cost/Audit JSON 中追加 `seed_hash` 与 `trace_id`，Codex 合成时写入同一 ID。确保 dry-run → execute → 人工确认全链路可追溯。 |
| **拒绝默认并发调用** | 拒绝 | 维持串行调用（Qwen → DeepSeek）。v1 阶段并发带来的日志交错、失败回滚与成本不可控远超收益，符合“不过度设计”原则。 |
| **修改 CLI 参数语义统一** | 修改 | 移除 `MULTI_REVIEW_API_CALLS` 环境变量，统一由 `--dry-run`（默认）与 `--execute` 控制。增加 `--force` 参数用于人工覆盖 P1 阻断（需二次确认）。 |
| **采纳输入侧 Prompt 隔离** | 采纳 | 在种子包生成阶段增加 `sanitize_input()`：剥离用户输入中的 `system/assistant` 角色标记、环境变量引用、越权指令；将清洗后内容注入 `review_inputs`。 |

## API Call Metadata

- provider: qwen
- model: qwen3.6-plus
- status: ok
- usage: `{"prompt_tokens": 5734, "completion_tokens": 4963, "total_tokens": 10697, "completion_tokens_details": {"reasoning_tokens": 3236, "text_tokens": 4963}, "prompt_tokens_details": {"text_tokens": 5734}}`
