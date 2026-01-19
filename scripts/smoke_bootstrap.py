#!/usr/bin/env python3
import json
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import List, Optional


def run(cmd: List[str], cwd: Optional[Path] = None) -> str:
    result = subprocess.run(
        cmd,
        cwd=str(cwd) if cwd else None,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"Command failed: {' '.join(cmd)}\n"
            f"stdout:\n{result.stdout}\n"
            f"stderr:\n{result.stderr}"
        )
    return result.stdout.strip()


def check(condition: bool, message: str, errors: List[str]) -> None:
    if not condition:
        errors.append(message)


def main() -> int:
    repo_root = Path(__file__).resolve().parents[1]
    bootstrap = repo_root / "skills" / "project-bootstrap" / "scripts" / "bootstrap.py"
    skillsets = json.loads((repo_root / "catalog" / "skillsets.json").read_text(encoding="utf-8"))
    baseline = skillsets.get("baseline", [])

    commit = run(["git", "rev-parse", "HEAD"], cwd=repo_root)

    with tempfile.TemporaryDirectory() as tmpdir:
        project_root = Path(tmpdir)
        run(
            [
                sys.executable,
                str(bootstrap),
                "init",
                "--skillregistry-git",
                str(repo_root),
                "--skillregistry-ref",
                commit,
                "--install-method",
                "local",
            ],
            cwd=project_root,
        )

        errors: List[str] = []
        check((project_root / ".agent" / "skillregistry").is_dir(), "missing .agent/skillregistry", errors)
        check((project_root / ".agent" / "project_profile.json").is_file(), "missing .agent/project_profile.json", errors)
        check((project_root / ".agent" / "skills_state.json").is_file(), "missing .agent/skills_state.json", errors)
        check((project_root / ".agent" / "skills_todo.md").is_file(), "missing .agent/skills_todo.md", errors)

        for skill in baseline:
            check(
                (project_root / ".codex" / "skills" / skill / "SKILL.md").is_file(),
                f"missing codex skill: {skill}",
                errors,
            )
        check(
            (project_root / ".codex" / "skills" / "project-workflow" / "SKILL.md").is_file(),
            "missing codex project-workflow overlay",
            errors,
        )

        state = json.loads((project_root / ".agent" / "skills_state.json").read_text(encoding="utf-8"))
        overlay_hashes = state.get("overlay_generated_hashes", {})
        check(
            "codex/project-workflow" in overlay_hashes,
            "missing overlay hash for codex/project-workflow",
            errors,
        )

        if errors:
            for error in errors:
                print(f"ERROR: {error}", file=sys.stderr)
            print(f"\n{len(errors)} smoke test error(s).", file=sys.stderr)
            return 1

        overlay_path = project_root / ".codex" / "skills" / "project-workflow" / "SKILL.md"
        overlay_path.write_text(
            overlay_path.read_text(encoding="utf-8") + "\n# local change\n",
            encoding="utf-8",
        )

        run(
            [
                sys.executable,
                str(bootstrap),
                "init",
                "--skillregistry-git",
                str(repo_root),
                "--skillregistry-ref",
                commit,
                "--install-method",
                "local",
            ],
            cwd=project_root,
        )

        overlay_pending = (
            project_root / ".agent" / "overlays_pending" / "codex" / "project-workflow" / "SKILL.md"
        )
        errors = []
        check(
            overlay_pending.is_file(),
            "expected overlays_pending for codex/project-workflow after modification",
            errors,
        )
        check(
            "# local change" in overlay_path.read_text(encoding="utf-8"),
            "modified overlay was overwritten",
            errors,
        )

        overlay_pending_claude = (
            project_root / ".agent" / "overlays_pending" / "claude" / "project-workflow" / "SKILL.md"
        )
        check(
            not overlay_pending_claude.exists(),
            "unexpected overlays_pending for claude/project-workflow",
            errors,
        )

        if errors:
            for error in errors:
                print(f"ERROR: {error}", file=sys.stderr)
            print(f"\n{len(errors)} smoke test error(s).", file=sys.stderr)
            return 1

    print("Bootstrap smoke test passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
