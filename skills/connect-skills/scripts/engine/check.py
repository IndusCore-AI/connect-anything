"""Check step: mechanical checks on an emitted skill folder (and on this pack's own skills).

  spec        skills-ref rules: frontmatter parses strictly, only the six portable fields, name rules, name ==
              folder, description 1 to 1,024 characters, compatibility up to 500. `skills-ref` itself runs too
              when it is on PATH.
  size        SKILL.md under 500 lines and the body under 5,000 tokens (the spec's numbers)
  refs        every path SKILL.md names in backticks exists
  one-copy    no rule appears twice in SKILL.md
  nested      no second SKILL.md below the root (loaders would see a second skill)
  provenance  every copied source folder has README.md and its LICENSE; referenced ones carry no copied files
  scan        no blocking finding anywhere in the folder; nothing promotional in the files the compiler wrote,
              by our scanner and by skill-radar's install_skill.py review
  lock        the lock's hashes match the folder
"""
import importlib.util
import io
import os
import re
import shutil
import contextlib

from .util import (LOCK_NAME, EM_DASH, EN_DASH, content_words, estimate_tokens, iter_files, parse_frontmatter,
                   run, split_frontmatter, EngineError)
from .scan import SKILL_RADAR_INSTALLER, scan_files, blocked
from .read import read_tree

ALLOWED_FIELDS = {"name", "description", "license", "allowed-tools", "metadata", "compatibility"}
MAX_LINES, MAX_TOKENS = 500, 5000
COMPILER_FILES = re.compile(r"^(SKILL\.md|MERGE\.md|[^/]+/README\.md|" + re.escape(LOCK_NAME) + r"|evals/.*)$")
PROMO_RULES = {"promo-instruction", "promo-line"}
SELF_CREDIT = re.compile(r"github\.com/(gaurpulkit|induscore)[^\s]*/connect-anything|(built|made|compiled|generated) (with|by) connect-anything|powered by connect-anything|connect-anything (by|from) induscore", re.I)


def spec_problems(skill_dir):
    """The skills-ref validator's rules, standard library only."""
    p = os.path.join(skill_dir, "SKILL.md")
    if not os.path.isfile(p):
        return ["Missing required file: SKILL.md"]
    text = open(p, encoding="utf-8").read()
    if not text.startswith("---"):
        return ["SKILL.md must start with YAML frontmatter (---)"]
    block, _ = split_frontmatter(text)
    if block is None:
        return ["SKILL.md frontmatter not properly closed with ---"]
    data, problems = parse_frontmatter(block)
    out = list(problems)
    extra = set(data) - ALLOWED_FIELDS
    if extra:
        out.append(f"Unexpected fields in frontmatter: {', '.join(sorted(extra))}")
    name = data.get("name")
    if not isinstance(name, str) or not name.strip():
        out.append("Field 'name' must be a non-empty string")
    else:
        if len(name) > 64:
            out.append(f"name exceeds 64 characters ({len(name)})")
        if name != name.lower():
            out.append("name must be lowercase")
        if name.startswith("-") or name.endswith("-") or "--" in name:
            out.append("name has a leading, trailing or doubled hyphen")
        if not all(c.isalnum() or c == "-" for c in name):
            out.append("name may hold only letters, digits and hyphens")
        if os.path.basename(os.path.normpath(skill_dir)) != name:
            out.append(f"folder '{os.path.basename(os.path.normpath(skill_dir))}' must match name '{name}'")
    desc = data.get("description")
    if not isinstance(desc, str) or not desc.strip():
        out.append("Field 'description' must be a non-empty string")
    elif len(desc) > 1024:
        out.append(f"description exceeds 1,024 characters ({len(desc)})")
    comp = data.get("compatibility")
    if comp is not None and (not isinstance(comp, str) or len(comp) > 500):
        out.append("compatibility must be a string of at most 500 characters")
    md = data.get("metadata")
    if md is not None and not isinstance(md, dict):
        out.append("metadata must be a map of strings")
    return out


def skills_ref(skill_dir):
    """Run the reference validator when installed. Returns (ran, ok, output)."""
    import subprocess
    exe = shutil.which("skills-ref")
    if not exe:
        return False, None, "skills-ref not on PATH (the same rules ran in Python above)"
    p = subprocess.run([exe, "validate", skill_dir], capture_output=True, text=True, timeout=60)
    return True, p.returncode == 0, (p.stdout + p.stderr).strip()


def size_check(skill_dir):
    text = open(os.path.join(skill_dir, "SKILL.md"), encoding="utf-8").read()
    _, body = split_frontmatter(text)
    lines = text.count("\n") + (0 if text.endswith("\n") else 1)
    return lines, estimate_tokens(body)


PATH_IN_TICKS = re.compile(r"`([A-Za-z0-9_.-]+(?:/[A-Za-z0-9_.-]+)*/?)`")


LINK_TARGET = re.compile(r"\]\(([^)\s#]+)(?:#[^)]*)?\)")


def missing_refs(skill_dir):
    """Paths SKILL.md names that do not exist. A path that exists only inside a source folder (written relative
    to that source) is missing too: the copied text was not pointed at its folder."""
    text = open(os.path.join(skill_dir, "SKILL.md"), encoding="utf-8").read()
    subdirs = [d for d in os.listdir(skill_dir) if os.path.isdir(os.path.join(skill_dir, d))]
    aliases = set()
    lock_path = os.path.join(skill_dir, LOCK_NAME)
    if os.path.isfile(lock_path):  # a path into any source's folder must exist, even one the merge left out
        import json
        aliases = set(json.load(open(lock_path, encoding="utf-8")).get("skills", {}))
    cands = {m.group(1) for m in PATH_IN_TICKS.finditer(text)} | {m.group(1) for m in LINK_TARGET.finditer(text)}
    missing = []
    for p in cands:
        if "/" not in p or p.startswith(("http", "~", "/", "$", "<")) or "*" in p or "<" in p:
            continue
        clean = p.rstrip("/")
        if os.path.exists(os.path.join(skill_dir, clean)):
            continue
        if os.path.exists(os.path.join(skill_dir, clean.split("/")[0])) or clean.split("/")[0] in aliases:
            missing.append(p)
        elif any(os.path.exists(os.path.join(skill_dir, d, clean)) for d in subdirs):
            missing.append(p + " (relative to a source folder)")
    for m in re.finditer(r"(<skill-dir>|\$\{CLAUDE_SKILL_DIR\})/([A-Za-z0-9_./-]+)", text):
        if not os.path.exists(os.path.join(skill_dir, m.group(2).rstrip("/."))):
            missing.append(m.group(0))
    return sorted(set(missing))


COMPILER_TAIL = re.compile(r"^## (Where the rest is|Sources|Skills this one runs \(not copied\))\s*$", re.M)


def duplicate_rules(skill_dir, threshold=0.8):
    text = open(os.path.join(skill_dir, "SKILL.md"), encoding="utf-8").read()
    m = COMPILER_TAIL.search(text)
    text = text[: m.start()] if m else text  # the compiler's own index lists are not rules
    rules = []
    for line in text.splitlines():
        m = re.match(r"^\s*(?:[-*+]|\d+[.)])\s+(.*\S)", line)
        if m:
            cw = set(content_words(m.group(1)))
            if len(cw) >= 5:
                rules.append((m.group(1), cw))
    dups = []
    for i in range(len(rules)):
        for j in range(i + 1, len(rules)):
            a, b = rules[i][1], rules[j][1]
            if len(a & b) / max(1, len(a | b)) >= threshold:
                dups.append((rules[i][0][:80], rules[j][0][:80]))
    return dups


def nested_skills(skill_dir):
    return [rel for rel, _ in iter_files(skill_dir) if rel.endswith("/SKILL.md")]


def provenance_problems(skill_dir):
    lock_path = os.path.join(skill_dir, LOCK_NAME)
    if not os.path.isfile(lock_path):
        return ["no lockfile"]
    import json
    lock = json.load(open(lock_path, encoding="utf-8"))
    out = []
    for alias, e in lock.get("skills", {}).items():
        folder = e.get("folder")
        if not folder:
            continue
        d = os.path.join(skill_dir, folder)
        if not os.path.isfile(os.path.join(d, "README.md")):
            out.append(f"{folder}/README.md missing")
        if e.get("use") == "flatten" and e.get("licence", {}).get("verdict") == "flatten" and not os.path.isfile(os.path.join(d, "LICENSE")):
            out.append(f"{folder}/LICENSE missing for a copied {e['licence']['spdx']} source")
        if e.get("use") == "reference":
            extra = [rel for rel, _ in iter_files(d) if rel != "README.md"]
            if extra:
                out.append(f"{folder}/ is referenced only but holds copied files: {extra[:3]}")
    return out


def radar_review(skill_dir):
    """skill-radar's own review() on the folder. Returns (available, flags)."""
    if not os.path.isfile(SKILL_RADAR_INSTALLER):
        return False, []
    spec = importlib.util.spec_from_file_location("_skill_radar_install", SKILL_RADAR_INSTALLER)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        flags = mod.review(skill_dir, "local", ".", "local", {}, "x")
    return True, flags


RADAR_FAIL_LABELS = ("下载后直接执行", "可疑提示注入措辞", "读 SSH 密钥", "读 Keychain", "反向 shell", "删除家目录/根目录")
RADAR_PROMO_LABEL = "自我推广/签名行"


def run_checks(skill_dir, allow=(), expect_lock=True, house_style=False):
    """All checks. Returns a list of {name, ok, detail}."""
    results = []

    def add(name, ok, detail):
        results.append({"name": name, "ok": bool(ok), "detail": detail})

    probs = spec_problems(skill_dir)
    add("spec", not probs, "; ".join(probs) if probs else "frontmatter valid, name matches the folder")
    ran, ok, out = skills_ref(skill_dir)
    if ran:
        add("skills-ref validate", ok, out.splitlines()[-1] if out else "")
    lines, tokens = size_check(skill_dir)
    add("size", lines < MAX_LINES and tokens < MAX_TOKENS, f"SKILL.md {lines} lines (limit {MAX_LINES}), body about {tokens} tokens (limit {MAX_TOKENS})")
    miss = missing_refs(skill_dir)
    add("refs", not miss, "every path SKILL.md names exists" if not miss else "missing: " + ", ".join(miss[:8]))
    dups = duplicate_rules(skill_dir)
    add("one-copy", not dups, "no rule appears twice" if not dups else f"{len(dups)} rules appear twice, e.g. {dups[0]}")
    nested = nested_skills(skill_dir)
    add("nested", not nested, "one SKILL.md" if not nested else "second SKILL.md at " + ", ".join(nested[:4]))
    if expect_lock:
        pp = provenance_problems(skill_dir)
        add("provenance", not pp, "every source folder has its README and LICENSE" if not pp else "; ".join(pp[:5]))
    files = read_tree(skill_dir)
    findings, summary = scan_files(files, allow=allow)
    bad = blocked(findings)
    own = [f for f in findings if COMPILER_FILES.match(f["file"]) and (f["rule"] in PROMO_RULES or f["rule"] == "tracking-link")]
    dashes = [rel for rel in (x["path"] for x in files) if COMPILER_FILES.match(rel) and rel != LOCK_NAME
              and _compiler_dashes(os.path.join(skill_dir, rel))]
    add("scan", not bad and not own, f"{summary['block']} blocking, {summary['review']} to review across {len(files)} files; "
        f"{len(own)} promotional lines in compiler-written files" + (f"; blocking: {bad[0]['file']}:{bad[0]['line']} {bad[0]['label']}" if bad else ""))
    avail, flags = radar_review(skill_dir)
    if avail:
        # copied source files were judged by our scanner (block = excluded); the radar's broad list decides
        # only for the files the compiler wrote
        hard = [f for f in flags if f[2] in RADAR_FAIL_LABELS and COMPILER_FILES.match(f[0])]
        promo = [f for f in flags if f[2] == RADAR_PROMO_LABEL and COMPILER_FILES.match(f[0]) and f[0] != LOCK_NAME]
        add("install_skill.py review", not hard and not promo,
            f"{len(flags)} lines flagged in total; {len(hard)} dangerous, {len(promo)} self-promotion in compiler-written files"
            + (f": {hard[0][0]}:{hard[0][1]}" if hard else "") + (f": {promo[0][0]}:{promo[0][1]} {promo[0][3][:60]}" if promo else ""))
    credit = [rel for rel in (x["path"] for x in files) if COMPILER_FILES.match(rel) and rel != LOCK_NAME
              and SELF_CREDIT.search(open(os.path.join(skill_dir, rel), encoding="utf-8", errors="replace").read())]
    add("no self-credit", not credit, "the compiler names itself only in the lockfile" if not credit
        else "the tool or its maker is named in: " + ", ".join(credit[:5]))
    if house_style:
        add("house style", not dashes, "no em or en dashes in compiler-written files" if not dashes else "em or en dashes in: " + ", ".join(dashes[:5]))
    if expect_lock and os.path.isfile(os.path.join(skill_dir, LOCK_NAME)):
        from .lock import verify_lock
        lp = verify_lock(skill_dir)
        add("lock", not lp, "hashes match the folder" if not lp else "; ".join(lp))
    return results


def _compiler_dashes(path):
    """Dashes in text the compiler wrote. SKILL.md inline sections copied from sources are not counted."""
    text = open(path, encoding="utf-8", errors="replace").read()
    return EM_DASH in text or EN_DASH in text


def all_ok(results):
    return all(r["ok"] for r in results)
