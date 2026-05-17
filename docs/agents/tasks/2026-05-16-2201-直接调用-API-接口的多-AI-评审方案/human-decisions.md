# Human Decisions

| ID | Required Decision | Default | Decision Owner | Status | Reason |
|---|---|---|---|---|---|
| H1 | 是否允许 API-runner 第一版发起真实外部模型调用 | 允许，但必须双重开关 | 用户 | approved | 用户已提供本地 key 并要求手动调用 API；正式实现仍默认 dry-run。 |
| H2 | 是否允许 API-runner 自动执行代码修改或外部分派 | 不允许 | 用户 | approved | 本任务目标是生成评审方案，不是自动执行实现。 |
| H3 | 是否默认将 API 评审结果写入 artifact | 是 | 用户 | approved | 项目要求长任务事实沉淀到共享文档。 |
| H4 | DeepSeek 高风险未消解时是否阻断最终可执行计划 | 是 | 用户 | approved | 高风险必须人工确认，不能被自动合成绕过。 |
| H5 | 是否接受双重开关作为真实调用门禁 | 是 | 用户 | pending | 需在实现前确认：`MULTI_REVIEW_API_CALLS=enabled` 和 `--execute` 必须同时满足。 |
| H6 | 是否设置每任务 token/cost 硬上限 | 不限制 | 用户 | approved | 用户确认“不限制”。实现只记录 token/cost，不因预算阈值阻断调用。 |
