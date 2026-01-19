import importlib.util
import json
import subprocess
from pathlib import Path
from typing import Dict, Iterable, List, Optional


def repo_root() -> Path:
    path = Path(__file__).resolve()
    for parent in path.parents:
        bootstrap = parent / "skills" / "project-bootstrap" / "scripts" / "bootstrap.py"
        if bootstrap.is_file():
            return parent
    raise RuntimeError("Could not locate repository root")


def bootstrap_path() -> Path:
    return repo_root() / "skills" / "project-bootstrap" / "scripts" / "bootstrap.py"


def load_bootstrap_module():
    path = bootstrap_path()
    spec = importlib.util.spec_from_file_location("bootstrap", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to import bootstrap module from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def run(cmd: List[str], cwd: Optional[Path] = None, env: Optional[Dict[str, str]] = None) -> str:
    result = subprocess.run(
        cmd,
        cwd=str(cwd) if cwd else None,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"Command failed: {' '.join(cmd)}\nstdout:\n{result.stdout}\nstderr:\n{result.stderr}"
        )
    return result.stdout.strip()


def init_git_repo(root: Path) -> None:
    run(["git", "init"], cwd=root)
    run(["git", "config", "user.email", "tests@example.com"], cwd=root)
    run(["git", "config", "user.name", "Tests"], cwd=root)


def commit_all(root: Path, message: str) -> str:
    run(["git", "add", "."], cwd=root)
    run(["git", "commit", "-m", message], cwd=root)
    return run(["git", "rev-parse", "HEAD"], cwd=root)


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def write_json(path: Path, payload: Dict) -> None:
    write_text(path, json.dumps(payload, indent=2, ensure_ascii=False) + "\n")


def create_skill(root: Path, name: str, description: str = "test") -> None:
    content = "---\n" f"name: {name}\n" f"description: {description}\n" "---\n\n"
    write_text(root / "skills" / name / "SKILL.md", content)


def create_registry(
    root: Path,
    skillsets: Dict[str, List[str]],
    template_names: Optional[Iterable[str]] = None,
) -> str:
    (root / "skills").mkdir(parents=True, exist_ok=True)
    (root / "catalog").mkdir(parents=True, exist_ok=True)

    all_skills = set()
    for skills in skillsets.values():
        all_skills.update(skills)
    for skill in sorted(all_skills):
        create_skill(root, skill)

    write_json(root / "catalog" / "skillsets.json", skillsets)

    if template_names is None:
        template_names = [
            "project-workflow.SKILL.template.md",
            "api-skeleton.SKILL.template.md",
        ]

    template_set = set(template_names)
    if template_set:
        (root / "templates").mkdir(parents=True, exist_ok=True)

    if "project-workflow.SKILL.template.md" in template_set:
        write_text(
            root / "templates" / "project-workflow.SKILL.template.md",
            "---\n"
            "name: project-workflow\n"
            "description: test\n"
            "---\n"
            "Build: {{BUILD_CMD}}\n"
            "Test: {{TEST_CMD}}\n"
            "Lint: {{LINT_CMD}}\n"
            "Run: {{RUN_CMD}}\n",
        )

    if "api-skeleton.SKILL.template.md" in template_set:
        write_text(
            root / "templates" / "api-skeleton.SKILL.template.md",
            "---\n"
            "name: api-{{API_NAME}}\n"
            "description: test\n"
            "---\n"
            "API: {{API_NAME}}\n",
        )

    init_git_repo(root)
    return commit_all(root, "init")
