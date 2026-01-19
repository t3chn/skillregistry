from pathlib import Path

from helpers import load_bootstrap_module


def test_safe_write_overlay_new_file(tmp_path: Path) -> None:
    module = load_bootstrap_module()
    prev_gen = {}
    new_gen = {}
    todo = []

    module.safe_write_overlay(
        project_root=tmp_path,
        target="codex",
        overlay_name="project-workflow",
        new_content="new-content",
        prev_generated_hashes=prev_gen,
        new_generated_hashes=new_gen,
        todo=todo,
        force=False,
        adopt_existing=False,
    )

    dst_file = tmp_path / ".codex" / "skills" / "project-workflow" / "SKILL.md"
    assert dst_file.read_text(encoding="utf-8") == "new-content"
    assert "codex/project-workflow" in new_gen


def test_safe_write_overlay_no_history_writes_pending(tmp_path: Path) -> None:
    module = load_bootstrap_module()
    dst_file = tmp_path / ".codex" / "skills" / "project-workflow" / "SKILL.md"
    dst_file.parent.mkdir(parents=True, exist_ok=True)
    dst_file.write_text("existing", encoding="utf-8")

    prev_gen = {}
    new_gen = {}
    todo = []

    module.safe_write_overlay(
        project_root=tmp_path,
        target="codex",
        overlay_name="project-workflow",
        new_content="new-content",
        prev_generated_hashes=prev_gen,
        new_generated_hashes=new_gen,
        todo=todo,
        force=False,
        adopt_existing=False,
    )

    pending = tmp_path / ".agent" / "overlays_pending" / "codex" / "project-workflow" / "SKILL.md"
    assert pending.read_text(encoding="utf-8") == "new-content"
    assert dst_file.read_text(encoding="utf-8") == "existing"
    assert "codex/project-workflow" not in new_gen
    assert any("no generation history" in item for item in todo)


def test_safe_write_overlay_adopt_existing(tmp_path: Path) -> None:
    module = load_bootstrap_module()
    dst_file = tmp_path / ".codex" / "skills" / "project-workflow" / "SKILL.md"
    dst_file.parent.mkdir(parents=True, exist_ok=True)
    dst_file.write_text("existing", encoding="utf-8")

    prev_gen = {}
    new_gen = {}
    todo = []

    module.safe_write_overlay(
        project_root=tmp_path,
        target="codex",
        overlay_name="project-workflow",
        new_content="new-content",
        prev_generated_hashes=prev_gen,
        new_generated_hashes=new_gen,
        todo=todo,
        force=False,
        adopt_existing=True,
    )

    pending = tmp_path / ".agent" / "overlays_pending" / "codex" / "project-workflow" / "SKILL.md"
    assert not pending.exists()
    assert dst_file.read_text(encoding="utf-8") == "existing"
    assert new_gen["codex/project-workflow"] == module.sha256_file(dst_file)
    assert any("adopted as baseline" in item for item in todo)


def test_safe_write_overlay_overwrites_when_unchanged(tmp_path: Path) -> None:
    module = load_bootstrap_module()
    dst_file = tmp_path / ".codex" / "skills" / "project-workflow" / "SKILL.md"
    dst_file.parent.mkdir(parents=True, exist_ok=True)
    dst_file.write_text("original", encoding="utf-8")

    prev_gen = {"codex/project-workflow": module.sha256_file(dst_file)}
    new_gen = dict(prev_gen)
    todo = []

    module.safe_write_overlay(
        project_root=tmp_path,
        target="codex",
        overlay_name="project-workflow",
        new_content="updated",
        prev_generated_hashes=prev_gen,
        new_generated_hashes=new_gen,
        todo=todo,
        force=False,
        adopt_existing=False,
    )

    assert dst_file.read_text(encoding="utf-8") == "updated"
    assert new_gen["codex/project-workflow"] == module.sha256_file(dst_file)


def test_safe_write_overlay_modified_writes_pending(tmp_path: Path) -> None:
    module = load_bootstrap_module()
    dst_file = tmp_path / ".codex" / "skills" / "project-workflow" / "SKILL.md"
    dst_file.parent.mkdir(parents=True, exist_ok=True)
    dst_file.write_text("modified", encoding="utf-8")

    prev_gen = {"codex/project-workflow": module.sha256_bytes(b"original")}
    new_gen = dict(prev_gen)
    todo = []

    module.safe_write_overlay(
        project_root=tmp_path,
        target="codex",
        overlay_name="project-workflow",
        new_content="new-content",
        prev_generated_hashes=prev_gen,
        new_generated_hashes=new_gen,
        todo=todo,
        force=False,
        adopt_existing=False,
    )

    pending = tmp_path / ".agent" / "overlays_pending" / "codex" / "project-workflow" / "SKILL.md"
    assert pending.read_text(encoding="utf-8") == "new-content"
    assert dst_file.read_text(encoding="utf-8") == "modified"
    assert new_gen["codex/project-workflow"] == prev_gen["codex/project-workflow"]
    assert any("was modified" in item for item in todo)


def test_safe_write_overlay_force_overwrite(tmp_path: Path) -> None:
    module = load_bootstrap_module()
    dst_dir = tmp_path / ".codex" / "skills" / "project-workflow"
    dst_dir.mkdir(parents=True, exist_ok=True)
    dst_file = dst_dir / "SKILL.md"
    dst_file.write_text("original", encoding="utf-8")

    prev_gen = {"codex/project-workflow": module.sha256_file(dst_file)}
    new_gen = dict(prev_gen)
    todo = []

    module.safe_write_overlay(
        project_root=tmp_path,
        target="codex",
        overlay_name="project-workflow",
        new_content="forced",
        prev_generated_hashes=prev_gen,
        new_generated_hashes=new_gen,
        todo=todo,
        force=True,
        adopt_existing=False,
    )

    backup = dst_dir / "SKILL.md.bootstrap.bak"
    assert backup.read_text(encoding="utf-8") == "original"
    assert dst_file.read_text(encoding="utf-8") == "forced"
    assert new_gen["codex/project-workflow"] == module.sha256_file(dst_file)
    assert any("force-overwrite-overlays" in item for item in todo)
