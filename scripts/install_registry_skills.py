#!/usr/bin/env python3
import argparse
import json
import os
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional


DEFAULT_REPO = "t3chn/skillregistry"
DEFAULT_REF = "main"
DEFAULT_METHOD = "auto"


@dataclass
class InstallItem:
    name: str
    path: str


def skill_installer_script() -> Path:
    codex_home = os.environ.get("CODEX_HOME") or str(Path.home() / ".codex")
    return Path(codex_home) / "skills" / ".system" / "skill-installer" / "scripts" / "install-skill-from-github.py"


def remove_path(path: Path) -> None:
    if path.is_dir():
        shutil.rmtree(path)
    else:
        path.unlink()


def normalize_skill_name(name: str) -> Optional[str]:
    altsep = os.path.altsep
    if not name:
        return None
    if os.path.sep in name or (altsep and altsep in name):
        return None
    if name in (".", ".."):
        return None
    return name


def build_items(skills: List[str], paths: List[str]) -> List[InstallItem]:
    items: List[InstallItem] = []
    for skill in skills:
        normalized = normalize_skill_name(skill)
        if not normalized:
            raise RuntimeError(f"Invalid skill name: {skill}")
        items.append(InstallItem(name=normalized, path=f"skills/{normalized}"))
    for raw in paths:
        path = raw.strip()
        if not path:
            continue
        name = Path(path).name
        if not name:
            raise RuntimeError(f"Unable to derive skill name from path: {raw}")
        items.append(InstallItem(name=name, path=path))
    return items


def format_summary(installed: List[str], skipped: List[Dict[str, str]], failed: List[Dict[str, str]]) -> str:
    summary = {
        "installed": installed,
        "skipped": skipped,
        "failed": failed,
    }
    return json.dumps(summary, indent=2, ensure_ascii=True)


def main() -> int:
    parser = argparse.ArgumentParser(description="Install registry skills via system skill-installer.")
    parser.add_argument("--repo", default=DEFAULT_REPO, help="GitHub repo in owner/repo format")
    parser.add_argument("--url", default="", help="GitHub URL (overrides --repo if set)")
    parser.add_argument("--ref", default=DEFAULT_REF, help="Git ref (branch/tag/commit)")
    parser.add_argument("--dest", required=True, help="Destination skills directory")
    parser.add_argument("--path", nargs="*", default=[], help="Path(s) to skills inside repo")
    parser.add_argument("--skill", nargs="*", default=[], help="Skill name(s) under skills/")
    parser.add_argument(
        "--method",
        choices=["auto", "download", "git"],
        default=DEFAULT_METHOD,
        help="Install method for skill-installer",
    )
    parser.add_argument("--force-overwrite", action="store_true", help="Overwrite existing skill directories")
    parser.add_argument("--json", action="store_true", help="Emit JSON summary to stdout")

    args = parser.parse_args()

    installer = skill_installer_script()
    if not installer.exists():
        print(
            f"Error: skill-installer not found at {installer}. Install it or set CODEX_HOME.",
            file=sys.stderr,
        )
        return 1

    items = build_items(args.skill, args.path)
    if not items:
        print("Error: provide at least one --skill or --path", file=sys.stderr)
        return 1

    dest_root = Path(args.dest)
    installed: List[str] = []
    skipped: List[Dict[str, str]] = []
    failed: List[Dict[str, str]] = []

    repo_flag = "--url" if args.url else "--repo"
    repo_value = args.url or args.repo
    if not repo_value:
        print("Error: missing --repo or --url", file=sys.stderr)
        return 1

    seen = set()
    for item in items:
        if item.name in seen:
            skipped.append({"name": item.name, "reason": "duplicate entry"})
            continue
        seen.add(item.name)

        if os.path.isabs(item.path) or os.path.normpath(item.path).startswith(".."):
            failed.append({"name": item.name, "reason": f"invalid path: {item.path}"})
            continue

        dest_dir = dest_root / item.name
        if dest_dir.exists():
            if not args.force_overwrite:
                skipped.append({"name": item.name, "reason": "destination exists"})
                continue
            try:
                remove_path(dest_dir)
            except OSError as exc:
                failed.append({"name": item.name, "reason": f"failed to remove destination: {exc}"})
                continue

        cmd = [
            sys.executable,
            str(installer),
            repo_flag,
            repo_value,
            "--ref",
            args.ref,
            "--path",
            item.path,
            "--dest",
            str(dest_root),
            "--method",
            args.method,
        ]
        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        if result.returncode != 0:
            reason = result.stderr.strip() or result.stdout.strip() or "install failed"
            failed.append({"name": item.name, "reason": reason})
            continue
        installed.append(item.name)

    if args.json:
        print(format_summary(installed, skipped, failed))
    else:
        for name in installed:
            print(f"Installed {name}")
        for entry in skipped:
            print(f"Skipped {entry['name']}: {entry['reason']}")
        for entry in failed:
            print(f"Failed {entry['name']}: {entry['reason']}", file=sys.stderr)

    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
