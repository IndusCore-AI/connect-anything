"""Lock step: connect-anything.lock.json, shaped like vercel-labs/skills' skills-lock.json.

Each source entry carries Vercel's fields (source, sourceUrl, sourceType, ref, skillPath, computedHash) plus
what a compiled skill needs to be honest and updatable: the licence verdict, how it was used, the hash of
every file read (so update can re-read exactly what changed), what was kept, and the scan result.
The top-level `tool` names the tool the way package-lock.json names npm. Nothing else credits anyone.
"""
import os

from .util import LOCK_NAME, LOCK_VERSION, TOOL_NAME, TOOL_URL, TOOL_VERSION, EngineError, folder_hash, read_json, write_json


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
    if lock.get("version") != LOCK_VERSION:
        raise EngineError(f"{path}: lock version {lock.get('version')} is not {LOCK_VERSION}")
    return lock


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
        if entry.get("use") == "flatten" and folder and not os.path.isdir(os.path.join(skill_dir, folder)):
            problems.append(f"{alias}: folder {folder}/ is missing")
    return problems
