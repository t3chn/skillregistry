from pathlib import Path

from helpers import load_bootstrap_module


def test_infer_commands_taskfile_precedence(tmp_path: Path) -> None:
    module = load_bootstrap_module()

    (tmp_path / "Taskfile.yml").write_text("version: '3'\n", encoding="utf-8")
    detected = module.Detected(
        languages=["python"],
        has_docker=False,
        has_github_actions=False,
        apis=[],
        openapi_files=[],
    )

    commands = module.infer_commands(tmp_path, detected)

    assert commands == {
        "build": "task build",
        "test": "task test",
        "lint": "task lint",
        "run": "task run",
    }


def test_infer_commands_uses_package_manager(tmp_path: Path) -> None:
    module = load_bootstrap_module()

    (tmp_path / "pnpm-lock.yaml").write_text("lockfileVersion: 5.4\n", encoding="utf-8")
    detected = module.Detected(
        languages=["ts"],
        has_docker=False,
        has_github_actions=False,
        apis=[],
        openapi_files=[],
    )

    commands = module.infer_commands(tmp_path, detected)

    assert commands["build"] == "pnpm run build"
    assert commands["test"] == "pnpm test"
    assert commands["lint"] == "pnpm run lint"
    assert commands["run"] == "pnpm run dev"
