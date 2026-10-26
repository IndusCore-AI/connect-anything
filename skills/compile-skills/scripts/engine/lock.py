"""Lock step: connect-anything.lock.json, shaped like vercel-labs/skills' skills-lock.json.

Each source entry carries Vercel's fields (source, sourceUrl, sourceType, ref, skillPath, computedHash) plus
what a compiled skill needs to be honest and updatable: the licence verdict, how it was used, the hash of
every file read (so update can re-read exactly what changed), what was kept, and the scan result.
The top-level `tool` names the tool the way package-lock.json names npm. Nothing else credits anyone.
"""
import os
import re

from .util import (LOCK_NAME, LOCK_VERSION, TOOL_NAME, TOOL_URL, TOOL_VERSION, EngineError, folder_hash, read_json,
                   sha256_file, skill_name_ok, write_json)

ALIAS_RE = re.compile(r"^[a-z0-9][a-z0-9._-]{0,63}$")
SOURCE_RE = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")


def _safe_rel(value):
    """A relative path inside the skill folder: no absolute path, drive letter, backslash or '..' segment."""
    if not isinstance(value, str) or not value or value.startswith(("/", "\\")) or re.match(r"^[A-Za-z]:", value):
        return False
    parts = value.replace("\\", "/").split("/")
    return all(p not in ("", ".", "..") for p in parts)


def lock_problems(lock):
    """Schema and path problems in a lockfile. A compiled skill can arrive from anywhere, so its lock is
    untrusted input: names, folders and paths are checked before any of them is joined to a real directory."""
    p = []
    if not isinstance(lock, dict):
        return ["the lock is not a JSON object"]
    if lock.get("version") != LOCK_VERSION:
        p.append(f"version {lock.get('version')!r} is not {LOCK_VERSION}")
    skill = lock.get("skill")
    if not isinstance(skill, dict):
        p.append("skill is missing")
    else:
        if not skill_name_ok(skill.get("name")):
            p.append(f"skill.name {skill.get('name')!r} is not a safe folder name")
        if skill.get("computedHash") is not None and not re.fullmatch(r"[0-9a-f]{64}", str(skill.get("computedHash"))):
            p.append("skill.computedHash is not a SHA-256")
    skills = lock.get("skills")
    if not isinstance(skills, dict):
        p.append("skills is missing")
        return p
    for alias, entry in skills.items():
        if not ALIAS_RE.match(str(alias)):
            p.append(f"skills key {alias!r} is not a safe alias")
            continue
        if not isinstance(entry, dict):
            p.append(f"{alias}: entry is not an object")
            continue
        if entry.get("source") and entry.get("sourceType", "github") == "github" and not SOURCE_RE.match(str(entry["source"])):
            p.append(f"{alias}: source {entry.get('source')!r} is not owner/repo")
        if entry.get("folder") is not None and (not _safe_rel(entry["folder"]) or "/" in entry["folder"]):
            p.append(f"{alias}: folder {entry.get('folder')!r} is not a single safe folder name")
        if entry.get("skillPath") is not None and not _safe_rel(entry["skillPath"]):
            p.append(f"{alias}: skillPath {entry.get('skillPath')!r} escapes the source folder")
        files = entry.get("files")
        if files is not None:
            if not isinstance(files, dict):
                p.append(f"{alias}: files is not a map")
            else:
                for rel in files:
                    if not _safe_rel(rel):
                        p.append(f"{alias}: file path {rel!r} escapes the source folder")
                        break
        for rel in (entry.get("kept") or []):
            if not _safe_rel(rel):
                p.append(f"{alias}: kept path {rel!r} escapes the source folder")
                break
    return p


def source_entry(src):
    lic = src["licence"]
    entry = {
        "source": src["source"],
        "sourceUrl": src.get("sourceUrl"),
        "sourceType": src["sourceType"],
        "ref": src.get("ref"),
        "skillPath": src.get("skillPath"),
        "computedHash": src.get("computedHash"),
        "folder": src["alias"] if src["mode"] != "excluded" else None,
        "use": src["mode"],
        "licence": {"spdx": lic["spdx"], "verdict": lic["verdict"], "file": lic.get("file")},
        "read": {"files": src["files_read"], "bytes": src["bytes_read"]},
        "scan": src["scan"]["summary"],
        "files": {f["path"]: f["sha256"] for f in src["files"] if f.get("sha256")},
        "kept": sorted(f["path"] for f in src["files"] if f.get("keep")),
        "sections": [{"id": s["id"], "file": s["file"], "lines": s["lines"], "hash": s["hash"], "use": s["action"],
                      **({"modified": True} if s.get("modified") else {})}
                     for s in src["sections"] if s["action"] in ("inline", "reference")],
    }
    if src.get("section_selector"):
        entry["section"] = src["section_selector"]
    if src.get("strip_ranges"):
        entry["stripped"] = sorted({rng["file"] for rng in src["strip_ranges"] if rng.get("file")})
    if src["mode"] == "excluded":
        entry["excluded"] = src.get("excluded_reason")
    return {k: v for k, v in entry.items() if v not in (None, [], {})}


def build_lock(plan, out_dir, eval_result=None, decisions=None):
    skills = {}
    for src in plan["sources"]:
        skills[src["alias"]] = source_entry(src)
    lock = {
        "version": LOCK_VERSION,
        "tool": {"name": TOOL_NAME, "version": TOOL_VERSION, "url": TOOL_URL},
        "skill": {"name": plan["name"], "mode": plan["mode"],
                  "computedHash": folder_hash(out_dir, exclude={LOCK_NAME})},
        "skills": dict(sorted(skills.items())),
    }
    if plan.get("job"):
        lock["skill"]["job"] = plan["job"]
    if decisions:
        lock["decisions"] = decisions
    if eval_result:
        lock["eval"] = {k: eval_result[k] for k in ("verdict", "tiers", "originals", "compiled", "eval_set_hash", "tolerance")
                        if k in eval_result}
    return lock


def write_lock(plan, out_dir, eval_result=None, decisions=None):
    lock = build_lock(plan, out_dir, eval_result, decisions)
    write_json(os.path.join(out_dir, LOCK_NAME), lock)
    return lock


def read_lock(skill_dir):
    path = os.path.join(skill_dir, LOCK_NAME)
    if not os.path.exists(path):
        raise EngineError(f"{skill_dir} has no {LOCK_NAME}. Run update with --adopt to create one from its source READMEs.")
    lock = read_json(path)
    problems = lock_problems(lock)
    if problems:
        raise EngineError(f"{path}: unsafe or invalid lock: " + "; ".join(problems[:5]))
    return lock


def _installed_path(entry, rel):
    folder = entry["folder"]
    main = os.path.basename(entry.get("skillPath") or "SKILL.md")
    renamed = entry.get("renamedSkillFile") or f"{folder.upper()}.md"
    if rel == "SKILL.md" or (entry.get("section") and rel == main):
        return f"{folder}/{renamed}"
    if rel in ("README.md", "LICENSE", "NOTICE"):
        return f"{folder}/SOURCE-{rel}"
    return f"{folder}/{rel}"


def verify_lock(skill_dir):
    """Problems between the lock and the folder on disk (empty list when they agree)."""
    lock = read_lock(skill_dir)
    problems = []
    actual = folder_hash(skill_dir, exclude={LOCK_NAME})
    if lock["skill"].get("computedHash") != actual:
        problems.append(f"folder hash {actual[:12]} does not match the lock's {lock['skill'].get('computedHash', '')[:12]}: "
                        "a file changed after the skill was compiled")
    for alias, entry in lock["skills"].items():
        folder = entry.get("folder")
        if entry.get("use") in ("flatten", "reference") and folder:
            if not os.path.isdir(os.path.join(skill_dir, folder)):
                problems.append(f"{alias}: folder {folder}/ is missing")
                continue
        for rel in (entry.get("kept") or []):
            dest_rel = _installed_path(entry, rel)
            dest = os.path.join(skill_dir, dest_rel)
            if os.path.islink(dest):
                problems.append(f"{alias}: {dest_rel} is a symbolic link; compiled skills contain plain files only")
                continue
            if not os.path.isfile(dest):
                problems.append(f"{alias}: {dest_rel} is missing")
                continue
            want = (entry.get("files") or {}).get(rel)
            if entry.get("section") and rel == os.path.basename(entry.get("skillPath") or "SKILL.md"):
                continue  # a section source is written as selected text, not as the original file
            if rel in (entry.get("stripped") or []):
                continue  # the copy was cut on purpose; the lock records the cut
            if want and sha256_file(dest) != want:
                problems.append(f"{alias}: {dest_rel} changed after the skill was compiled")
    for dirpath, dirnames, filenames in os.walk(skill_dir):
        for name in dirnames + filenames:
            ap = os.path.join(dirpath, name)
            if os.path.islink(ap):
                rel = os.path.relpath(ap, skill_dir).replace(os.sep, "/")
                problems.append(f"symbolic link in the compiled skill: {rel}")
    return problems
