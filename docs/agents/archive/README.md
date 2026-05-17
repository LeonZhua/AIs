# docs/agents 归档说明

`docs/agents/archive/` 用于保存共享上下文入口的历史快照，避免把 `PROJECT_STATE.md` 和 `WORKLOG.md` 长期堆成难以恢复的正文。

## 归档对象

- `PROJECT_STATE.md`：当入口已经不再“轻量”，例如 Recent Handoff 过长、混入大段验证过程时，先做 verbatim 快照归档，再把当前文件改回轻量入口。
- `WORKLOG.md`：当工作日志体量明显膨胀时，整文件归档到这里；新的 `WORKLOG.md` 只保留轻量入口、归档指针和当前未结束任务索引。

## 归档原则

- 归档文件优先保留原文，不做二次摘要改写。
- 当前入口文件只保留恢复上下文必需的信息，不复制归档正文。
- 归档后要同步更新 `PROJECT_STATE.md`、`WORKLOG.md` 或相关任务记录里的指针，确保后续 Agent 能沿链路回溯。
