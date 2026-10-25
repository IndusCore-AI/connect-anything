#!/usr/bin/env python3
"""Copy the shared engine, the entrance script and the references into each skill folder.

Installers such as `npx skills add` and `gh skill install` copy one skill folder, not the repo, so each skill
must carry what it runs. The copies are generated from scripts/ and references/ (the only place to edit them);
`python3 tools/sync.py --check` fails when a copy has drifted, and the test suite runs it.
"""
import filecmp
import os
import shutil
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKILLS = {"connect-skills": "connect", "compile-skills": "compile", "update-skills": "update"}
IGNORE = shutil.ignore_patterns("__pycache__", "*.pyc", ".DS_Store")


def plan():
    """(source, destination) pairs for every generated copy."""
    pairs = []
    for skill, entrance in SKILLS.items():
        dest = os.path.join(ROOT, "skills", skill)
        pairs.append((os.path.join(ROOT, "scripts", "engine"), os.path.join(dest, "scripts", "engine")))
        pairs.append((os.path.join(ROOT, "scripts", entrance), os.path.join(dest, "scripts", entrance)))
        for ref in sorted(os.listdir(os.path.join(ROOT, "references"))):
            if ref.endswith(".md"):
                pairs.append((os.path.join(ROOT, "references", ref), os.path.join(dest, "references", ref)))
    return pairs


def drift():
    out = []
    for src, dst in plan():
        if os.path.isdir(src):
            cmp = filecmp.dircmp(src, dst, ignore=["__pycache__", ".DS_Store"]) if os.path.isdir(dst) else None
            if cmp is None:
                out.append(dst)
                continue
            stack = [cmp]
            while stack:
                c = stack.pop()
                bad = c.left_only + c.right_only + c.diff_files + c.funny_files
                out += [os.path.join(c.right, b) for b in bad if not b.endswith(".pyc")]
                stack += list(c.subdirs.values())
        elif not os.path.isfile(dst) or not filecmp.cmp(src, dst, shallow=False):
            out.append(dst)
    return out


def sync():
    for src, dst in plan():
        if os.path.isdir(src):
            if os.path.isdir(dst):
                shutil.rmtree(dst)
            shutil.copytree(src, dst, ignore=IGNORE)
        else:
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.copy2(src, dst)


if __name__ == "__main__":
    if "--check" in sys.argv:
        d = drift()
        if d:
            print("out of date (run python3 tools/sync.py):\n  " + "\n  ".join(os.path.relpath(p, ROOT) for p in d))
            sys.exit(1)
        print("skill folders match scripts/ and references/")
        sys.exit(0)
    sync()
    print("synced " + ", ".join(SKILLS))
