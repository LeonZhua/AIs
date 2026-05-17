import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "tools" / "agent_context.py"


class AgentContextToolTest(unittest.TestCase):
    def run_tool(self, *args, cwd=None):
        return subprocess.run(
            [sys.executable, str(SCRIPT), *args],
            cwd=cwd or ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )

    def test_validate_accepts_root_template(self):
        result = self.run_tool("validate")

        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        self.assertIn("AGENTS.md", result.stdout)
        self.assertIn("docs/agents/archive/README.md", result.stdout)
        self.assertIn("docs/agents/PROJECT_STATE.md", result.stdout)
        self.assertIn("pure Codex", result.stdout)

    def test_status_prints_current_context(self):
        result = self.run_tool("status")

        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        self.assertIn("Cursor_Kit Codex Context", result.stdout)
        self.assertIn("Current Focus", result.stdout)
        self.assertIn("Recent Handoff", result.stdout)

    def test_new_task_defaults_to_codex_agent(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            tasks_dir = root / "docs" / "agents" / "tasks"
            tasks_dir.mkdir(parents=True)
            (tasks_dir / "TEMPLATE-task.md").write_text(
                "# 任务记录：{{TITLE}}\n"
                "\n"
                "- 任务 ID：{{TASK_ID}}\n"
                "- 负责 Agent：{{AGENT}}\n"
                "- 状态：进行中\n",
                encoding="utf-8",
            )

            result = self.run_tool(
                "--root",
                str(root),
                "new-task",
                "--title",
                "示例任务",
            )

            self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
            created = list(tasks_dir.glob("*-示例任务.md"))
            self.assertEqual(len(created), 1, result.stdout)
            body = created[0].read_text(encoding="utf-8")
            self.assertIn("# 任务记录：示例任务", body)
            self.assertIn("- 负责 Agent：codex", body)
            self.assertRegex(created[0].name, r"^\d{4}-\d{2}-\d{2}-\d{4}-示例任务\.md$")

    def test_new_task_still_accepts_explicit_compatible_agent(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            tasks_dir = root / "docs" / "agents" / "tasks"
            tasks_dir.mkdir(parents=True)
            (tasks_dir / "TEMPLATE-task.md").write_text(
                "# 任务记录：{{TITLE}}\n"
                "\n"
                "- 任务 ID：{{TASK_ID}}\n"
                "- 负责 Agent：{{AGENT}}\n"
                "- 状态：进行中\n",
                encoding="utf-8",
            )

            result = self.run_tool(
                "--root",
                str(root),
                "new-task",
                "--title",
                "Claude 派生任务",
                "--agent",
                "claude",
            )

            self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
            created = list(tasks_dir.glob("*-Claude-派生任务.md"))
            self.assertEqual(len(created), 1, result.stdout)
            body = created[0].read_text(encoding="utf-8")
            self.assertIn("- 负责 Agent：claude", body)

    def test_export_rules_generates_claude_rules(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = self.run_tool(
                "export-rules",
                "--agent",
                "claude",
                "--target-root",
                tmp,
            )

            self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
            rules = Path(tmp) / "CLAUDE.md"
            self.assertTrue(rules.is_file(), result.stdout)
            body = rules.read_text(encoding="utf-8")
            self.assertIn("Claude Code", body)
            self.assertIn("docs/agents/PROJECT_STATE.md", body)
            self.assertIn("docs/agents/WORKLOG.md", body)
            self.assertIn("docs/agents/LESSONS.md", body)

    def test_export_rules_generates_trae_rules(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = self.run_tool(
                "export-rules",
                "--agent",
                "trae",
                "--target-root",
                tmp,
            )

            self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
            rules = Path(tmp) / ".trae" / "project_rules.md"
            self.assertTrue(rules.is_file(), result.stdout)
            body = rules.read_text(encoding="utf-8")
            self.assertIn("Trae", body)
            self.assertIn("docs/agents/PROJECT_STATE.md", body)
            self.assertIn("docs/agents/WORKLOG.md", body)
            self.assertIn("docs/agents/LESSONS.md", body)

    def test_export_rules_all_generates_both_compatible_rules(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = self.run_tool(
                "export-rules",
                "--agent",
                "all",
                "--target-root",
                tmp,
            )

            self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
            self.assertTrue((Path(tmp) / "CLAUDE.md").is_file(), result.stdout)
            self.assertTrue((Path(tmp) / ".trae" / "project_rules.md").is_file(), result.stdout)

    def test_export_rules_refuses_to_overwrite_without_force(self):
        with tempfile.TemporaryDirectory() as tmp:
            rules = Path(tmp) / "CLAUDE.md"
            rules.write_text("keep me\n", encoding="utf-8")

            result = self.run_tool(
                "export-rules",
                "--agent",
                "claude",
                "--target-root",
                tmp,
            )

            self.assertNotEqual(result.returncode, 0, result.stdout)
            self.assertIn("already exists", result.stderr)
            self.assertEqual(rules.read_text(encoding="utf-8"), "keep me\n")

    def test_export_rules_force_overwrites_existing_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            rules = Path(tmp) / "CLAUDE.md"
            rules.write_text("old\n", encoding="utf-8")

            result = self.run_tool(
                "export-rules",
                "--agent",
                "claude",
                "--target-root",
                tmp,
                "--force",
            )

            self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
            body = rules.read_text(encoding="utf-8")
            self.assertIn("Claude Code", body)
            self.assertNotEqual(body, "old\n")

    def seed_multi_review_root(self, root):
        docs = root / "docs" / "agents"
        docs.mkdir(parents=True)
        shutil.copytree(ROOT / "docs" / "agents" / "templates", docs / "templates")
        shutil.copytree(ROOT / "docs" / "agents" / "protocols", docs / "protocols")

    def test_multi_review_init_light_creates_single_file_task(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.seed_multi_review_root(root)

            result = self.run_tool(
                "--root",
                str(root),
                "multi-review",
                "init",
                "--title",
                "轻量多模型任务",
                "--mode",
                "light",
            )

            self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
            self.assertIn("task-id:", result.stdout)
            task_id = re.search(r"task-id: (.+)", result.stdout).group(1).strip()
            task_file = root / "docs" / "agents" / "tasks" / f"{task_id}.md"
            self.assertTrue(task_file.is_file(), result.stdout)
            body = task_file.read_text(encoding="utf-8")
            for heading in [
                "## Request",
                "## Model Prompts",
                "## Cross Reviews",
                "## Human Decisions",
                "## Verification",
                "## State Log",
            ]:
                self.assertIn(heading, body)

    def test_multi_review_init_full_creates_directory_artifacts(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.seed_multi_review_root(root)

            result = self.run_tool(
                "--root",
                str(root),
                "multi-review",
                "init",
                "--title",
                "复杂多模型任务",
                "--mode",
                "full",
            )

            self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
            task_id = re.search(r"task-id: (.+)", result.stdout).group(1).strip()
            task_dir = root / "docs" / "agents" / "tasks" / task_id
            for rel in [
                "task.md",
                "adjudication.md",
                "human-decisions.md",
                "final-plan.md",
                "verification.md",
                "state-log.md",
                "prompts/plans",
                "prompts/reviews",
                "plans",
                "reviews",
            ]:
                self.assertTrue((task_dir / rel).exists(), f"missing {rel}\n{result.stdout}")
            self.assertFalse((task_dir / "cost-log.md").exists())
            self.assertFalse((task_dir / "execution-assignments.md").exists())

    def test_multi_review_generates_prompts_and_reports_waiting_status(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.seed_multi_review_root(root)
            created = self.run_tool(
                "--root",
                str(root),
                "multi-review",
                "init",
                "--title",
                "Prompt 生成任务",
                "--mode",
                "full",
            )
            task_id = re.search(r"task-id: (.+)", created.stdout).group(1).strip()

            prompts = self.run_tool(
                "--root",
                str(root),
                "multi-review",
                "plan-prompts",
                "--task",
                task_id,
                "--models",
                "codex,deepseek,glm",
            )
            status = self.run_tool("--root", str(root), "multi-review", "status", "--task", task_id)

            self.assertEqual(prompts.returncode, 0, prompts.stderr + prompts.stdout)
            self.assertEqual(status.returncode, 0, status.stderr + status.stdout)
            self.assertIn("plans_waiting", status.stdout)
            self.assertIn("deepseek: prompt=yes output=no", status.stdout)
            self.assertTrue((root / "docs" / "agents" / "tasks" / task_id / "prompts" / "plans" / "deepseek.md").is_file())

    def test_multi_review_validate_task_and_check_quality_detect_placeholders(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.seed_multi_review_root(root)
            created = self.run_tool(
                "--root",
                str(root),
                "multi-review",
                "init",
                "--title",
                "质量检查任务",
                "--mode",
                "light",
            )
            task_id = re.search(r"task-id: (.+)", created.stdout).group(1).strip()

            structure = self.run_tool("--root", str(root), "multi-review", "validate-task", "--task", task_id)
            quality = self.run_tool("--root", str(root), "multi-review", "check-quality", "--task", task_id)

            self.assertEqual(structure.returncode, 0, structure.stderr + structure.stdout)
            self.assertNotEqual(quality.returncode, 0, quality.stdout)
            self.assertIn("placeholder", quality.stderr + quality.stdout)


class RootTemplateInvariantTest(unittest.TestCase):
    def read(self, rel):
        return (ROOT / rel).read_text(encoding="utf-8")

    def test_agent_entrypoints_point_to_shared_docs(self):
        body = self.read("AGENTS.md")
        self.assertIn("docs/agents/PROJECT_STATE.md", body)
        self.assertIn("docs/agents/WORKLOG.md", body)
        self.assertIn("docs/agents/LESSONS.md", body)

    def test_readme_describes_pure_codex_template_not_hybrid_or_multi_tool_template(self):
        body = self.read("README.md")

        self.assertIn("纯 Codex 主模板", body)
        self.assertIn("export-rules", body)
        self.assertNotIn("三工具共享上下文模板", body)
        self.assertNotIn("混合 AI Coding 工作流", body)
        self.assertNotIn("codex-kit", body)
        self.assertNotIn("claude-kit", body)

    def test_root_template_does_not_keep_compatible_rules_as_entrypoints(self):
        self.assertTrue((ROOT / "AGENTS.md").is_file())
        self.assertFalse((ROOT / "CLAUDE.md").exists())
        self.assertFalse((ROOT / ".trae" / "project_rules.md").exists())

    def test_archive_docs_exist_for_lightweight_context_maintenance(self):
        body = self.read("docs/agents/archive/README.md")

        self.assertIn("PROJECT_STATE.md", body)
        self.assertIn("WORKLOG.md", body)
        self.assertIn("轻量入口", body)

    def test_multi_model_review_protocol_and_templates_exist(self):
        protocol = self.read("docs/agents/protocols/multi-model-review.md")

        self.assertIn("多 AI", protocol)
        self.assertIn("prompt-only", protocol)
        self.assertIn("human_blocked", protocol)
        for rel in [
            "docs/agents/templates/multi-model-task-light.md",
            "docs/agents/templates/multi-model-task-full.md",
            "docs/agents/templates/model-plan.md",
            "docs/agents/templates/model-review.md",
            "docs/agents/templates/adjudication.md",
            "docs/agents/templates/human-decisions.md",
            "docs/agents/templates/final-plan.md",
            "docs/agents/templates/verification.md",
            "docs/agents/skills/multi-model-review/SKILL.md",
        ]:
            self.assertTrue((ROOT / rel).is_file(), rel)

    def test_old_single_tool_kit_directories_are_removed(self):
        self.assertFalse((ROOT / "codex-kit").exists())
        self.assertFalse((ROOT / "claude-kit").exists())
        self.assertFalse((ROOT / "docs" / "ai-workflows" / "hybrid-coding").exists())


if __name__ == "__main__":
    unittest.main()
