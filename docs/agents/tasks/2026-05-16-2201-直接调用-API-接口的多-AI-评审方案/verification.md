# Verification

| Command or Check | Expected | Actual | Status |
|---|---|---|---|
| Qwen API review call | 返回 Qwen 评审并写入 `reviews/qwen-review.md` | 成功，usage 记录在 review 文件 | pass |
| DeepSeek API review call | 返回 DeepSeek 评审并写入 `reviews/deepseek-review.md` | 成功，usage 记录在 review 文件 | pass |
| 裁决表 | 覆盖 P0/P1/P2 关键问题并给出决策 | 已写入 `adjudication.md` | pass |
| 人工确认项 | P0/P1 和执行门禁进入确认表 | 已写入 `human-decisions.md`，部分待确认 | partial |
| 最终计划 | 生成 API-runner 最终计划 | 已写入 `final-plan.md` | pass |
| 密钥泄露检查 | 文档中不得包含真实 API Key 或 Authorization header | 未运行自动扫描；人工写入时未包含真实密钥 | not_run |
