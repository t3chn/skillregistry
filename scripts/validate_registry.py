#!/usr/bin/env python3
import sys
from pathlib import Path
from typing import Dict, List, Tuple

REQUIRED_DIRS = {"skills", "templates", "catalog", "docs"}
ALLOWED_DIRS = REQUIRED_DIRS | {"scripts", "tests"}


def parse_frontmatter(path: Path) -> Tuple[Dict[str, str], str]:
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}, "missing frontmatter start '---'"

    end = None
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            end = i
            break
    if end is None:
        return {}, "frontmatter missing closing '---'"

    data = parse_frontmatter_lines(lines[1:end])
    return data, ""


def parse_frontmatter_lines(lines: List[str]) -> Dict[str, str]:
    data: Dict[str, str] = {}
    i = 0
    while i < len(lines):
        raw = lines[i]
        stripped = raw.strip()
        if not stripped or stripped.startswith("#"):
            i += 1
            continue
        if ":" not in raw:
            i += 1
            continue

        key, rest = raw.split(":", 1)
        key = key.strip()
        value = rest.lstrip()

        if value in (">", "|"):
            i += 1
            block: List[str] = []
            while i < len(lines):
                block_line = lines[i]
                if block_line.startswith(" ") or block_line.startswith("\t"):
                    block.append(block_line.strip())
                    i += 1
                else:
                    break
            data[key] = " ".join(block).strip()
            continue

        if value == "":
            i += 1
            block = []
            while i < len(lines):
                block_line = lines[i]
                if block_line.startswith(" ") or block_line.startswith("\t"):
                    block.append(block_line.strip())
                    i += 1
                else:
                    break
            data[key] = " ".join(block).strip() if block else ""
            continue

        v = value.strip()
        if (v.startswith("\"") and v.endswith("\"")) or (v.startswith("'") and v.endswith("'")):
            v = v[1:-1]
        data[key] = v
        i += 1

    return data


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    errors: List[str] = []

    for entry in sorted(root.iterdir(), key=lambda p: p.name):
        if entry.name.startswith("."):
            continue
        if entry.is_dir() and entry.name not in ALLOWED_DIRS:
            errors.append(f"Unexpected top-level directory: {entry.name}")

    for name in REQUIRED_DIRS:
        if not (root / name).is_dir():
            errors.append(f"Missing required directory: {name}")

    if not (root / "templates").is_dir():
        errors.append("Missing templates/")
    if not (root / "catalog" / "skillsets.json").is_file():
        errors.append("Missing catalog/skillsets.json")

    docs_research = root / "docs" / "research"
    if docs_research.exists():
        errors.append("Disallowed path present: docs/research")
    docs_research_md = root / "docs" / "research.md"
    if docs_research_md.exists():
        errors.append("Disallowed file present: docs/research.md")

    skills_dir = root / "skills"
    if skills_dir.is_dir():
        for skill_dir in sorted(skills_dir.iterdir(), key=lambda p: p.name):
            if skill_dir.name.startswith("."):
                continue
            if not skill_dir.is_dir():
                errors.append(f"Non-directory entry in skills/: {skill_dir.name}")
                continue
            skill_md = skill_dir / "SKILL.md"
            if not skill_md.is_file():
                errors.append(f"Missing SKILL.md for skill: {skill_dir.name}")
                continue
            frontmatter, err = parse_frontmatter(skill_md)
            if err:
                errors.append(f"{skill_md}: {err}")
                continue
            name = frontmatter.get("name", "").strip()
            description = frontmatter.get("description", "").strip()
            if not name:
                errors.append(f"{skill_md}: missing frontmatter field: name")
            if not description:
                errors.append(f"{skill_md}: missing frontmatter field: description")
            if name and name != skill_dir.name:
                errors.append(
                    f"{skill_md}: frontmatter name '{name}' does not match folder '{skill_dir.name}'"
                )

    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        print(f"\n{len(errors)} validation error(s).", file=sys.stderr)
        return 1

    print("Registry validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
