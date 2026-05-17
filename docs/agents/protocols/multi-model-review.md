# 多 AI 计划评审协议

本协议定义 Cursor_Kit 的 prompt-only 多 AI 评审流程。协议文件是只读规范，不包含任务占位符；可实例化内容放在 `docs/agents/templates/`。

## 定位

- Cursor_Kit 保存协议、模板、任务 artifact 和检查命令。
- Codex Skill 驱动流程，但不维护独立数据库。
- Codex 负责裁决、集成、验证和 `WORKLOG.md` 更新。
- 外部模型只提供独立方案、交叉评审和可选执行建议。
- v1 不自动调用 API，不保存 API Key，不自动执行外部分派。

## v1 操作手册

1. Codex 生成 plan prompts。
2. 用户把 prompt 分别粘贴到 DeepSeek、GLM、Kimi 等外部模型。
3. 用户把模型输出粘贴回对应 artifact。
4. Codex 运行结构和质量检查。
5. Codex 生成 review prompts。
6. 用户粘贴外部 review 输出。
7. Codex 再次运行结构和质量检查。
8. Codex 生成 adjudication 和 human-decisions。
9. 用户确认高风险项。
10. Codex 生成 final-plan。

## API-runner 操作手册

API-runner 是 prompt-only 之外的自动化路径，用于通过 Qwen/DeepSeek API 完成多 AI 评审和多 AI 验收。

1. 运行 `multi-review api-plan --task <task-id>` 生成 seed package、脱敏扫描、拆分门禁和 dry-run 调用计划。
2. 如需真实调用，必须同时设置 `MULTI_REVIEW_API_CALLS=enabled` 并传入 `--execute`。
3. 如用户人工声明任务过大，传入 `--split-task` 生成 `task-breakdown.json`；未声明则不自动拆分。
4. API plan 阶段调用 Qwen 生成结构化方案，调用 DeepSeek 做反方风险审查，Codex 本地裁决。
5. 命中敏感输入、Qwen/DeepSeek 不可用、解析失败、P0/P1 或静态高风险时，不生成可执行 final plan。
6. 实现或人工执行后，运行 `multi-review api-accept --task <task-id>` 生成验收 dry-run。
7. 如需真实验收调用，同样要求 `MULTI_REVIEW_API_CALLS=enabled` 和 `--execute`。
8. API accept 阶段由 Qwen 验收工程符合度，DeepSeek 验收安全边界，Codex 输出 acceptance report 和 rework items。

## 模式边界

- `light`：小型代码修复、轻量文档、无 P0/P1、无执行分派、预计只需 1-2 个外部模型。
- `full`：架构、API、数据模型、多模块任务、策略设计、生产行为、安全或资金风险、需要执行分派、需要 3 个以上模型 artifact。
- `light` 中出现 P0/P1、人工确认项超过 3 个、或需要执行分派时，应升级到 `full`。

## 隔离规则

- 独立方案阶段，每个模型只能看到同一份任务输入和共享上下文摘要。
- 独立方案阶段，不允许任何模型提前看到其他模型方案。
- `--models` 只生成 prompt，不证明模型已经被调用。
- 交叉评审阶段，评审模型只看到被评方案和必要上下文。
- 评审 prompt 必须列出被评方案路径。
- 评审输出必须先复述被评方案核心假设，再提出问题。

## 模型矩阵

| 任务类型 | 默认模型 | 说明 |
|---|---|---|
| 小型修复 | Codex + DeepSeek | 低成本反方审查 |
| 架构/API/数据模型 | Codex + DeepSeek + GLM-5.1 | GLM 评估工程落地和长链执行 |
| API 调用方案设计 | Codex + DeepSeek + Qwen | Qwen 评估 API 编排、结构化输出和中文工程方案完整性 |
| 长中文需求/复杂规则 | Codex + DeepSeek + Kimi K2.6 | Kimi 评估长上下文完整性 |
| 多模态材料 | Codex + Kimi K2.6 | v1 只生成 prompt，实际多模态处理待 API 或人工工具接入 |
| 成本敏感批量审查 | Codex + DeepSeek + GLM-4.7-FlashX | 低成本初筛 |
| 执行分派候选 | Codex + DeepSeek + GLM-5.1 | v1 只设计分派，不自动执行 |

## 人工确认

- 任一 P0 必须人工确认。
- P1 涉及安全、资金、不可逆操作、生产配置、数据库迁移、鉴权权限时必须人工确认。
- 架构、API、数据模型类 P1 可由 Codex 先裁决，但必须写入 `human-decisions.md`，并在 final-plan 前由人工一次性确认。
- 互斥建议、范围变更、验收标准变更、执行分派都必须人工确认。

## 裁决规则

- 不采用多数决。
- 所有 P0/P1 必须进入裁决表。
- Codex 可裁决低风险 P2/P3。
- 裁决必须有理由和证据，并标记是否涉及 Codex 自身方案。

## 质量门禁

- 必需 section 或文件必须存在。
- 不得保留模板占位符。
- 每个 plan 必须包含目标理解、关键约束、执行步骤、验收标准、风险。
- 每个 review 必须包含被评方案核心假设复述、至少 3 个检查维度、问题或未发现问题的依据。
- 每条 adjudication 必须有决策、理由、证据。
- 每个 human decision 必须有决策人和理由。
- verification 必须有命令、预期、实际结果、状态。
- API-runner 必须默认 dry-run；真实外部调用必须双重开关。
- 输入脱敏命中时禁止外发给外部模型。
- Qwen/DeepSeek 不可用时等待模型可用，不用缺失模型结果生成可执行 final plan。
- 模型输出解析失败时不合成可执行计划。
- token/cost 只记录，不设置硬上限。

## 状态机

```text
draft
  -> prompts_ready
  -> plans_waiting
  -> plans_ready
  -> reviews_waiting
  -> reviews_ready
  -> adjudicated
  -> human_decisions_ready
  -> human_blocked
  -> human_approved
  -> final_plan_ready
  -> executing
  -> verifying
  -> verification_failed
  -> rework_planning | rework_execution
  -> blocked
  -> verified
  -> closed
```

- `human_blocked` 表示等待人工确认，恢复条件记录在 `human-decisions.md`。
- `blocked` 表示外部条件阻塞，恢复条件记录在 `verification.md` 或 `state-log.md`。
- 验证失败时不能关闭任务，必须进入 `rework_planning` 或 `rework_execution`。
