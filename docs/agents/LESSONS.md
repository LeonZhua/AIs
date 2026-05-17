# Lessons

> 这里只记录长期适用的项目经验。临时过程、一次性决策和任务流水写入 `WORKLOG.md` 或任务记录。

## 当前经验

- 纯 Codex 主模板应只把 `AGENTS.md` 作为根目录主动入口；Claude Code / Trae rules 通过生成器按需派生，避免模板定位漂移。
- 工具切换的关键不是互相调用，而是维护一个足够短、足够及时的共享上下文入口。
- 多 AI 评审应分层：Cursor_Kit 保存协议、模板和 artifact，Skill 只驱动流程；v1 默认 prompt-only，外部模型输出由人工粘贴，避免把密钥或供应商耦合写进模板核心。
- `PROJECT_STATE.md` 和 `WORKLOG.md` 要长期保持轻量入口；旧正文优先 verbatim 归档到 `docs/agents/archive/`，不要在入口层堆历史。
- 封板前先补齐任务记录、`WORKLOG.md` 和必要的 `PROJECT_STATE.md`，再做最终提交和验证，避免代码与共享上下文脱节。
- 任务过程记录和长期经验必须分开；否则新工具接手时会被过期细节干扰。
