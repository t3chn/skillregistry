from pathlib import Path

from helpers import load_bootstrap_module


def test_detect_project_languages_flags_and_apis(tmp_path: Path) -> None:
    module = load_bootstrap_module()

    (tmp_path / "go.mod").write_text("module example\n", encoding="utf-8")
    (tmp_path / "Cargo.toml").write_text("[package]\nname = 'x'\n", encoding="utf-8")
    (tmp_path / "pyproject.toml").write_text("[project]\nname = 'x'\n", encoding="utf-8")
    (tmp_path / "package.json").write_text("{}\n", encoding="utf-8")
    (tmp_path / "Dockerfile").write_text("FROM scratch\n", encoding="utf-8")
    (tmp_path / ".github" / "workflows").mkdir(parents=True)

    env_file = tmp_path / ".env.example"
    env_file.write_text("STRIPE_API_KEY=abc\nFOO__BAR_TOKEN=xyz\n", encoding="utf-8")

    (tmp_path / "openapi.yaml").write_text("openapi: 3.0.0\n", encoding="utf-8")

    detected = module.detect_project(tmp_path)

    assert detected.languages == ["go", "python", "rust", "ts"]
    assert detected.has_docker is True
    assert detected.has_github_actions is True
    assert "stripe" in detected.apis
    assert "foo_bar" in detected.apis
    assert set(detected.openapi_files) == {"openapi.yaml"}
