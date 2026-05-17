# Adjudication

## Scope

本裁决基于真实 API 调用产生的 Qwen Review 和 DeepSeek Review，目标是完成“基于 API、流程的多 AI 评审方案”的完整评审闭环。

## Decision Table

| ID | Source | Severity | Issue | Decision | Reason | Evidence |
|---|---|---:|---|---|---|---|
| A1 | Qwen | P0 | LLM 输出解析与重试策略缺失 | 采纳 | API-runner 必须能处理 Markdown 包裹 JSON、空输出、截断、非结构化文本，否则无法稳定落地。 | Qwen Review P0：输出解析与重试策略缺失。 |
| A2 | Qwen | P0 | 种子包输入侧缺少 prompt 注入隔离 | 采纳 | 用户输入会进入外部模型上下文，必须先清洗角色伪造、越权指令、环境变量索取等内容。 | Qwen Review P0：输入侧未做 Prompt 注入隔离。 |
| A3 | DeepSeek | P0 | 密钥安全仅靠文档约定，缺少运行时强制校验 | 采纳 | 安全边界必须由 client/logging 层强制执行，不能只依赖开发者遵守文档。 | DeepSeek Review P0：运行时强制脱敏缺失。 |
| A4 | DeepSeek | P0 | dry-run/execute 单一开关可能被误触发 | 采纳并升级为设计约束 | 真实 API 调用必须同时满足环境变量 `MULTI_REVIEW_API_CALLS=enabled` 和 CLI `--execute`。 | DeepSeek Review P0：dry-run 机制可能被绕过或误开。 |
| A5 | Qwen | P1 | 裁决规则缺乏程序化确定性 | 采纳 | 最终计划必须定义确定性裁决矩阵，而不是“保守优先”这类模糊文字。 | Qwen Review P1：裁决规则无法直接映射为程序逻辑。 |
| A6 | DeepSeek | P1 | 不能只依赖 DeepSeek 风险标签阻断 | 采纳 | Codex 必须内置静态风险规则，DeepSeek 只是增强信号。 | DeepSeek Review P1：模型可能漏报或输出异常。 |
| A7 | DeepSeek | P1 | 成本记录没有硬上限 | 部分采纳 | 用户明确选择不设置 token/cost 硬上限；实现仍必须记录 token/cost，但不得因预算阈值阻断调用。 | DeepSeek Review P1：费用可能事后才发现；用户后续确认“不限制”。 |
| A8 | Qwen | P1 | 审计日志缺少 trace_id / seed_hash | 采纳 | 多模型调用和人工确认需要强关联标识。 | Qwen Review P1：审计链路断裂风险。 |
| A9 | Qwen / DeepSeek | P2 | 部分成功降级策略不明确 | 采纳 | 任一模型失败时不得输出“可执行 final plan”，只能输出降级计划和缺失来源。 | 两方 Review 均指出 partial success 模糊。 |
| A10 | Qwen / Codex | P2 | 默认输出到 chat 不利于审计 | 采纳 | API 版本应默认落 artifact，聊天只返回摘要。 | Qwen Review 建议默认 artifact。 |
| A11 | DeepSeek | P2 | Qwen 原始方案偏通用 HTTP 客户端 | 采纳为经验 | 后续 Qwen prompt 必须更聚焦多模型评审流程，而非通用 API client。 | DeepSeek Review P2：目标偏移。 |

## Final Decisions

1. API-runner 第一版只生成评审计划、风险清单、人工确认项和最终计划，不执行代码或外部分派。
2. 默认输出 artifact，聊天只输出摘要。
3. 真实 API 调用需要双重开关：`MULTI_REVIEW_API_CALLS=enabled` + `--execute`。
4. Codex 第一轮种子包必须经过输入清洗和 seed hash 记录。
5. Qwen/DeepSeek 输出必须经过解析、schema 校验和脱敏扫描。
6. Codex 裁决必须同时使用 DeepSeek 风险与本地静态风险规则。
7. 任一 P0 或未消解 P1 必须进入 `human-decisions.md`，不得生成可执行计划。
8. token/cost 只记录不阻断；不设置每任务硬上限。
9. 增加独立多 AI 验收阶段：评审用于决定方案，验收用于验证实现结果；验收需由 Codex 汇总本地证据，并调用 Qwen/DeepSeek 分别验收工程符合度和安全边界。
10. 增加任务拆分门禁：大任务不得直接进入 API 评审，必须先由 Codex 生成 `task-breakdown`，拆成可独立评审、实现和验收的子任务。
