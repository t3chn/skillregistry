#!/usr/bin/env python3
import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


# -------------------- helpers --------------------


KNOWN_TARGETS = {"codex", "claude"}
SUPPORTED_TARGETS = {"codex"}
DEFAULT_REGISTRY_REPO = "t3chn/skillregistry"


def run(cmd: List[str], cwd: Optional[Path] = None) -> str:
    p = subprocess.run(
        cmd,
        cwd=str(cwd) if cwd else None,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    if p.returncode != 0:
        raise RuntimeError(f"Command failed: {' '.join(cmd)}\n{p.stderr.strip()}")
    return p.stdout.strip()


def repo_root() -> Path:
    try:
        out = run(["git", "rev-parse", "--show-toplevel"])
        return Path(out)
    except Exception:
        return Path.cwd()


def ensure_dir(p: Path) -> None:
    p.mkdir(parents=True, exist_ok=True)


def read_text(p: Path) -> str:
    return p.read_text(encoding="utf-8")


def write_text(p: Path, s: str) -> None:
    ensure_dir(p.parent)
    p.write_text(s, encoding="utf-8")


def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def sha256_file(p: Path) -> str:
    return sha256_bytes(p.read_bytes())


def copy_dir(src: Path, dst: Path) -> None:
    if dst.exists():
        shutil.rmtree(dst)
    shutil.copytree(src, dst)


def remove_dir_if_exists(p: Path) -> bool:
    if p.exists():
        shutil.rmtree(p)
        return True
    return False


def exists_any(root: Path, names: List[str]) -> bool:
    return any((root / n).exists() for n in names)


def remove_path(p: Path) -> None:
    if p.is_dir():
        shutil.rmtree(p)
    else:
        p.unlink()


def registry_installer_helper(skillregistry_root: Path) -> Path:
    return skillregistry_root / "scripts" / "install_registry_skills.py"


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug or "proj"


def infer_project_prefix(root: Path) -> str:
    slug = slugify(root.name)
    return slug[:4] if len(slug) >= 4 else slug


def split_targets(targets: List[str]) -> Tuple[List[str], List[str]]:
    supported: List[str] = []
    unsupported: List[str] = []
    for t in targets:
        if t not in KNOWN_TARGETS:
            raise RuntimeError(f"Unknown target: {t}")
        if t in SUPPORTED_TARGETS:
            supported.append(t)
        else:
            unsupported.append(t)
    return supported, unsupported


def prefixed_overlay_name(prefix: str, base_name: str) -> str:
    if not prefix:
        return base_name
    return f"{prefix}-{base_name}"


# -------------------- detection --------------------


@dataclass
class Detected:
    languages: List[str]
    has_docker: bool
    has_github_actions: bool
    apis: List[str]  # e.g. "stripe", "sentry"
    openapi_files: List[str]  # relative paths


def detect_project(root: Path) -> Detected:
    langs: List[str] = []
    if (root / "go.mod").exists():
        langs.append("go")
    if (root / "Cargo.toml").exists():
        langs.append("rust")
    if (root / "pyproject.toml").exists() or (root / "requirements.txt").exists():
        langs.append("python")
    if (root / "package.json").exists():
        langs.append("ts")

    has_docker = exists_any(root, ["Dockerfile", "docker-compose.yml", "compose.yaml"])
    has_gha = (root / ".github" / "workflows").exists()

    api_candidates = set()
    env_files = [root / ".env.example", root / ".env", root / "env.example"]
    for f in env_files:
        if f.exists():
            txt = read_text(f)
            for m in re.finditer(
                r"^([A-Z0-9_]+)_(API_KEY|TOKEN|BASE_URL|API_URL)\s*=",
                txt,
                re.M,
            ):
                prefix = m.group(1).lower().replace("__", "_")
                api_candidates.add(prefix)

    openapi_files: List[str] = []
    for p in root.rglob("*"):
        if p.is_file():
            name = p.name.lower()
            if name in (
                "openapi.json",
                "openapi.yaml",
                "openapi.yml",
                "swagger.json",
                "swagger.yaml",
                "swagger.yml",
            ):
                openapi_files.append(str(p.relative_to(root)))

    return Detected(
        languages=sorted(set(langs)),
        has_docker=has_docker,
        has_github_actions=has_gha,
        apis=sorted(api_candidates),
        openapi_files=openapi_files,
    )


# -------------------- command inference (MVP) --------------------


def infer_commands(root: Path, detected: Detected) -> Dict[str, str]:
    if (root / "Taskfile.yml").exists():
        return {"build": "task build", "test": "task test", "lint": "task lint", "run": "task run"}
    if (root / "justfile").exists():
        return {"build": "just build", "test": "just test", "lint": "just lint", "run": "just run"}
    if (root / "Makefile").exists():
        return {"build": "make build", "test": "make test", "lint": "make lint", "run": "make run"}

    cmds: Dict[str, str] = {}
    if "go" in detected.languages:
        cmds.setdefault("build", "go build ./...")
        cmds.setdefault("test", "go test ./...")
        cmds.setdefault("lint", "golangci-lint run  # TODO: ensure installed")
        cmds.setdefault("run", "go run ./cmd/...  # TODO: adjust")
    if "rust" in detected.languages:
        cmds.setdefault("build", "cargo build")
        cmds.setdefault("test", "cargo test")
        cmds.setdefault("lint", "cargo clippy")
        cmds.setdefault("run", "cargo run")
    if "python" in detected.languages:
        cmds.setdefault("build", "python -m compileall .")
        cmds.setdefault("test", "pytest -q")
        cmds.setdefault("lint", "ruff check .  # TODO: ensure configured")
        cmds.setdefault("run", "python -m your_module  # TODO: adjust")
    if "ts" in detected.languages:
        pm = "npm"
        if (root / "pnpm-lock.yaml").exists():
            pm = "pnpm"
        elif (root / "yarn.lock").exists():
            pm = "yarn"
        cmds.setdefault("build", f"{pm} run build")
        cmds.setdefault("test", f"{pm} test")
        cmds.setdefault("lint", f"{pm} run lint")
        cmds.setdefault("run", f"{pm} run dev")
    return cmds


# -------------------- skill selection --------------------


def load_skillsets(skillregistry_root: Path) -> Dict[str, List[str]]:
    p = skillregistry_root / "catalog" / "skillsets.json"
    if not p.exists():
        return {}
    return json.loads(read_text(p))


def select_registry_skills(detected: Detected, skillsets: Dict[str, List[str]]) -> List[str]:
    selected: List[str] = []
    selected += skillsets.get("baseline", [])

    if "go" in detected.languages:
        selected += skillsets.get("lang_go", [])
    if "rust" in detected.languages:
        selected += skillsets.get("lang_rust", [])
    if "python" in detected.languages:
        selected += skillsets.get("lang_python", [])
    if "ts" in detected.languages:
        selected += skillsets.get("lang_ts", [])

    seen = set()
    out: List[str] = []
    for s in selected:
        if s not in seen:
            seen.add(s)
            out.append(s)
    return out


def normalize_api_name(api: str) -> str:
    return re.sub(r"[^a-z0-9_]+", "_", api).strip("_")


# -------------------- registry clone/update --------------------


def ensure_skillregistry(project_root: Path, git_url: str, ref: str) -> Tuple[Path, str]:
    sr = project_root / ".agent" / "skillregistry"
    ensure_dir(sr.parent)
    if not sr.exists():
        run(["git", "clone", git_url, str(sr)])
    run(["git", "fetch", "--all", "--tags"], cwd=sr)
    run(["git", "checkout", ref], cwd=sr)
    commit = run(["git", "rev-parse", "HEAD"], cwd=sr)
    return sr, commit


# -------------------- state --------------------


def load_prev_state(state_path: Path) -> Dict[str, Any]:
    if not state_path.exists():
        return {}
    try:
        return json.loads(read_text(state_path))
    except Exception:
        return {}


# -------------------- installation & cleanup --------------------


def skill_dst(project_root: Path, target: str, name: str) -> Path:
    if target == "codex":
        return project_root / ".codex" / "skills" / name
    if target == "claude":
        return project_root / ".claude" / "skills" / name
    raise RuntimeError(f"Unknown target: {target}")


def skills_root(project_root: Path, target: str) -> Path:
    if target == "codex":
        return project_root / ".codex" / "skills"
    if target == "claude":
        return project_root / ".claude" / "skills"
    raise RuntimeError(f"Unknown target: {target}")


def clean_stale_registry_skills(
    project_root: Path,
    targets: List[str],
    prev_state: Dict[str, Any],
    selected_skills: List[str],
    cleaned: List[str],
) -> None:
    prev_registry = prev_state.get("registry_skills_installed") or []
    prev_registry = [str(x) for x in prev_registry]

    to_remove = [s for s in prev_registry if s not in selected_skills]
    for s in to_remove:
        for t in targets:
            dst = skill_dst(project_root, t, s)
            if remove_dir_if_exists(dst):
                cleaned.append(f"{t}:{s}")


def parse_registry_installer_summary(raw: str) -> Dict[str, Any]:
    try:
        summary = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"Invalid JSON from install_registry_skills.py: {exc}") from exc
    if not isinstance(summary, dict):
        raise RuntimeError("Invalid JSON from install_registry_skills.py: expected object")
    return summary


def format_registry_installer_failures(failed: List[Dict[str, str]]) -> str:
    parts: List[str] = []
    for entry in failed:
        name = str(entry.get("name", "unknown"))
        reason = str(entry.get("reason", "install failed"))
        parts.append(f"{name}: {reason}")
    return "; ".join(parts)


def install_registry_skills(
    skillregistry_root: Path,
    project_root: Path,
    skills: List[str],
    targets: List[str],
    todo: List[str],
    install_method: str,
    force_overwrite: bool,
    registry_ref: str,
) -> Tuple[List[str], List[Dict[str, str]]]:
    if install_method not in ("skill-installer", "local"):
        raise RuntimeError(f"Unknown install method: {install_method}")

    installed: List[str] = []
    skipped: List[Dict[str, str]] = []
    seen_installed = set()
    available_skills: List[str] = []
    for name in skills:
        src = skillregistry_root / "skills" / name
        if not src.exists():
            todo.append(f"- Missing skill in registry: `{name}` (expected {src})")
            skipped.append({"name": name, "reason": "missing in registry"})
            continue
        available_skills.append(name)

    if not available_skills:
        return installed, skipped

    if install_method == "local":
        for name in available_skills:
            src = skillregistry_root / "skills" / name
            for t in targets:
                dst = skill_dst(project_root, t, name)
                if dst.exists():
                    if not force_overwrite:
                        skipped.append({"name": name, "reason": f"destination exists for {t}"})
                        todo.append(
                            f"- Registry skill `{name}` already exists for {t}; "
                            "not overwriting. Use `--force-overwrite-registry-skills` to replace."
                        )
                        if dst.is_dir() and name not in seen_installed:
                            installed.append(name)
                            seen_installed.add(name)
                        continue
                    remove_path(dst)
                ensure_dir(dst.parent)
                copy_dir(src, dst)
                if name not in seen_installed:
                    installed.append(name)
                    seen_installed.add(name)
        return installed, skipped

    helper = registry_installer_helper(skillregistry_root)
    if not helper.exists():
        raise RuntimeError(
            f"registry installer helper not found at {helper}. "
            "Update the skillregistry clone or rerun with --install-method local."
        )

    for t in targets:
        dest_root = skills_root(project_root, t)
        cmd = [
            sys.executable,
            str(helper),
            "--repo",
            DEFAULT_REGISTRY_REPO,
            "--ref",
            registry_ref,
            "--dest",
            str(dest_root),
            "--json",
        ]
        if force_overwrite:
            cmd.append("--force-overwrite-registry-skills")
        for name in available_skills:
            cmd.extend(["--skill", name])

        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )

        summary: Dict[str, Any] = {"installed": [], "skipped": [], "failed": []}
        stdout = result.stdout.strip()
        if stdout:
            summary = parse_registry_installer_summary(stdout)
        elif result.returncode == 0:
            raise RuntimeError("install_registry_skills.py returned no JSON output")

        failed_entries = summary.get("failed") or []
        if result.returncode != 0 or failed_entries:
            failure_reason = ""
            if failed_entries:
                failure_reason = format_registry_installer_failures(failed_entries)
            elif result.stderr.strip():
                failure_reason = result.stderr.strip()
            else:
                failure_reason = "install failed"
            raise RuntimeError(f"Registry skill install failed for {t}: {failure_reason}")

        for name in summary.get("installed") or []:
            if name not in seen_installed:
                installed.append(name)
                seen_installed.add(name)

        for entry in summary.get("skipped") or []:
            name = str(entry.get("name", "")).strip()
            if not name:
                continue
            reason = str(entry.get("reason", "skipped"))
            if reason == "destination exists":
                reason = f"destination exists for {t}"
                todo.append(
                    f"- Registry skill `{name}` already exists for {t}; "
                    "not overwriting. Use `--force-overwrite-registry-skills` to replace."
                )
                dst = skill_dst(project_root, t, name)
                if dst.is_dir() and name not in seen_installed:
                    installed.append(name)
                    seen_installed.add(name)
            skipped.append({"name": name, "reason": reason})
    return installed, skipped


# -------------------- overlay safe-write policy --------------------


def render_template(skillregistry_root: Path, template_name: str, vars: Dict[str, str]) -> str:
    tp = skillregistry_root / "templates" / template_name
    if not tp.exists():
        raise RuntimeError(f"Template not found: {tp}")
    s = read_text(tp)
    for k, v in vars.items():
        s = s.replace(f"{{{{{k}}}}}", v)
    return s


def set_frontmatter_name(content: str, name: str) -> str:
    lines = content.splitlines()
    if not lines or lines[0].strip() != "---":
        return content
    end = None
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            end = i
            break
    if end is None:
        return content
    name_idx = None
    for i in range(1, end):
        if lines[i].startswith("name:"):
            name_idx = i
            break
    if name_idx is None:
        lines.insert(1, f"name: {name}")
    else:
        lines[name_idx] = f"name: {name}"
    out = "\n".join(lines)
    if content.endswith("\n"):
        out += "\n"
    return out


def find_similar_overlays(project_root: Path, target: str, base_name: str) -> List[str]:
    root = skills_root(project_root, target)
    if not root.exists():
        return []
    matches: List[str] = []
    suffix = f"-{base_name}"
    for entry in root.iterdir():
        if not entry.is_dir():
            continue
        name = entry.name
        if name == base_name or name.endswith(suffix):
            matches.append(name)
    return matches


def overlay_key(target: str, overlay_name: str) -> str:
    return f"{target}/{overlay_name}"


def safe_write_overlay(
    project_root: Path,
    target: str,
    overlay_name: str,
    new_content: str,
    prev_generated_hashes: Dict[str, str],
    new_generated_hashes: Dict[str, str],
    todo: List[str],
    force: bool,
    adopt_existing: bool,
) -> None:
    dst_dir = skill_dst(project_root, target, overlay_name)
    dst_file = dst_dir / "SKILL.md"
    ensure_dir(dst_dir)

    key = overlay_key(target, overlay_name)
    prev_gen = prev_generated_hashes.get(key)

    if not dst_file.exists():
        write_text(dst_file, new_content)
        new_generated_hashes[key] = sha256_file(dst_file)
        return

    if force:
        backup = dst_dir / "SKILL.md.bootstrap.bak"
        write_text(backup, read_text(dst_file))
        write_text(dst_file, new_content)
        new_generated_hashes[key] = sha256_file(dst_file)
        todo.append(f"- Overlay `{key}` overwritten due to --force-overwrite-overlays (backup: `{backup}`)")
        return

    if not prev_gen:
        if adopt_existing:
            new_generated_hashes[key] = sha256_file(dst_file)
            todo.append(f"- Overlay `{key}` adopted as baseline (will auto-update only if unmodified later).")
            return

        pending = project_root / ".agent" / "overlays_pending" / target / overlay_name / "SKILL.md"
        write_text(pending, new_content)
        todo.append(
            f"- Overlay `{key}` exists but has no generation history; not overwriting. "
            f"New candidate written to `{pending}`. "
            f"If you want auto-updates, rerun with `--adopt-existing-overlays`."
        )
        return

    current_hash = sha256_file(dst_file)
    if current_hash == prev_gen:
        write_text(dst_file, new_content)
        new_generated_hashes[key] = sha256_file(dst_file)
        return

    pending = project_root / ".agent" / "overlays_pending" / target / overlay_name / "SKILL.md"
    write_text(pending, new_content)
    new_generated_hashes[key] = prev_gen
    todo.append(
        f"- Overlay `{key}` was modified; not overwriting. "
        f"New candidate written to `{pending}` (merge manually)."
    )


def generate_project_workflow(
    skillregistry_root: Path,
    project_root: Path,
    targets: List[str],
    commands: Dict[str, str],
    todo: List[str],
    prev_generated_hashes: Dict[str, str],
    new_generated_hashes: Dict[str, str],
    force_overwrite: bool,
    adopt_existing: bool,
    project_prefix: str,
    force_create_overlays: bool,
    prefix_changed: bool,
    prev_prefix: Optional[str],
    overlays_skipped: List[Dict[str, str]],
) -> None:
    required = ["build", "test", "lint", "run"]
    for r in required:
        if r not in commands or "TODO" in commands[r]:
            todo.append(
                f"- Verify command `{r}` in project-workflow (auto-inferred: `{commands.get(r, '<missing>')}`)"
            )

    base_name = "project-workflow"
    body = render_template(
        skillregistry_root,
        "project-workflow.SKILL.template.md",
        {
            "BUILD_CMD": commands.get("build", "TODO"),
            "TEST_CMD": commands.get("test", "TODO"),
            "LINT_CMD": commands.get("lint", "TODO"),
            "RUN_CMD": commands.get("run", "TODO"),
        },
    )

    for t in targets:
        overlay_name = prefixed_overlay_name(project_prefix, base_name)
        body_with_name = set_frontmatter_name(body, overlay_name)
        dst_dir = skill_dst(project_root, t, overlay_name)
        similar = [name for name in find_similar_overlays(project_root, t, base_name) if name != overlay_name]
        if not dst_dir.exists() and similar and not force_create_overlays and not prefix_changed:
            reason = f"similar overlay exists: {', '.join(similar)}"
            overlays_skipped.append({"name": f"{t}/{overlay_name}", "reason": reason})
            todo.append(
                f"- Overlay `{t}/{overlay_name}` skipped because similar overlay exists: {', '.join(similar)}. "
                "Use `--force-create-overlays` to create anyway."
            )
            continue
        if prefix_changed and similar:
            prev = prev_prefix or "<unknown>"
            todo.append(
                f"- Overlay prefix changed from `{prev}` to `{project_prefix}` for `{t}/{base_name}`; "
                f"existing overlays not renamed: {', '.join(similar)}. Review/migrate manually."
            )
        safe_write_overlay(
            project_root=project_root,
            target=t,
            overlay_name=overlay_name,
            new_content=body_with_name,
            prev_generated_hashes=prev_generated_hashes,
            new_generated_hashes=new_generated_hashes,
            todo=todo,
            force=force_overwrite,
            adopt_existing=adopt_existing,
        )


def generate_api_skeletons(
    skillregistry_root: Path,
    project_root: Path,
    targets: List[str],
    detected: Detected,
    todo: List[str],
    prev_generated_hashes: Dict[str, str],
    new_generated_hashes: Dict[str, str],
    force_overwrite: bool,
    adopt_existing: bool,
    project_prefix: str,
    force_create_overlays: bool,
    prefix_changed: bool,
    prev_prefix: Optional[str],
    overlays_skipped: List[Dict[str, str]],
) -> None:
    if detected.openapi_files:
        todo.append("- Found OpenAPI/Swagger files:\n  " + "\n  ".join([f"* `{p}`" for p in detected.openapi_files]))

    for api in detected.apis:
        name = normalize_api_name(api)
        if not name:
            continue

        base_name = f"api-{name}"
        overlay_name = prefixed_overlay_name(project_prefix, base_name)
        body = render_template(skillregistry_root, "api-skeleton.SKILL.template.md", {"API_NAME": name})
        created_any = False

        for t in targets:
            body_with_name = set_frontmatter_name(body, overlay_name)
            dst_dir = skill_dst(project_root, t, overlay_name)
            similar = [s for s in find_similar_overlays(project_root, t, base_name) if s != overlay_name]
            if not dst_dir.exists() and similar and not force_create_overlays and not prefix_changed:
                reason = f"similar overlay exists: {', '.join(similar)}"
                overlays_skipped.append({"name": f"{t}/{overlay_name}", "reason": reason})
                todo.append(
                    f"- Overlay `{t}/{overlay_name}` skipped because similar overlay exists: {', '.join(similar)}. "
                    "Use `--force-create-overlays` to create anyway."
                )
                continue
            if prefix_changed and similar:
                prev = prev_prefix or "<unknown>"
                todo.append(
                    f"- Overlay prefix changed from `{prev}` to `{project_prefix}` for `{t}/{base_name}`; "
                    f"existing overlays not renamed: {', '.join(similar)}. Review/migrate manually."
                )
            ensure_dir(dst_dir / "references")

            safe_write_overlay(
                project_root=project_root,
                target=t,
                overlay_name=overlay_name,
                new_content=body_with_name,
                prev_generated_hashes=prev_generated_hashes,
                new_generated_hashes=new_generated_hashes,
                todo=todo,
                force=force_overwrite,
                adopt_existing=adopt_existing,
            )
            created_any = True

            ref_todo = dst_dir / "references" / "TODO.md"
            if not ref_todo.exists():
                write_text(
                    ref_todo,
                    "Fill: base_url, auth method, endpoints, rate limits, idempotency rules, errors.\n",
                )

        if created_any:
            todo.append(f"- API skill overlay ensured: `{overlay_name}` (needs docs/scheme enrichment)")


# -------------------- entrypoint --------------------


def main() -> int:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)

    init = sub.add_parser("init")
    init.add_argument("--targets", default="codex,claude", help="comma-separated: codex,claude")
    init.add_argument(
        "--skillregistry-git",
        default=os.environ.get("SKILLREGISTRY_GIT", ""),
        help="git url or local path (or env SKILLREGISTRY_GIT)",
    )
    init.add_argument(
        "--skillregistry-ref",
        default=os.environ.get("SKILLREGISTRY_REF", "main"),
        help="branch/tag/commit (or env SKILLREGISTRY_REF)",
    )
    init.add_argument(
        "--install-method",
        choices=["skill-installer", "local"],
        default="skill-installer",
        help="install registry skills via skill-installer (default) or local copy",
    )
    init.add_argument(
        "--force-overwrite-registry-skills",
        action="store_true",
        help="overwrite registry skills even if they already exist",
    )
    init.add_argument(
        "--force-overwrite-overlays",
        action="store_true",
        help="overwrite overlays even if modified (writes backup)",
    )
    init.add_argument(
        "--force-create-overlays",
        action="store_true",
        help="create overlays even if similar overlays already exist",
    )
    init.add_argument(
        "--adopt-existing-overlays",
        action="store_true",
        help="if overlay exists but has no generation history, adopt current as baseline",
    )
    init.add_argument(
        "--project-prefix",
        default="",
        help="override project prefix used for overlays",
    )
    init.add_argument(
        "--no-clean-stale-registry-skills",
        action="store_true",
        help="do not remove previously installed registry skills that are no longer selected",
    )

    args = ap.parse_args()
    root = repo_root()
    ensure_dir(root / ".agent")
    ensure_dir(root / ".codex" / "skills")
    ensure_dir(root / ".claude" / "skills")

    targets = [t.strip() for t in args.targets.split(",") if t.strip()]
    supported_targets, unsupported_targets = split_targets(targets)

    if not args.skillregistry_git:
        raise RuntimeError("Missing --skillregistry-git (or env SKILLREGISTRY_GIT)")

    state_path = root / ".agent" / "skills_state.json"
    prev_state = load_prev_state(state_path)
    prev_prefix = prev_state.get("project_prefix")
    if prev_prefix is not None:
        prev_prefix = str(prev_prefix)
    project_prefix = args.project_prefix or prev_prefix or infer_project_prefix(root)
    prefix_changed = prev_prefix is not None and prev_prefix != project_prefix

    sr_root, sr_commit = ensure_skillregistry(root, args.skillregistry_git, args.skillregistry_ref)

    detected = detect_project(root)
    commands = infer_commands(root, detected)
    skillsets = load_skillsets(sr_root)
    registry_skills_selected = select_registry_skills(detected, skillsets)

    todo: List[str] = []
    cleaned: List[str] = []
    if unsupported_targets:
        for t in unsupported_targets:
            todo.append(f"- Target `{t}` is not supported yet; skipping registry installs and overlays.")

    if not args.no_clean_stale_registry_skills and supported_targets:
        clean_stale_registry_skills(root, supported_targets, prev_state, registry_skills_selected, cleaned)

    registry_skills_installed: List[str] = []
    registry_skills_skipped: List[Dict[str, str]] = []
    if supported_targets:
        registry_skills_installed, registry_skills_skipped = install_registry_skills(
            sr_root,
            root,
            registry_skills_selected,
            supported_targets,
            todo,
            install_method=args.install_method,
            force_overwrite=args.force_overwrite_registry_skills,
            registry_ref=args.skillregistry_ref,
        )

    prev_gen_hashes: Dict[str, str] = prev_state.get("overlay_generated_hashes") or {}
    prev_gen_hashes = {str(k): str(v) for k, v in prev_gen_hashes.items()}

    new_gen_hashes: Dict[str, str] = dict(prev_gen_hashes)
    overlays_skipped: List[Dict[str, str]] = []
    if unsupported_targets:
        for t in unsupported_targets:
            pw_name = prefixed_overlay_name(project_prefix, "project-workflow")
            overlays_skipped.append({"name": f"{t}/{pw_name}", "reason": "unsupported target"})
            for api in detected.apis:
                name = normalize_api_name(api)
                if name:
                    api_name = prefixed_overlay_name(project_prefix, f"api-{name}")
                    overlays_skipped.append({"name": f"{t}/{api_name}", "reason": "unsupported target"})

    if supported_targets:
        generate_project_workflow(
            skillregistry_root=sr_root,
            project_root=root,
            targets=supported_targets,
            commands=commands,
            todo=todo,
            prev_generated_hashes=prev_gen_hashes,
            new_generated_hashes=new_gen_hashes,
            force_overwrite=args.force_overwrite_overlays,
            adopt_existing=args.adopt_existing_overlays,
            project_prefix=project_prefix,
            force_create_overlays=args.force_create_overlays,
            prefix_changed=prefix_changed,
            prev_prefix=prev_prefix,
            overlays_skipped=overlays_skipped,
        )

        if detected.apis or detected.openapi_files:
            generate_api_skeletons(
                skillregistry_root=sr_root,
                project_root=root,
                targets=supported_targets,
                detected=detected,
                todo=todo,
                prev_generated_hashes=prev_gen_hashes,
                new_generated_hashes=new_gen_hashes,
                force_overwrite=args.force_overwrite_overlays,
                adopt_existing=args.adopt_existing_overlays,
                project_prefix=project_prefix,
                force_create_overlays=args.force_create_overlays,
                prefix_changed=prefix_changed,
                prev_prefix=prev_prefix,
                overlays_skipped=overlays_skipped,
            )

    profile = {
        "repo_root": str(root),
        "detected": {
            "languages": detected.languages,
            "has_docker": detected.has_docker,
            "has_github_actions": detected.has_github_actions,
            "apis": detected.apis,
            "openapi_files": detected.openapi_files,
        },
        "inferred_commands": commands,
    }
    write_text(root / ".agent" / "project_profile.json", json.dumps(profile, indent=2, ensure_ascii=False) + "\n")

    state = {
        "skillregistry": {"git": args.skillregistry_git, "ref": args.skillregistry_ref, "commit": sr_commit},
        "targets": targets,
        "project_prefix": project_prefix,
        "install_method": args.install_method,
        "registry_skills_selected": registry_skills_selected,
        "registry_skills_installed": registry_skills_installed,
        "registry_skills_skipped": registry_skills_skipped,
        "unsupported_targets": unsupported_targets,
        "overlays_skipped": overlays_skipped,
        "cleaned_registry_skills": cleaned,
        "overlay_generated_hashes": new_gen_hashes,
    }
    write_text(state_path, json.dumps(state, indent=2, ensure_ascii=False) + "\n")

    write_text(
        root / ".agent" / "skills_todo.md",
        "# TODO after bootstrap\n\n" + ("\n".join(todo) if todo else "(no todo)") + "\n",
    )

    print("Bootstrap complete.")
    print("Next:")
    print("- Review .agent/skills_todo.md")
    print("- Restart Codex CLI to reload skills (recommended).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
