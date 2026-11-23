#!/usr/bin/env python3
"""Validate skill structure: frontmatter, naming, leftover TODOs, and committed captures."""
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
SKILLS = ROOT / "skills"
NAME_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
FORBIDDEN = {".har", ".jtl"}

errors = []

for skill in sorted(SKILLS.glob("*/SKILL.md")):
    folder = skill.parent.name
    text = skill.read_text(encoding="utf-8")
    match = re.match(r"---\n(.*?)\n---\n", text, re.S)
    if not match:
        errors.append(f"{skill.relative_to(ROOT)}: missing frontmatter")
        continue
    fields = {}
    for line in match.group(1).splitlines():
        if ":" in line and not line.startswith(" "):
            key, value = line.split(":", 1)
            fields[key.strip()] = value.strip()
    name = fields.get("name", "")
    description = fields.get("description", "")
    if name != folder:
        errors.append(f"{skill.relative_to(ROOT)}: name '{name}' does not match folder '{folder}'")
    if not NAME_RE.match(name) or len(name) > 64:
        errors.append(f"{skill.relative_to(ROOT)}: invalid name '{name}'")
    if not description:
        errors.append(f"{skill.relative_to(ROOT)}: empty description")
    elif len(description) > 1024:
        errors.append(f"{skill.relative_to(ROOT)}: description is {len(description)} chars (max 1024)")

for md in sorted(SKILLS.rglob("*.md")):
    if "TODO" in md.read_text(encoding="utf-8"):
        errors.append(f"{md.relative_to(ROOT)}: contains TODO")

for path in ROOT.rglob("*"):
    if ".git" in path.parts:
        continue
    if path.is_file() and path.suffix.lower() in FORBIDDEN:
        errors.append(f"{path.relative_to(ROOT)}: capture or result file must not be committed")

if errors:
    print("\n".join(errors))
    sys.exit(1)
print(f"OK: {len(list(SKILLS.glob('*/SKILL.md')))} skills validated")
