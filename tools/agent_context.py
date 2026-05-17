#!/usr/bin/env python3
"""Small helper for Cursor_Kit Codex context files."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import ssl
import sys
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path


REQUIRED_FILES = [
    "AGENTS.md",
    "docs/agents/README.md",
    "docs/agents/archive/README.md",
    "docs/agents/protocols/multi-model-review.md",
    "docs/agents/PROJECT_STATE.md",
    "docs/agents/WORKLOG.md",
    "docs/agents/LESSONS.md",
    "docs/agents/tasks/TEMPLATE-task.md",
    "docs/agents/templates/multi-model-task-light.md",
    "docs/agents/templates/multi-model-task-full.md",
    "docs/agents/templates/model-plan.md",
    "docs/agents/templates/model-review.md",
    "docs/agents/templates/adjudication.md",
    "docs/agents/templates/human-decisions.md",
    "docs/agents/templates/final-plan.md",
    "docs/agents/templates/verification.md",
    "docs/agents/skills/multi-model-review/SKILL.md",
    ".cursor-kit-version",
]

PRIMARY_ENTRYPOINTS = ["AGENTS.md"]

COMPATIBLE_RULE_PATHS = {
    "claude": "CLAUDE.md",
    "trae": ".trae/project_rules.md",
}

SHARED_REFERENCES = [
    "docs/agents/PROJECT_STATE.md",
    "docs/agents/WORKLOG.md",
    "docs/agents/LESSONS.md",
]

TASK_AGENT_CHOICES = ["codex", "claude", "trae"]
EXPORT_AGENT_CHOICES = ["claude", "trae", "all"]
MULTI_REVIEW_MODE_CHOICES = ["light", "full"]
DEFAULT_MULTI_REVIEW_MODELS = ["codex", "deepseek", "glm"]
SUPPORTED_MULTI_REVIEW_MODELS = ["codex", "deepseek", "glm", "kimi", "qwen"]
LIGHT_REQUIRED_SECTIONS = [
    "Request",
    "Context Summary",
    "Model Prompts",
    "Model Plans",
    "Cross Review Prompts",
    "Cross Reviews",
    "Adjudication",
    "Human Decisions",
    "Final Plan",
    "Verification",
    "State Log",
    "Handoff",
]
FULL_REQUIRED_PATHS = [
    "task.md",
    "prompts/plans",
    "prompts/reviews",
    "plans",
    "reviews",
    "adjudication.md",
    "human-decisions.md",
    "final-plan.md",
    "verification.md",
    "state-log.md",
]
PLACEHOLDER_PATTERNS = ["{{", "TODO", "TBD", "（待补充）", "(待补充)"]
DEFAULT_API_MODELS = ["qwen", "deepseek"]
API_PROVIDER_CHOICES = ["qwen", "deepseek"]
SENSITIVE_PATTERNS = [
    r"sk-[A-Za-z0-9_\-]{12,}",
    r"AKIA[0-9A-Z]{16}",
    r"(?i)(api[_-]?key|token|secret|password)\s*[:=]\s*['\"]?[A-Za-z0-9_\-./+=]{12,}",
    r"(?i)authorization\s*:\s*bearer\s+[A-Za-z0-9_\-./+=]{12,}",
    r"-----BEGIN [A-Z ]*PRIVATE KEY-----",
    r"\b(?:10|127)\.\d{1,3}\.\d{1,3}\.\d{1,3}\b",
    r"\b192\.168\.\d{1,3}\.\d{1,3}\b",
]
STATIC_HIGH_RISK_PATTERNS = [
    "生产配置",
    "数据库",
    "权限",
    "资金",
    "密钥轮换",
    "隐私数据",
    "PII",
    "delete",
    "drop table",
    "payment",
]


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def write_json(path: Path, data: object) -> None:
    write_text(path, json.dumps(data, ensure_ascii=False, indent=2) + "\n")


def load_local_env(root: Path) -> dict[str, str]:
    env = dict(os.environ)
    env_path = root / ".env.local"
    if not env_path.is_file():
        return env
    for raw_line in read_text(env_path).splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip("'\"")
        env.setdefault(key, value)
    return env


def utcish_run_id() -> str:
    return datetime.now().strftime("%Y%m%d-%H%M%S")


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def scan_sensitive(text: str) -> list[str]:
    hits: list[str] = []
    for pattern in SENSITIVE_PATTERNS:
        if re.search(pattern, text):
            hits.append(pattern)
    return hits


def scan_static_risks(text: str) -> list[str]:
    lowered = text.lower()
    return [pattern for pattern in STATIC_HIGH_RISK_PATTERNS if pattern.lower() in lowered]


def redact(text: str) -> str:
    redacted = text
    for pattern in SENSITIVE_PATTERNS:
        redacted = re.sub(pattern, "[REDACTED]", redacted)
    return redacted


def get_json_candidate(text: str) -> dict[str, object] | None:
    stripped = text.strip()
    candidates = [stripped]
    for match in re.finditer(r"```(?:json)?\s*(.*?)```", text, flags=re.DOTALL | re.IGNORECASE):
        candidates.append(match.group(1).strip())
    for candidate in candidates:
        try:
            value = json.loads(candidate)
        except json.JSONDecodeError:
            continue
        if isinstance(value, dict):
            return value
    return None


def api_task_dir(root: Path, task_id: str) -> Path:
    mode, path = task_paths(root, task_id)
    if mode != "full":
        raise ValueError("api review requires full mode task directory")
    api_path = path / "api"
    api_path.mkdir(parents=True, exist_ok=True)
    return api_path


def append_jsonl(path: Path, record: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False) + "\n")


def render_compatible_rules(agent: str) -> str:
    if agent == "claude":
        display_name = "Claude Code"
        intro = (
            "Claude Code 会自动注入本文件。本文件由 Cursor_Kit 纯 Codex 主模板按需生成；"
            "只有用户明确切换到 Claude Code 时才使用。"
        )
        tool_note = "不要把项目规则重复写入 `~/.claude/CLAUDE.md`；项目规则以本文件和 `docs/agents/` 为准。"
    elif agent == "trae":
        display_name = "Trae"
        intro = (
            "Trae 使用本项目规则文件。本文件由 Cursor_Kit 纯 Codex 主模板按需生成；"
            "只有用户明确切换到 Trae 时才使用。"
        )
        tool_note = "不要把项目专属规则重复写入用户级 rules，避免跨项目污染。"
    else:
        raise ValueError(f"unsupported compatible rules agent: {agent}")

    return f"""# 本仓库约定（{display_name}）

{intro}

默认执行入口是 Codex 的 `AGENTS.md`。本文件是兼容 rules，用于让 {display_name} 按同一套任务记录机制接手目标项目。

## 硬约束

- 沟通与注释优先用中文；发现概念混用、验收口径模糊或表述不严谨时，直接指出并给出准确表述。
- 禁止在对话、代码、文档、日志或测试输出中暴露 API Key、令牌及任何密钥；一律用占位符代替。
- 不回滚、覆盖或删除用户未授权的现有改动。
- 修改代码或文档前，确认当前任务是否已有任务记录；没有则创建。
- 每轮结束前更新任务记录和 `docs/agents/WORKLOG.md`，写清变更、验证和下一步。
- 完成前运行最相关验证；无法验证时说明原因与剩余风险。

## 任务入口

复杂任务开始前按顺序读取：

1. `docs/agents/PROJECT_STATE.md`
2. `docs/agents/WORKLOG.md`
3. `docs/agents/LESSONS.md`

轻量问答、概念解释、纯讨论不强制创建任务记录。

## 文档路由

- `docs/agents/PROJECT_STATE.md`：当前阶段目标、主线任务、活跃任务、最近交接。
- `docs/agents/WORKLOG.md`：按时间倒序记录 Codex 和按需派生 rules 的工作回合。
- `docs/agents/LESSONS.md`：跨工具共享的长期项目经验。
- `docs/agents/tasks/`：任务级记录。
- `docs/agents/README.md`：共享上下文机制说明。

## {display_name} 机制注意事项

- 本文件是由 `python3 tools/agent_context.py export-rules --agent {agent}` 生成的兼容 rules，不是 Cursor_Kit 根模板的主动入口。
- {tool_note}
- 长任务可能发生上下文压缩，恢复事实必须写入共享文档，而不是只留在对话中。
"""


def extract_section(markdown: str, heading: str) -> str:
    pattern = re.compile(
        rf"^## {re.escape(heading)}\n(?P<body>.*?)(?=^## |\Z)",
        re.MULTILINE | re.DOTALL,
    )
    match = pattern.search(markdown)
    if not match:
        return "（未记录）"

    body = match.group("body").strip()
    if not body:
        return "（未记录）"

    lines = body.splitlines()
    return "\n".join(lines[:8]).strip()


def status(root: Path) -> int:
    state_path = root / "docs/agents/PROJECT_STATE.md"
    worklog_path = root / "docs/agents/WORKLOG.md"

    missing = [path for path in [state_path, worklog_path] if not path.is_file()]
    if missing:
        for path in missing:
            print(f"[missing] {path.relative_to(root)}", file=sys.stderr)
        return 1

    state = read_text(state_path)
    worklog = read_text(worklog_path)

    print("# Cursor_Kit Codex Context")
    print()
    print("## Current Focus")
    print(extract_section(state, "Current Focus"))
    print()
    print("## Main Task")
    print(extract_section(state, "Main Task"))
    print()
    print("## Recent Handoff")
    print(extract_section(state, "Recent Handoff"))
    print()
    print("## Latest Worklog")
    print(first_log_entry(worklog))
    return 0


def first_log_entry(markdown: str) -> str:
    match = re.search(r"^## .*\n(?P<body>.*?)(?=^## |\Z)", markdown, re.MULTILINE | re.DOTALL)
    if not match:
        return "（未记录）"
    body = match.group(0).strip()
    lines = body.splitlines()
    return "\n".join(lines[:10]).strip()


def validate(root: Path) -> int:
    errors: list[str] = []

    for rel in REQUIRED_FILES:
        path = root / rel
        if path.is_file():
            print(f"[ok] {rel}")
        else:
            errors.append(f"missing file: {rel}")

    for rel in PRIMARY_ENTRYPOINTS:
        path = root / rel
        if not path.is_file():
            continue
        body = read_text(path)
        for ref in SHARED_REFERENCES:
            if ref not in body:
                errors.append(f"{rel} does not reference {ref}")
            else:
                print(f"[ok] {rel} -> {ref}")

    for rel in COMPATIBLE_RULE_PATHS.values():
        path = root / rel
        if path.exists():
            errors.append(f"root template should not keep generated compatible rules: {rel}")

    for agent in ["claude", "trae"]:
        body = render_compatible_rules(agent)
        for ref in SHARED_REFERENCES:
            if ref not in body:
                errors.append(f"export-rules template for {agent} does not reference {ref}")
            else:
                print(f"[ok] export-rules {agent} -> {ref}")

    if errors:
        for error in errors:
            print(f"[error] {error}", file=sys.stderr)
        return 1

    print("[ok] pure Codex compatible agent context template is complete")
    return 0


def slugify(title: str) -> str:
    title = re.sub(r"\s+", "-", title.strip())
    title = re.sub(r"[^\w\u4e00-\u9fff-]+", "", title, flags=re.UNICODE)
    title = title.strip("-_")
    return title or "task"


def new_task(root: Path, title: str, agent: str) -> int:
    template_path = root / "docs/agents/tasks/TEMPLATE-task.md"
    if not template_path.is_file():
        print(f"[error] missing template: {template_path}", file=sys.stderr)
        return 1

    now = datetime.now()
    created_at = now.strftime("%Y-%m-%d %H:%M")
    task_id = f"{now:%Y-%m-%d-%H%M}-{slugify(title)}"
    task_path = root / "docs/agents/tasks" / f"{task_id}.md"

    counter = 2
    while task_path.exists():
        task_path = root / "docs/agents/tasks" / f"{task_id}-{counter}.md"
        counter += 1

    content = read_text(template_path)
    content = (
        content.replace("{{TITLE}}", title.strip())
        .replace("{{TASK_ID}}", task_path.stem)
        .replace("{{AGENT}}", agent)
        .replace("{{CREATED_AT}}", created_at)
    )

    write_text(task_path, content)
    print(f"created: {task_path.relative_to(root)}")
    print("next: register the task in docs/agents/PROJECT_STATE.md and update docs/agents/WORKLOG.md")
    return 0


def render_template(root: Path, rel: str, values: dict[str, str]) -> str:
    path = root / rel
    if not path.is_file():
        raise FileNotFoundError(path)
    content = read_text(path)
    for key, value in values.items():
        content = content.replace(f"{{{{{key}}}}}", value)
    return content


def parse_models(models: str | None) -> list[str]:
    if not models:
        return DEFAULT_MULTI_REVIEW_MODELS
    parsed = [model.strip() for model in models.split(",") if model.strip()]
    invalid = [model for model in parsed if model not in SUPPORTED_MULTI_REVIEW_MODELS]
    if invalid:
        raise ValueError(f"unsupported models: {', '.join(invalid)}")
    return parsed or DEFAULT_MULTI_REVIEW_MODELS


def task_paths(root: Path, task_id: str) -> tuple[str, Path]:
    tasks_root = root / "docs/agents/tasks"
    light_path = tasks_root / f"{task_id}.md"
    full_path = tasks_root / task_id
    if light_path.is_file():
        return "light", light_path
    if (full_path / "task.md").is_file():
        return "full", full_path
    raise FileNotFoundError(tasks_root / task_id)


def section_body(markdown: str, heading: str) -> str:
    pattern = re.compile(
        rf"^## {re.escape(heading)}\n(?P<body>.*?)(?=^## |\Z)",
        re.MULTILINE | re.DOTALL,
    )
    match = pattern.search(markdown)
    return match.group("body").strip() if match else ""


def append_to_section(markdown: str, heading: str, addition: str) -> str:
    pattern = re.compile(
        rf"(^## {re.escape(heading)}\n)(?P<body>.*?)(?=^## |\Z)",
        re.MULTILINE | re.DOTALL,
    )

    def replace(match: re.Match[str]) -> str:
        body = match.group("body").rstrip()
        if body:
            body = f"{body}\n\n{addition.strip()}\n\n"
        else:
            body = f"{addition.strip()}\n\n"
        return match.group(1) + body

    updated, count = pattern.subn(replace, markdown, count=1)
    if count == 0:
        return markdown.rstrip() + f"\n\n## {heading}\n{addition.strip()}\n"
    return updated


def multi_review_init(root: Path, title: str, mode: str) -> int:
    now = datetime.now()
    created_at = now.strftime("%Y-%m-%d %H:%M")
    task_id_base = f"{now:%Y-%m-%d-%H%M}-{slugify(title)}"
    tasks_root = root / "docs/agents/tasks"
    task_id = task_id_base
    counter = 2
    while (tasks_root / f"{task_id}.md").exists() or (tasks_root / task_id).exists():
        task_id = f"{task_id_base}-{counter}"
        counter += 1

    values = {"TITLE": title.strip(), "TASK_ID": task_id, "CREATED_AT": created_at, "MODE": mode}
    if mode == "light":
        content = render_template(root, "docs/agents/templates/multi-model-task-light.md", values)
        write_text(tasks_root / f"{task_id}.md", content)
    else:
        task_dir = tasks_root / task_id
        for rel in ["prompts/plans", "prompts/reviews", "plans", "reviews"]:
            (task_dir / rel).mkdir(parents=True, exist_ok=True)
        write_text(task_dir / "task.md", render_template(root, "docs/agents/templates/multi-model-task-full.md", values))
        for name, template in [
            ("adjudication.md", "docs/agents/templates/adjudication.md"),
            ("human-decisions.md", "docs/agents/templates/human-decisions.md"),
            ("final-plan.md", "docs/agents/templates/final-plan.md"),
            ("verification.md", "docs/agents/templates/verification.md"),
        ]:
            write_text(task_dir / name, render_template(root, template, values))
        write_text(
            task_dir / "state-log.md",
            f"# State Log\n\n| Time | From | To | Actor | Summary |\n|---|---|---|---|---|\n| {created_at} | - | draft | codex | 创建多 AI 评审任务。 |\n",
        )

    print(f"task-id: {task_id}")
    print(f"mode: {mode}")
    print("next: run multi-review plan-prompts and paste external model outputs into the task artifacts")
    return 0


def render_plan_prompt(task_id: str, model: str, mode: str, task_ref: str) -> str:
    role_bias = {
        "codex": "关注仓库约束、可执行性、验证路径和最终集成风险。",
        "deepseek": "以反方视角查找漏洞、边界条件、成本和过度设计。",
        "glm": "关注工程落地、可维护性、代码执行风险和长链任务稳定性。",
        "kimi": "关注长上下文完整性、中文需求理解和多模态材料审查。",
        "qwen": "关注 API 编排、供应商兼容性、结构化输出和中文工程方案完整性。",
    }[model]
    return f"""# {model} Plan Prompt

- Task ID: {task_id}
- Task Mode: {mode}
- Task Artifact: `{task_ref}`

你只应看到同一份任务输入和共享上下文摘要，不应看到其他模型的方案草稿。

## Role Bias

{role_bias}

## Required Output

1. 目标理解
2. 关键约束
3. 推荐方案
4. 执行步骤
5. 验收标准
6. 风险与边界
7. 需要人工确认的问题
"""


def render_review_prompt(task_id: str, reviewer: str, reviewed: list[str], mode: str) -> str:
    reviewed_files = ", ".join(f"`plans/{model}.md`" for model in reviewed)
    return f"""# {reviewer} Review Prompt

- Task ID: {task_id}
- Task Mode: {mode}
- Reviewer: {reviewer}
- Reviewed Plans: {', '.join(reviewed)}
- Reviewed Files: {reviewed_files}
- Excluded Own Plan: yes

你只能评审上面列出的方案。先复述被评方案核心假设，再提出问题。

## Required Output

- Reviewer:
- Reviewed Plans:
- Reviewed Files:
- Excluded Own Plan: yes|no

1. 我理解该方案的核心假设是：
2. 该方案最强的部分是：
3. 至少 3 个检查维度：
4. P0/P1/P2 问题或未发现问题的依据：
5. 建议采纳、拒绝或修改的点：
"""


def multi_review_plan_prompts(root: Path, task_id: str, models_arg: str | None) -> int:
    models = parse_models(models_arg)
    mode, path = task_paths(root, task_id)
    if mode == "light":
        body = read_text(path)
        additions = []
        for model in models:
            additions.append(render_plan_prompt(task_id, model, mode, str(path.relative_to(root))))
        write_text(path, append_to_section(body, "Model Prompts", "\n\n".join(additions)))
    else:
        for model in models:
            prompt = render_plan_prompt(task_id, model, mode, str((path / "task.md").relative_to(root)))
            write_text(path / "prompts/plans" / f"{model}.md", prompt)
    print(f"generated plan prompts for: {', '.join(models)}")
    print("next: paste each external model output into Model Plans or plans/<model>.md")
    return 0


def multi_review_review_prompts(root: Path, task_id: str) -> int:
    mode, path = task_paths(root, task_id)
    if mode == "light":
        models = [model for model in SUPPORTED_MULTI_REVIEW_MODELS if model in section_body(read_text(path), "Model Plans")]
        models = models or DEFAULT_MULTI_REVIEW_MODELS
        additions = []
        for reviewer in models:
            reviewed = [model for model in models if model != reviewer]
            additions.append(render_review_prompt(task_id, reviewer, reviewed, mode))
        write_text(path, append_to_section(read_text(path), "Cross Review Prompts", "\n\n".join(additions)))
    else:
        plan_files = sorted(file.stem for file in (path / "plans").glob("*.md"))
        models = plan_files or [file.stem for file in (path / "prompts/plans").glob("*.md")] or DEFAULT_MULTI_REVIEW_MODELS
        for reviewer in models:
            reviewed = [model for model in models if model != reviewer]
            write_text(path / "prompts/reviews" / f"{reviewer}.md", render_review_prompt(task_id, reviewer, reviewed, mode))
    print("generated review prompts")
    print("next: paste each external review into Cross Reviews or reviews/<model>-review.md")
    return 0


def multi_review_adjudication(root: Path, task_id: str) -> int:
    mode, path = task_paths(root, task_id)
    if mode == "light":
        body = read_text(path)
        body = append_to_section(body, "Adjudication", render_template(root, "docs/agents/templates/adjudication.md", {"TITLE": task_id, "TASK_ID": task_id, "CREATED_AT": ""}))
        body = append_to_section(body, "Human Decisions", render_template(root, "docs/agents/templates/human-decisions.md", {"TITLE": task_id, "TASK_ID": task_id, "CREATED_AT": ""}))
        write_text(path, body)
    else:
        print("adjudication artifacts already exist; fill adjudication.md and human-decisions.md")
    print("next: resolve low-risk items and record required human decisions")
    return 0


def has_placeholders(text: str) -> bool:
    return any(pattern in text for pattern in PLACEHOLDER_PATTERNS)


def validate_human_decisions_table(text: str) -> bool:
    return "| ID | Trigger | Decision Needed | Options | Decision | Decided By | Reason | Timestamp |" in text


def validate_adjudication_table(text: str) -> bool:
    return "| 建议 | 来源 | 严重级别 | 决策 | 理由 | 证据 | 是否涉及 Codex 自身方案 | 是否需人工 |" in text


def multi_review_validate_task(root: Path, task_id: str) -> int:
    errors: list[str] = []
    try:
        mode, path = task_paths(root, task_id)
    except FileNotFoundError as exc:
        print(f"[error] missing task: {exc}", file=sys.stderr)
        return 1

    if mode == "light":
        body = read_text(path)
        for heading in LIGHT_REQUIRED_SECTIONS:
            if f"## {heading}" not in body:
                errors.append(f"missing section: {heading}")
        if "| ID | Trigger | Decision Needed | Options | Decision | Decided By | Reason | Timestamp |" not in body:
            errors.append("missing human decisions table")
    else:
        for rel in FULL_REQUIRED_PATHS:
            if not (path / rel).exists():
                errors.append(f"missing artifact: {rel}")
        if (path / "human-decisions.md").is_file() and not validate_human_decisions_table(read_text(path / "human-decisions.md")):
            errors.append("human-decisions.md missing required table")
        if (path / "adjudication.md").is_file() and not validate_adjudication_table(read_text(path / "adjudication.md")):
            errors.append("adjudication.md missing required table")

    if errors:
        for error in errors:
            print(f"[error] {error}", file=sys.stderr)
        return 1
    print(f"[ok] {task_id} matches {mode} multi-review structure")
    return 0


def multi_review_check_quality(root: Path, task_id: str) -> int:
    warnings: list[str] = []
    mode, path = task_paths(root, task_id)
    files: list[tuple[str, str]]
    if mode == "light":
        body = read_text(path)
        files = [(path.name, body)]
        for heading in LIGHT_REQUIRED_SECTIONS:
            content = section_body(body, heading)
            if not content:
                warnings.append(f"empty section: {heading}")
            if has_placeholders(content):
                warnings.append(f"placeholder remains in section: {heading}")
    else:
        files = [(str(file.relative_to(path)), read_text(file)) for file in path.rglob("*.md")]
        for rel, text in files:
            if not text.strip():
                warnings.append(f"empty file: {rel}")
            if has_placeholders(text):
                warnings.append(f"placeholder remains in file: {rel}")

    combined = "\n".join(text for _, text in files)
    if "Reviewer:" in combined and "核心假设" not in combined:
        warnings.append("review content should restate reviewed plan core assumptions")
    if "Verification Results" in combined and "| Command | Expected | Actual | Status | Verified By |" not in combined:
        warnings.append("verification result table is missing")

    if warnings:
        for warning in warnings:
            print(f"[warning] {warning}", file=sys.stderr)
        return 1
    print(f"[ok] {task_id} passed basic multi-review quality checks")
    return 0


def multi_review_status(root: Path, task_id: str) -> int:
    mode, path = task_paths(root, task_id)
    print(f"task-id: {task_id}")
    print(f"mode: {mode}")
    if mode == "light":
        body = read_text(path)
        state = "plans_waiting" if section_body(body, "Model Prompts") and not section_body(body, "Model Plans") else "draft"
        print(f"state: {state}")
        for model in SUPPORTED_MULTI_REVIEW_MODELS:
            prompt = model in section_body(body, "Model Prompts")
            output = model in section_body(body, "Model Plans")
            print(f"{model}: prompt={'yes' if prompt else 'no'} output={'yes' if output else 'no'}")
    else:
        prompt_models = sorted(file.stem for file in (path / "prompts/plans").glob("*.md"))
        output_models = {file.stem for file in (path / "plans").glob("*.md")}
        state = "plans_waiting" if prompt_models and not output_models else "draft"
        if output_models and len(output_models) < len(prompt_models):
            state = "plans_waiting"
        if output_models and len(output_models) == len(prompt_models):
            state = "plans_ready"
        print(f"state: {state}")
        for model in prompt_models or DEFAULT_MULTI_REVIEW_MODELS:
            print(f"{model}: prompt={'yes' if model in prompt_models else 'no'} output={'yes' if model in output_models else 'no'}")
    return 0


def build_seed_package(root: Path, task_id: str, split_requested: bool) -> dict[str, object]:
    _, task_dir = task_paths(root, task_id)
    task_text = read_text(task_dir / "task.md")
    scheme_path = task_dir / "api/multi-round-review/final-scheme.md"
    scheme_text = read_text(scheme_path) if scheme_path.is_file() else ""
    source = f"{task_text}\n\n{scheme_text}"
    return {
        "task_id": task_id,
        "trace_id": utcish_run_id(),
        "goal": "通过多 AI 评审确保多 AI 执行方案可行；任务过大时合理拆分；实现后由多 AI 验收。",
        "non_goals": ["不自动执行代码修改", "不自动创建 PR", "不自动外部分派"],
        "constraints": {
            "api_calls": "默认 dry-run；真实调用需要 MULTI_REVIEW_API_CALLS=enabled 与 --execute",
            "secrets": "密钥只来自本地环境变量；不得写入 artifact、日志、命令行参数或对话",
            "cost": "记录 token/cost，不设置硬上限，不因预算阈值阻断调用",
            "decomposition": "只有人工声明后才拆分任务",
        },
        "model_roles": {
            "qwen": "结构化方案、流程工程化、schema/artifact 一致性",
            "deepseek": "反方风险、安全边界、失败路径、过度设计",
            "codex": "本地 seed、脱敏、拆分、裁决、验收汇总",
        },
        "split_requested": split_requested,
        "source_hash": sha256_text(source),
    }


def write_artifact_chain(api_dir: Path, trace_id: str, artifact: Path) -> None:
    content = read_text(artifact)
    append_jsonl(
        api_dir / "artifact-chain.jsonl",
        {
            "trace_id": trace_id,
            "artifact": str(artifact.relative_to(api_dir.parent)),
            "sha256": sha256_text(content),
            "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        },
    )


def write_seed_and_safety(root: Path, task_id: str, split_requested: bool) -> tuple[Path, dict[str, object], dict[str, object]]:
    api_dir_path = api_task_dir(root, task_id)
    seed = build_seed_package(root, task_id, split_requested)
    seed_path = api_dir_path / "seed-package.json"
    write_json(seed_path, seed)

    _, task_dir = task_paths(root, task_id)
    task_text = read_text(task_dir / "task.md")
    final_scheme = task_dir / "api/multi-round-review/final-scheme.md"
    scheme_text = read_text(final_scheme) if final_scheme.is_file() else ""
    hits = scan_sensitive(f"{task_text}\n{scheme_text}")
    safety = {
        "trace_id": seed["trace_id"],
        "status": "blocked" if hits else "pass",
        "policy": "命中敏感信息则禁止外发",
        "hits_count": len(hits),
        "hit_patterns": hits,
    }
    safety_path = api_dir_path / "safety-input-sanitization.json"
    write_json(safety_path, safety)
    write_artifact_chain(api_dir_path, str(seed["trace_id"]), seed_path)
    write_artifact_chain(api_dir_path, str(seed["trace_id"]), safety_path)
    return api_dir_path, seed, safety


def write_task_breakdown(api_dir_path: Path, seed: dict[str, object], split_requested: bool) -> dict[str, object]:
    if split_requested:
        breakdown = {
            "trace_id": seed["trace_id"],
            "status": "ready_for_human_confirmation",
            "requires_human_confirmation": True,
            "reason": "用户人工声明任务需要拆分。",
            "subtasks": [
                {
                    "id": "api-runner-core",
                    "goal": "环境变量、双重开关、Qwen/DeepSeek API client、脱敏日志。",
                    "dependencies": [],
                    "merge_strategy": "append",
                },
                {
                    "id": "seed-and-schema",
                    "goal": "Codex seed package、输入清洗、输出 schema、解析容错。",
                    "dependencies": ["api-runner-core"],
                    "merge_strategy": "append",
                },
                {
                    "id": "review-adjudication",
                    "goal": "Qwen plan、DeepSeek risk review、Codex 裁决、human decisions。",
                    "dependencies": ["seed-and-schema"],
                    "merge_strategy": "append",
                },
                {
                    "id": "acceptance-phase",
                    "goal": "多 AI 验收、acceptance evidence、acceptance report、rework items。",
                    "dependencies": ["review-adjudication"],
                    "merge_strategy": "append",
                },
            ],
        }
    else:
        breakdown = {
            "trace_id": seed["trace_id"],
            "status": "not_requested",
            "requires_human_confirmation": False,
            "reason": "未收到人工拆分声明，按用户决策不自动拆分任务。",
            "subtasks": [],
        }
    path = api_dir_path / "task-breakdown.json"
    write_json(path, breakdown)
    write_artifact_chain(api_dir_path, str(seed["trace_id"]), path)
    return breakdown


def provider_config(env: dict[str, str], provider: str) -> tuple[str, str, str]:
    if provider == "qwen":
        return (
            env.get("QWEN_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1"),
            env.get("DASHSCOPE_API_KEY") or env.get("QWEN_API_KEY", ""),
            env.get("QWEN_MODEL", "qwen3.6-plus"),
        )
    if provider == "deepseek":
        return (
            env.get("DEEPSEEK_BASE_URL", "https://api.deepseek.com"),
            env.get("DEEPSEEK_API_KEY", ""),
            env.get("DEEPSEEK_MODEL", "deepseek-v4-pro"),
        )
    raise ValueError(f"unsupported api provider: {provider}")


def call_chat_completion(provider: str, env: dict[str, str], prompt: str) -> dict[str, object]:
    base_url, api_key, model = provider_config(env, provider)
    if not api_key or api_key.startswith("<"):
        return {"ok": False, "provider": provider, "model": model, "error": "api key missing or placeholder"}

    payload: dict[str, object] = {
        "model": model,
        "messages": [
            {"role": "system", "content": "你是严谨的软件工程评审助手。禁止输出密钥、token、Authorization header 或真实凭证。"},
            {"role": "user", "content": prompt},
        ],
    }
    if provider == "qwen":
        payload["temperature"] = 0.2
        payload["max_tokens"] = 3600
    if provider == "deepseek":
        payload["thinking"] = {"type": "enabled"}
        payload["reasoning_effort"] = "high"
        payload["stream"] = False

    try:
        import certifi  # type: ignore

        context = ssl.create_default_context(cafile=certifi.where())
    except Exception:
        context = ssl.create_default_context()

    request = urllib.request.Request(
        base_url.rstrip("/") + "/chat/completions",
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=420, context=context) as response:
            body = json.loads(response.read().decode("utf-8"))
        message = body.get("choices", [{}])[0].get("message", {})
        return {
            "ok": True,
            "provider": provider,
            "model": model,
            "content": redact(message.get("content", "")),
            "usage": body.get("usage", {}),
        }
    except urllib.error.HTTPError as exc:
        error = redact(exc.read().decode("utf-8", errors="replace")[:1000])
        return {"ok": False, "provider": provider, "model": model, "error": f"HTTP {exc.code}: {error}"}
    except Exception as exc:
        return {"ok": False, "provider": provider, "model": model, "error": f"{type(exc).__name__}: {exc}"}


def normalize_model_output(provider: str, raw: str) -> dict[str, object]:
    parsed = get_json_candidate(raw)
    if parsed is not None:
        parsed.setdefault("provider", provider)
        parsed.setdefault("parse_status", "json")
        return parsed
    return {
        "provider": provider,
        "parse_status": "markdown",
        "summary": raw[:1000],
        "raw_content": raw,
    }


def api_review_prompts(seed: dict[str, object], breakdown: dict[str, object]) -> dict[str, str]:
    seed_json = json.dumps(seed, ensure_ascii=False, indent=2)
    breakdown_json = json.dumps(breakdown, ensure_ascii=False, indent=2)
    common = f"""目标：构建基于 API、流程的多 AI 评审方案。

Seed Package:
{seed_json}

Task Breakdown:
{breakdown_json}

硬约束：
- 不输出任何密钥、token、Authorization header 或真实凭证。
- 若发现 P0/P1，必须明确写出阻断理由。
- 输出可用 Markdown，但必须包含结构化标题和可执行建议。
"""
    return {
        "qwen": common
        + "\n你是 Qwen，检查流程、接口、schema、artifact、错误处理、验收标准是否完整，输出结构化方案。",
        "deepseek": common
        + "\n你是 DeepSeek，做反方风险审查，重点检查安全边界、失败路径、过度设计、人工门禁和验收闭环。",
    }


def api_accept_prompts(seed: dict[str, object], evidence: dict[str, object]) -> dict[str, str]:
    seed_json = json.dumps(seed, ensure_ascii=False, indent=2)
    evidence_json = json.dumps(evidence, ensure_ascii=False, indent=2)
    common = f"""目标：对 API 多 AI 评审方案的实现结果做多 AI 验收。

Seed Package:
{seed_json}

Acceptance Evidence:
{evidence_json}

硬约束：
- 不输出任何密钥、token、Authorization header 或真实凭证。
- 验收必须给出 pass/fail、P0/P1、证据引用和 rework 建议。
"""
    return {
        "qwen": common + "\n你是 Qwen，验收工程符合度：流程、schema、artifact、错误处理、成本记录。",
        "deepseek": common + "\n你是 DeepSeek，验收安全边界：密钥处理、双重开关、失败降级、人工门禁、敏感信息泄露。",
    }


def write_api_call_log(api_dir_path: Path, trace_id: str, result: dict[str, object], phase: str) -> None:
    usage = result.get("usage", {}) if isinstance(result.get("usage"), dict) else {}
    append_jsonl(
        api_dir_path / "calls-log.jsonl",
        {
            "trace_id": trace_id,
            "provider": result.get("provider"),
            "model": result.get("model"),
            "phase": phase,
            "status": "ok" if result.get("ok") else "failed",
            "prompt_tokens": usage.get("prompt_tokens", 0),
            "completion_tokens": usage.get("completion_tokens", 0),
            "total_tokens": usage.get("total_tokens", 0),
            "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        },
    )


def multi_review_api_plan(root: Path, task_id: str, execute: bool, split_task: bool) -> int:
    api_dir_path, seed, safety = write_seed_and_safety(root, task_id, split_task)
    breakdown = write_task_breakdown(api_dir_path, seed, split_task)
    trace_id = str(seed["trace_id"])

    if safety["status"] != "pass":
        write_json(
            api_dir_path / "human-decisions.json",
            {
                "trace_id": trace_id,
                "status": "blocked",
                "reason": "输入脱敏命中，按用户决策禁止外发。",
                "required_decision": "清理敏感输入或拒绝进入外部模型评审。",
            },
        )
        print("state: human_blocked")
        print("reason: sensitive input detected; external API review is forbidden")
        return 1

    env = load_local_env(root)
    if not execute:
        write_json(
            api_dir_path / "dry-run-plan.json",
            {
                "trace_id": trace_id,
                "status": "dry_run",
                "external_calls": [],
                "next": "set MULTI_REVIEW_API_CALLS=enabled and pass --execute to call Qwen/DeepSeek",
            },
        )
        print("state: dry_run")
        print(f"artifact: {api_dir_path.relative_to(root)}/dry-run-plan.json")
        return 0

    if env.get("MULTI_REVIEW_API_CALLS") != "enabled":
        write_json(
            api_dir_path / "human-decisions.json",
            {
                "trace_id": trace_id,
                "status": "blocked",
                "reason": "真实调用需要 MULTI_REVIEW_API_CALLS=enabled 与 --execute 双重开关。",
            },
        )
        print("state: blocked")
        print("reason: MULTI_REVIEW_API_CALLS is not enabled")
        return 1

    prompts = api_review_prompts(seed, breakdown)
    qwen = call_chat_completion("qwen", env, prompts["qwen"])
    write_api_call_log(api_dir_path, trace_id, qwen, "plan")
    if not qwen.get("ok"):
        write_json(api_dir_path / "human-decisions.json", {"trace_id": trace_id, "status": "blocked", "reason": "Qwen 不可用，等待模型可用。", "error": qwen.get("error")})
        print("state: human_blocked")
        print("reason: qwen unavailable")
        return 1
    qwen_output = normalize_model_output("qwen", str(qwen.get("content", "")))
    write_json(api_dir_path / "qwen-output.json", qwen_output)
    write_artifact_chain(api_dir_path, trace_id, api_dir_path / "qwen-output.json")

    deepseek = call_chat_completion("deepseek", env, prompts["deepseek"])
    write_api_call_log(api_dir_path, trace_id, deepseek, "risk-review")
    if not deepseek.get("ok"):
        write_json(api_dir_path / "human-decisions.json", {"trace_id": trace_id, "status": "blocked", "reason": "DeepSeek 不可用，等待模型可用。", "error": deepseek.get("error")})
        print("state: human_blocked")
        print("reason: deepseek unavailable")
        return 1
    deepseek_output = normalize_model_output("deepseek", str(deepseek.get("content", "")))
    write_json(api_dir_path / "deepseek-review.json", deepseek_output)
    write_artifact_chain(api_dir_path, trace_id, api_dir_path / "deepseek-review.json")

    combined = f"{json.dumps(qwen_output, ensure_ascii=False)}\n{json.dumps(deepseek_output, ensure_ascii=False)}"
    risks = scan_static_risks(combined)
    has_p0_p1 = bool(re.search(r"\bP[01]\b", combined))
    adjudication = {
        "trace_id": trace_id,
        "status": "human_blocked" if has_p0_p1 or risks else "final_plan_ready",
        "static_risks": risks,
        "has_p0_p1": has_p0_p1,
        "decision": "P0/P1 或静态高风险触发人工门禁" if has_p0_p1 or risks else "允许生成 final-plan",
    }
    write_json(api_dir_path / "adjudication.json", adjudication)
    if adjudication["status"] == "human_blocked":
        write_json(api_dir_path / "human-decisions.json", {"trace_id": trace_id, "status": "pending", "reason": adjudication["decision"], "static_risks": risks})
        print("state: human_blocked")
        print(f"artifact: {api_dir_path.relative_to(root)}/human-decisions.json")
        return 1

    final_plan = {
        "trace_id": trace_id,
        "status": "final_plan_ready",
        "summary": "Qwen 与 DeepSeek 均可用，未触发 P0/P1 或静态高风险门禁。",
        "qwen_ref": "api/qwen-output.json",
        "deepseek_ref": "api/deepseek-review.json",
        "next": "run api-accept after implementation evidence is available",
    }
    write_json(api_dir_path / "final-plan.json", final_plan)
    write_artifact_chain(api_dir_path, trace_id, api_dir_path / "final-plan.json")
    print("state: final_plan_ready")
    print(f"artifact: {api_dir_path.relative_to(root)}/final-plan.json")
    return 0


def multi_review_api_accept(root: Path, task_id: str, execute: bool) -> int:
    api_dir_path = api_task_dir(root, task_id)
    seed_path = api_dir_path / "seed-package.json"
    if not seed_path.is_file():
        print("[error] missing api/seed-package.json; run api-plan first", file=sys.stderr)
        return 1
    seed = json.loads(read_text(seed_path))
    trace_id = str(seed.get("trace_id", utcish_run_id()))
    evidence = {
        "trace_id": trace_id,
        "final_plan_exists": (api_dir_path / "final-plan.json").is_file(),
        "calls_log_exists": (api_dir_path / "calls-log.jsonl").is_file(),
        "human_decisions_exists": (api_dir_path / "human-decisions.json").is_file(),
        "artifact_chain_exists": (api_dir_path / "artifact-chain.jsonl").is_file(),
    }
    write_json(api_dir_path / "acceptance-evidence.json", evidence)

    env = load_local_env(root)
    if not execute:
        write_json(
            api_dir_path / "acceptance-report.json",
            {
                "trace_id": trace_id,
                "status": "dry_run",
                "pass": False,
                "next": "set MULTI_REVIEW_API_CALLS=enabled and pass --execute to call acceptance models",
            },
        )
        print("state: acceptance_dry_run")
        return 0
    if env.get("MULTI_REVIEW_API_CALLS") != "enabled":
        print("[error] MULTI_REVIEW_API_CALLS is not enabled", file=sys.stderr)
        return 1

    prompts = api_accept_prompts(seed, evidence)
    qwen = call_chat_completion("qwen", env, prompts["qwen"])
    write_api_call_log(api_dir_path, trace_id, qwen, "acceptance")
    if not qwen.get("ok"):
        write_json(api_dir_path / "rework-items.json", {"trace_id": trace_id, "status": "blocked", "reason": "Qwen 验收不可用，等待模型可用。", "error": qwen.get("error")})
        print("state: acceptance_blocked")
        return 1
    qwen_acceptance = normalize_model_output("qwen", str(qwen.get("content", "")))
    write_json(api_dir_path / "qwen-acceptance.json", qwen_acceptance)

    deepseek = call_chat_completion("deepseek", env, prompts["deepseek"])
    write_api_call_log(api_dir_path, trace_id, deepseek, "acceptance-security")
    if not deepseek.get("ok"):
        write_json(api_dir_path / "rework-items.json", {"trace_id": trace_id, "status": "blocked", "reason": "DeepSeek 验收不可用，等待模型可用。", "error": deepseek.get("error")})
        print("state: acceptance_blocked")
        return 1
    deepseek_acceptance = normalize_model_output("deepseek", str(deepseek.get("content", "")))
    write_json(api_dir_path / "deepseek-acceptance.json", deepseek_acceptance)

    combined = f"{json.dumps(qwen_acceptance, ensure_ascii=False)}\n{json.dumps(deepseek_acceptance, ensure_ascii=False)}"
    failed = bool(re.search(r"\bP[01]\b", combined)) or "fail" in combined.lower() or "失败" in combined
    report = {
        "trace_id": trace_id,
        "pass": not failed,
        "status": "acceptance_failed" if failed else "accepted",
        "evidence_refs": ["api/acceptance-evidence.json", "api/qwen-acceptance.json", "api/deepseek-acceptance.json"],
        "next_action": "rework" if failed else "close",
    }
    write_json(api_dir_path / "acceptance-report.json", report)
    if failed:
        write_json(api_dir_path / "rework-items.json", {"trace_id": trace_id, "status": "open", "reason": "多 AI 验收发现 P0/P1 或失败信号。"})
    print(f"state: {report['status']}")
    return 0 if not failed else 1


def export_rules(target_root: Path, agent: str, force: bool) -> int:
    target_root = target_root.expanduser().resolve()
    target_root.mkdir(parents=True, exist_ok=True)

    agents = ["claude", "trae"] if agent == "all" else [agent]
    targets = [(name, target_root / COMPATIBLE_RULE_PATHS[name]) for name in agents]

    existing = [path for _, path in targets if path.exists()]
    if existing and not force:
        for path in existing:
            print(f"[error] already exists: {path}", file=sys.stderr)
        print("next: pass --force to overwrite existing compatible rules", file=sys.stderr)
        return 1

    for name, path in targets:
        write_text(path, render_compatible_rules(name))
        print(f"wrote: {path}")

    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Inspect and maintain Cursor_Kit Codex context.")
    parser.add_argument("--root", default=".", help="Project root. Defaults to current directory.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("status", help="Print current shared context summary.")
    subparsers.add_parser("validate", help="Validate required shared context files and references.")

    new_task_parser = subparsers.add_parser("new-task", help="Create a task record from the template.")
    new_task_parser.add_argument("--title", required=True, help="Task title.")
    new_task_parser.add_argument(
        "--agent",
        default="codex",
        choices=TASK_AGENT_CHOICES,
        help="Agent creating the task. Defaults to codex.",
    )

    export_parser = subparsers.add_parser("export-rules", help="Generate compatible Claude Code or Trae rules.")
    export_parser.add_argument("--agent", required=True, choices=EXPORT_AGENT_CHOICES, help="Compatible rules to export.")
    export_parser.add_argument("--target-root", required=True, help="Target project root for generated rules.")
    export_parser.add_argument("--force", action="store_true", help="Overwrite existing generated rules.")

    multi_parser = subparsers.add_parser("multi-review", help="Manage prompt-only multi-model review artifacts.")
    multi_subparsers = multi_parser.add_subparsers(dest="multi_command", required=True)

    multi_init = multi_subparsers.add_parser("init", help="Create a multi-model review task.")
    multi_init.add_argument("--title", required=True, help="Task title.")
    multi_init.add_argument("--mode", default="light", choices=MULTI_REVIEW_MODE_CHOICES, help="Artifact mode.")

    multi_plan = multi_subparsers.add_parser("plan-prompts", help="Generate isolated model plan prompts.")
    multi_plan.add_argument("--task", required=True, help="Task id from multi-review init.")
    multi_plan.add_argument("--models", default=",".join(DEFAULT_MULTI_REVIEW_MODELS), help="Comma-separated model keys.")

    multi_review = multi_subparsers.add_parser("review-prompts", help="Generate cross-review prompts.")
    multi_review.add_argument("--task", required=True, help="Task id from multi-review init.")

    multi_adj = multi_subparsers.add_parser("adjudication", help="Prepare adjudication and human-decision artifacts.")
    multi_adj.add_argument("--task", required=True, help="Task id from multi-review init.")

    multi_validate = multi_subparsers.add_parser("validate-task", help="Validate task artifact structure.")
    multi_validate.add_argument("--task", required=True, help="Task id from multi-review init.")

    multi_quality = multi_subparsers.add_parser("check-quality", help="Run basic content-quality checks.")
    multi_quality.add_argument("--task", required=True, help="Task id from multi-review init.")

    multi_status = multi_subparsers.add_parser("status", help="Print multi-review task state.")
    multi_status.add_argument("--task", required=True, help="Task id from multi-review init.")

    multi_api_plan = multi_subparsers.add_parser("api-plan", help="Run API-based multi-AI review planning.")
    multi_api_plan.add_argument("--task", required=True, help="Task id from multi-review init.")
    multi_api_plan.add_argument("--execute", action="store_true", help="Call external Qwen/DeepSeek APIs. Requires MULTI_REVIEW_API_CALLS=enabled.")
    multi_api_plan.add_argument("--split-task", action="store_true", help="User-declared task decomposition request.")

    multi_api_accept = multi_subparsers.add_parser("api-accept", help="Run API-based multi-AI acceptance.")
    multi_api_accept.add_argument("--task", required=True, help="Task id from multi-review init.")
    multi_api_accept.add_argument("--execute", action="store_true", help="Call external Qwen/DeepSeek APIs. Requires MULTI_REVIEW_API_CALLS=enabled.")

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    root = Path(args.root).expanduser().resolve()

    if args.command == "status":
        return status(root)
    if args.command == "validate":
        return validate(root)
    if args.command == "new-task":
        return new_task(root, args.title, args.agent)
    if args.command == "export-rules":
        return export_rules(Path(args.target_root), args.agent, args.force)
    if args.command == "multi-review":
        try:
            if args.multi_command == "init":
                return multi_review_init(root, args.title, args.mode)
            if args.multi_command == "plan-prompts":
                return multi_review_plan_prompts(root, args.task, args.models)
            if args.multi_command == "review-prompts":
                return multi_review_review_prompts(root, args.task)
            if args.multi_command == "adjudication":
                return multi_review_adjudication(root, args.task)
            if args.multi_command == "validate-task":
                return multi_review_validate_task(root, args.task)
            if args.multi_command == "check-quality":
                return multi_review_check_quality(root, args.task)
            if args.multi_command == "status":
                return multi_review_status(root, args.task)
            if args.multi_command == "api-plan":
                return multi_review_api_plan(root, args.task, args.execute, args.split_task)
            if args.multi_command == "api-accept":
                return multi_review_api_accept(root, args.task, args.execute)
        except (FileNotFoundError, ValueError) as exc:
            print(f"[error] {exc}", file=sys.stderr)
            return 1

    parser.error(f"unknown command: {args.command}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
