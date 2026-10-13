#!/usr/bin/env python3
"""Package the skill folder as a .skill (zip) for upload to Claude (maintenance only).

    python scripts/package_skill.py <skill folder> <output folder>

Checks before writing anything, because an upload fails on any of them:
  * SKILL.md has YAML frontmatter with `name` equal to the folder name, `description` <= 1024 characters and
    `compatibility` <= 500 characters;
  * the archive has at most 200 files (Claude's upload limit; the skill's large references are bundled to stay under it);
  * no file is a Python cache, a script unit test (`scripts/test_*.py`) or an OS artefact.
Writes <output>/<name>.skill and a byte-identical <name>.zip, with every file under a single top-level <name>/ folder.
"""
import os
import sys
import zipfile

MAX_FILES = 200


def main():
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    src, out_dir = os.path.abspath(sys.argv[1]), sys.argv[2]
    name = os.path.basename(src.rstrip("/\\"))
    text = open(os.path.join(src, "SKILL.md"), encoding="utf-8").read()
    parts = text.split("---")
    if not text.startswith("---") or len(parts) < 3:
        sys.exit("SKILL.md has no frontmatter")
    try:
        import yaml
        fm = yaml.safe_load(parts[1])
    except ImportError:
        sys.exit("needs PyYAML (pip install pyyaml) to read the frontmatter")
    problems = []
    if fm.get("name") != name:
        problems.append(f"name {fm.get('name')!r} must equal the folder name {name!r}")
    if len(fm.get("description", "")) > 1024:
        problems.append(f"description is {len(fm['description'])} characters (max 1024)")
    if len(fm.get("compatibility", "")) > 500:
        problems.append(f"compatibility is {len(fm['compatibility'])} characters (max 500)")
    files = []
    for root, dirs, names in os.walk(src):
        dirs[:] = [d for d in dirs if d != "__pycache__"]
        for n in sorted(names):
            if n.endswith((".pyc", ".DS_Store")) or n == "Thumbs.db" or (n.startswith("test_") and n.endswith(".py")):
                continue
            files.append(os.path.join(root, n))
    if len(files) > MAX_FILES:
        problems.append(f"{len(files)} files (max {MAX_FILES}); bundle more of the references")
    if problems:
        sys.exit("not packaged:\n  " + "\n  ".join(problems))
    os.makedirs(out_dir, exist_ok=True)
    out = os.path.join(out_dir, name + ".skill")
    if os.path.exists(out):
        os.remove(out)
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for p in files:
            z.write(p, name + "/" + os.path.relpath(p, src).replace(os.sep, "/"))
    with zipfile.ZipFile(out) as z:
        assert z.testzip() is None
        assert f"{name}/SKILL.md" in z.namelist()
    zip_copy = os.path.join(out_dir, name + ".zip")
    with open(out, "rb") as a, open(zip_copy, "wb") as b:
        b.write(a.read())
    print(f"{len(files)} files, {os.path.getsize(out) / 1e6:.1f} MB -> {out} (and {os.path.basename(zip_copy)})")


if __name__ == "__main__":
    main()
