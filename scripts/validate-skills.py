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

# modes (perf-mode, sweep-mode): the router and every playbook keep the same structure
MODES = ["perf-mode", "sweep-mode"]
ROUTER_SECTIONS = ["## Start here (hard rule)", "## Non-negotiables", "## Principles", "## Autonomy",
                   "## Delegation", "## Reply format", "## Playbooks"]
PLAYBOOK_SECTIONS = ["## Inputs", "## Steps", "## Verification", "## Stop conditions", "## Delegation",
                     "## Reply format", "## Related playbooks", "## Done when"]
known = {p.name for p in SKILLS.iterdir() if p.is_dir()}
SKILL_PREFIXES = {"script", "principle", "results", "load", "browser", "flow", "journey", "sweep", "perf", "har",
                  "web", "repair", "review"}


def block(text, name):
    m = re.search(rf"<!-- {name}:start -->(.*?)<!-- {name}:end -->", text, re.S)
    return m.group(1).strip() if m else None


mode_texts = {}
principles_listed = set()
for mode in MODES:
    base = SKILLS / mode
    if not base.exists():
        continue
    router = (base / "SKILL.md").read_text(encoding="utf-8")
    mode_texts[mode] = (router, (base / "worker.md").read_text(encoding="utf-8") if (base / "worker.md").exists() else "")
    for h in ROUTER_SECTIONS:
        if h not in router:
            errors.append(f"skills/{mode}/SKILL.md: missing section '{h}'")
    if not (base / "worker.md").exists():
        errors.append(f"skills/{mode}/worker.md is missing")
    principles_listed |= set(re.findall(r"`(principle-[a-z0-9-]+)`", router))
    playbooks = base / "playbooks"
    listed = set(re.findall(r"\(playbooks/([a-z0-9-]+)\.md\)", router))
    on_disk = {p.stem for p in playbooks.glob("*.md")} if playbooks.exists() else set()
    for name in sorted(on_disk - listed):
        errors.append(f"skills/{mode}/SKILL.md: playbook '{name}' is not in the table")
    for name in sorted(listed - on_disk):
        errors.append(f"skills/{mode}/SKILL.md: table links playbooks/{name}.md, which does not exist")
    for name in sorted(on_disk):
        text = (playbooks / f"{name}.md").read_text(encoding="utf-8")
        if not text.startswith("# Playbook:"):
            errors.append(f"{mode}/playbooks/{name}.md: must start with '# Playbook:'")
        for h in PLAYBOOK_SECTIONS:
            if h not in text:
                errors.append(f"{mode}/playbooks/{name}.md: missing section '{h}'")
        for token in re.findall(r"`([a-z0-9]+(?:-[a-z0-9]+)+)`", text):
            if token.split("-")[0] in SKILL_PREFIXES and token not in known | on_disk:
                errors.append(f"{mode}/playbooks/{name}.md: '{token}' is not a skill or playbook")

for principle in sorted(p.name for p in SKILLS.glob("principle-*") if p.is_dir()):
    if principle not in principles_listed:
        errors.append(f"principle '{principle}' is not listed by any mode")

# the hard rule and the worker core are the same text in every mode
for marker, idx in (("hard-rule", 0), ("worker-core", 1)):
    texts = {m: block(t[idx], marker) for m, t in mode_texts.items()}
    for m, t in texts.items():
        if t is None:
            errors.append(f"skills/{m}: missing <!-- {marker}:start/end --> block")
    present = {t for t in texts.values() if t}
    if len(present) > 1:
        errors.append(f"the {marker} block differs between modes: " + ", ".join(sorted(texts)))

# packs: every name is a skill, and a pack is self-contained
PACKS = ROOT / "packs"
if PACKS.exists():
    for pack in sorted(PACKS.glob("*.txt")):
        names = [l.strip() for l in pack.read_text(encoding="utf-8").splitlines() if l.strip()]
        for n in names:
            if n not in known:
                errors.append(f"{pack.relative_to(ROOT)}: '{n}' is not a skill")
        for n in names:
            if n not in known:
                continue
            for md in (SKILLS / n).rglob("*.md"):
                for token in set(re.findall(r"`([a-z0-9]+(?:-[a-z0-9]+)+)`", md.read_text(encoding="utf-8"))):
                    if token in known and token not in names:
                        errors.append(f"{pack.relative_to(ROOT)}: {md.relative_to(ROOT)} names '{token}', which is not in the pack")

for path in ROOT.rglob("*"):
    if ".git" in path.parts:
        continue
    if path.is_file() and path.suffix.lower() in FORBIDDEN:
        errors.append(f"{path.relative_to(ROOT)}: capture or result file must not be committed")

if errors:
    print("\n".join(errors))
    sys.exit(1)
print(f"OK: {len(list(SKILLS.glob('*/SKILL.md')))} skills validated")
