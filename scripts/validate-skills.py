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

# script paths in skills must be written relative to the skill folder, and must exist
REPO_REL = re.compile(r"(?<![\w<>/.-])skills/[a-z0-9-]+/(?:scripts|references)/")
SKILL_DIR_REF = re.compile(r"<skill-dir>/((?:scripts|references)/[\w./-]+)")
SKILLS_DIR_REF = re.compile(r"<skills-dir>/([a-z0-9-]+)/((?:scripts|references)/[\w./-]+)")
for md in sorted(SKILLS.rglob("*.md")):
    text = md.read_text(encoding="utf-8")
    skill_dir = SKILLS / md.relative_to(SKILLS).parts[0]
    for m in REPO_REL.finditer(text):
        errors.append(f"{md.relative_to(ROOT)}: repo-relative script path '{m.group(0)}...'; use <skill-dir>/ or <skills-dir>/")
    for m in SKILL_DIR_REF.finditer(text):
        if not (skill_dir / m.group(1)).exists():
            errors.append(f"{md.relative_to(ROOT)}: <skill-dir>/{m.group(1)} does not exist")
    for m in SKILLS_DIR_REF.finditer(text):
        if not (SKILLS / m.group(1) / m.group(2)).exists():
            errors.append(f"{md.relative_to(ROOT)}: <skills-dir>/{m.group(1)}/{m.group(2)} does not exist")

# perf-mode: the router and every playbook keep the same structure
PERF = SKILLS / "perf-mode"
PLAYBOOKS = PERF / "playbooks"
ROUTER_SECTIONS = ["## Start here (hard rule)", "## Non-negotiables", "## Principles", "## Autonomy",
                   "## Delegation", "## Reply format", "## Playbooks"]
PLAYBOOK_SECTIONS = ["## Inputs", "## Steps", "## Verification", "## Stop conditions", "## Delegation",
                     "## Reply format", "## Related playbooks", "## Done when"]
if PERF.exists():
    router = (PERF / "SKILL.md").read_text(encoding="utf-8")
    for h in ROUTER_SECTIONS:
        if h not in router:
            errors.append(f"skills/perf-mode/SKILL.md: missing section '{h}'")
    if not (PERF / "worker.md").exists():
        errors.append("skills/perf-mode/worker.md is missing")
    for principle in sorted(p.name for p in SKILLS.glob("principle-*") if p.is_dir()):
        if f"`{principle}`" not in router:
            errors.append(f"skills/perf-mode/SKILL.md: principle '{principle}' is not listed")
    known = {p.name for p in SKILLS.iterdir() if p.is_dir()}
    listed = set(re.findall(r"\(playbooks/([a-z0-9-]+)\.md\)", router))
    on_disk = {p.stem for p in PLAYBOOKS.glob("*.md") if not p.name.startswith("_")}
    for name in sorted(on_disk - listed):
        errors.append(f"skills/perf-mode/SKILL.md: playbook '{name}' is not in the table")
    for name in sorted(listed - on_disk):
        errors.append(f"skills/perf-mode/SKILL.md: table links playbooks/{name}.md, which does not exist")
    for name in sorted(on_disk):
        text = (PLAYBOOKS / f"{name}.md").read_text(encoding="utf-8")
        if not text.startswith("# Playbook:"):
            errors.append(f"playbooks/{name}.md: must start with '# Playbook:'")
        for h in PLAYBOOK_SECTIONS:
            if h not in text:
                errors.append(f"playbooks/{name}.md: missing section '{h}'")
        for token in re.findall(r"`([a-z0-9]+(?:-[a-z0-9]+)+)`", text):
            if token.split("-")[0] in {"script", "principle", "results", "load", "browser", "flow", "journey",
                                       "sweep", "perf", "har"} and token not in known | on_disk:
                errors.append(f"playbooks/{name}.md: '{token}' is not a skill or playbook")

for path in ROOT.rglob("*"):
    if ".git" in path.parts:
        continue
    if path.is_file() and path.suffix.lower() in FORBIDDEN:
        errors.append(f"{path.relative_to(ROOT)}: capture or result file must not be committed")

if errors:
    print("\n".join(errors))
    sys.exit(1)
print(f"OK: {len(list(SKILLS.glob('*/SKILL.md')))} skills validated")
