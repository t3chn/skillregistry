import json
import subprocess
import sys
from pathlib import Path
from typing import List, Optional

from helpers import (
    bootstrap_path,
    commit_all,
    create_registry,
    init_git_repo,
    load_bootstrap_module,
    write_json,
    write_text,
)


def run_bootstrap(
    project_root: Path,
    registry_root: Path,
    ref: str,
    extra_args: Optional[List[str]] = None,
) -> subprocess.CompletedProcess:
    cmd = [
        sys.executable,
        str(bootstrap_path()),
        "init",
        "--skillregistry-git",
        str(registry_root),
        "--skillregistry-ref",
        ref,
        "--install-method",
        "local",
    ]
    if extra_args:
        cmd.extend(extra_args)
    return subprocess.run(
        cmd,
        cwd=str(project_root),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )


def test_bootstrap_empty_project_creates_basics(tmp_path: Path) -> None:
    registry = tmp_path / "registry"
    skillsets = {"baseline": ["base-a", "base-b"]}
    commit = create_registry(registry, skillsets)

    project = tmp_path / "project"
    project.mkdir()
    init_git_repo(project)

    result = run_bootstrap(project, registry, commit)
    assert result.returncode == 0, result.stderr

    assert (project / ".agent" / "skillregistry").is_dir()
    assert (project / ".agent" / "project_profile.json").is_file()
    assert (project / ".agent" / "skills_state.json").is_file()
    assert (project / ".agent" / "skills_todo.md").is_file()

    state = json.loads((project / ".agent" / "skills_state.json").read_text(encoding="utf-8"))
    assert state["registry_skills_installed"] == ["base-a", "base-b"]
    assert state["unsupported_targets"] == ["claude"]

    assert (project / ".codex" / "skills" / "base-a" / "SKILL.md").is_file()
    overlay = project / ".codex" / "skills" / "project-workflow" / "SKILL.md"
    assert overlay.is_file()
    assert "TODO" in overlay.read_text(encoding="utf-8")
    assert not (project / ".claude" / "skills" / "base-a" / "SKILL.md").exists()

    todo = (project / ".agent" / "skills_todo.md").read_text(encoding="utf-8")
    assert "Verify command `build`" in todo
    assert "Target `claude` is not supported yet" in todo


def test_bootstrap_python_project_and_api_overlay(tmp_path: Path) -> None:
    registry = tmp_path / "registry"
    skillsets = {"baseline": ["base-a"], "lang_python": ["lang-python"]}
    commit = create_registry(registry, skillsets)

    project = tmp_path / "project"
    project.mkdir()
    init_git_repo(project)
    (project / "pyproject.toml").write_text("[project]\nname = 'demo'\n", encoding="utf-8")
    (project / ".env.example").write_text("STRIPE_API_KEY=abc\n", encoding="utf-8")

    result = run_bootstrap(project, registry, commit)
    assert result.returncode == 0, result.stderr

    assert (project / ".codex" / "skills" / "lang-python" / "SKILL.md").is_file()
    workflow = project / ".codex" / "skills" / "project-workflow" / "SKILL.md"
    assert "pytest -q" in workflow.read_text(encoding="utf-8")
    api_overlay = project / ".codex" / "skills" / "api-stripe" / "SKILL.md"
    assert api_overlay.is_file()
    ref_todo = project / ".codex" / "skills" / "api-stripe" / "references" / "TODO.md"
    assert ref_todo.is_file()
    assert not (project / ".claude" / "skills" / "lang-python" / "SKILL.md").exists()


def test_overlay_pending_when_modified(tmp_path: Path) -> None:
    registry = tmp_path / "registry"
    skillsets = {"baseline": ["base-a"]}
    commit = create_registry(registry, skillsets)

    project = tmp_path / "project"
    project.mkdir()
    init_git_repo(project)

    first = run_bootstrap(project, registry, commit)
    assert first.returncode == 0, first.stderr

    overlay = project / ".codex" / "skills" / "project-workflow" / "SKILL.md"
    overlay.write_text(overlay.read_text(encoding="utf-8") + "\n# local change\n", encoding="utf-8")

    second = run_bootstrap(project, registry, commit)
    assert second.returncode == 0, second.stderr

    pending = project / ".agent" / "overlays_pending" / "codex" / "project-workflow" / "SKILL.md"
    assert pending.is_file()
    assert "# local change" in overlay.read_text(encoding="utf-8")

    claude_pending = project / ".agent" / "overlays_pending" / "claude" / "project-workflow" / "SKILL.md"
    assert not claude_pending.exists()


def test_existing_overlay_without_adopt_writes_pending(tmp_path: Path) -> None:
    registry = tmp_path / "registry"
    skillsets = {"baseline": ["base-a"]}
    commit = create_registry(registry, skillsets)

    project = tmp_path / "project"
    project.mkdir()
    init_git_repo(project)
    existing = project / ".codex" / "skills" / "project-workflow" / "SKILL.md"
    write_text(existing, "existing")

    result = run_bootstrap(project, registry, commit)
    assert result.returncode == 0, result.stderr

    pending = project / ".agent" / "overlays_pending" / "codex" / "project-workflow" / "SKILL.md"
    assert pending.is_file()
    assert existing.read_text(encoding="utf-8") == "existing"


def test_adopt_existing_overlay_sets_hash(tmp_path: Path) -> None:
    registry = tmp_path / "registry"
    skillsets = {"baseline": ["base-a"]}
    commit = create_registry(registry, skillsets)

    project = tmp_path / "project"
    project.mkdir()
    init_git_repo(project)
    existing = project / ".codex" / "skills" / "project-workflow" / "SKILL.md"
    write_text(existing, "existing")

    result = run_bootstrap(project, registry, commit, ["--adopt-existing-overlays"])
    assert result.returncode == 0, result.stderr

    pending = project / ".agent" / "overlays_pending" / "codex" / "project-workflow" / "SKILL.md"
    assert not pending.exists()

    state = json.loads((project / ".agent" / "skills_state.json").read_text(encoding="utf-8"))
    module = load_bootstrap_module()
    expected_hash = module.sha256_file(existing)
    assert state["overlay_generated_hashes"]["codex/project-workflow"] == expected_hash


def test_stale_registry_skills_cleanup(tmp_path: Path) -> None:
    registry = tmp_path / "registry"
    skillsets = {"baseline": ["base-a", "base-b"]}
    commit = create_registry(registry, skillsets)

    project = tmp_path / "project"
    project.mkdir()
    init_git_repo(project)

    first = run_bootstrap(project, registry, commit)
    assert first.returncode == 0, first.stderr

    write_json(registry / "catalog" / "skillsets.json", {"baseline": ["base-b"]})
    commit2 = commit_all(registry, "drop base-a")

    second = run_bootstrap(project, registry, commit2)
    assert second.returncode == 0, second.stderr

    assert not (project / ".codex" / "skills" / "base-a").exists()
    assert (project / ".codex" / "skills" / "base-b").is_dir()


def test_no_clean_stale_registry_skills(tmp_path: Path) -> None:
    registry = tmp_path / "registry"
    skillsets = {"baseline": ["base-a", "base-b"]}
    commit = create_registry(registry, skillsets)

    project = tmp_path / "project"
    project.mkdir()
    init_git_repo(project)

    first = run_bootstrap(project, registry, commit)
    assert first.returncode == 0, first.stderr

    write_json(registry / "catalog" / "skillsets.json", {"baseline": ["base-b"]})
    commit2 = commit_all(registry, "drop base-a")

    second = run_bootstrap(project, registry, commit2, ["--no-clean-stale-registry-skills"])
    assert second.returncode == 0, second.stderr

    assert (project / ".codex" / "skills" / "base-a").is_dir()
    assert (project / ".codex" / "skills" / "base-b").is_dir()


def test_missing_skillregistry_git_errors(tmp_path: Path) -> None:
    project = tmp_path / "project"
    project.mkdir()
    init_git_repo(project)

    result = subprocess.run(
        [sys.executable, str(bootstrap_path()), "init"],
        cwd=str(project),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    assert result.returncode != 0
    assert "Missing --skillregistry-git" in result.stderr


def test_invalid_targets_error(tmp_path: Path) -> None:
    registry = tmp_path / "registry"
    skillsets = {"baseline": ["base-a"]}
    commit = create_registry(registry, skillsets)

    project = tmp_path / "project"
    project.mkdir()
    init_git_repo(project)

    result = run_bootstrap(project, registry, commit, ["--targets", "codex,invalid"])
    assert result.returncode != 0
    assert "Unknown target: invalid" in result.stderr


def test_missing_template_fails(tmp_path: Path) -> None:
    registry = tmp_path / "registry"
    skillsets = {"baseline": ["base-a"]}
    commit = create_registry(registry, skillsets, template_names=["api-skeleton.SKILL.template.md"])

    project = tmp_path / "project"
    project.mkdir()
    init_git_repo(project)

    result = run_bootstrap(project, registry, commit)
    assert result.returncode != 0
    assert "Template not found" in result.stderr
