"""Update: refresh a skill you already use, and fill a gap you name, without writing anything until you approve.

  1. Lock     read connect-anything.lock.json, or with --adopt build one from the per-source READMEs of a
              hand-made merge (the source URL and commit they record; the source path is found by matching the
              copied original SKILL.md's hash against each skill in the repo at that commit).
  2. Upstream for every locked source: resolve the new commit, list what changed under its skill path since the
              locked commit, re-read and re-scan every changed file in full, re-check the licence, and note files
              the installed copy edited locally (never overwritten).
  3. Gap      with --gap: candidates from --candidates, a skill-radar report, and a GitHub search; each one is
              fetched, read in full, scanned and licence-checked, then its sections are scored against the gap.
              The installed skill is scored the same way, so the report shows how weak it is on the gap today.
  4. Propose  a full copy of the skill with the upstream changes and the chosen gap pieces, PROPOSAL.md, and the
              eval: current folder against the proposal, on the skill's evals plus gap probes. A proposal that
              loses on the existing evals is refused.
  5. Apply    only `update apply --approve <id>`, and only if neither folder changed since the proposal.
"""
import datetime as dt
import difflib
import hashlib
import json
import os
import re
import shutil

from . import check as checkmod, choose, eval as evalmod, fetch as fetchmod, licence as licmod, read as readmod, scan as scanmod
from .merge import renamed_skill_file, vendored_name, rebase_paths, _dir_summary
from .util import (LOCK_NAME, EngineError, estimate_tokens, folder_hash, iter_files, log, parse_frontmatter, parse_sections,
                   read_json, run, sha256_file, split_frontmatter, write_json, write_text, block_sections)

README_SRC = re.compile(r"https?://github\.com/([A-Za-z0-9_.-]+)/([A-Za-z0-9_.-]+?)(?:\.git)?(?=[\s,)`/]|$)[^\n]{0,80}?(?:commit|@)\s*`?([0-9a-f]{7,40})")


# ------------------------------------------------------------------ 1. lock
def adopt(skill_dir):
    """Lock entries for a hand-made merged skill, from what its per-source READMEs record."""
    entries = {}
    for d in sorted(os.listdir(skill_dir)):
        readme = os.path.join(skill_dir, d, "README.md")
        if not os.path.isfile(readme):
            continue
        text = open(readme, encoding="utf-8").read()
        m = README_SRC.search(text)
        if not m:
            continue
        repo = f"{m.group(1)}/{m.group(2)}"
        sha, date = fetchmod.resolve_ref(repo, m.group(3))
        root, meta = fetchmod.stage_github({"repo": repo, "ref": sha})
        installed = {sha256_file(ap): rel for rel, ap in iter_files(os.path.join(skill_dir, d))}
        best = None
        for sp in fetchmod.find_skill_dirs(root):
            h = sha256_file(os.path.join(root, sp, "SKILL.md"))
            if h in installed:
                best = (sp, installed[h])
                break
        if best is None:
            dirs = fetchmod.find_skill_dirs(root)
            named = [x for x in dirs if os.path.basename(x).replace("-", "") in d.replace("-", "") or d.replace("-", "") in os.path.basename(x).replace("-", "")]
            if len(dirs) == 1 or len(named) == 1:
                best = ((named or dirs)[0], None)
            else:
                raise EngineError(f"{d}/README.md names {repo} but its skill path is unclear: {dirs[:8]}. Pass --map {d}=<path>")
        sp, renamed = best
        entries[d] = {"source": repo, "sourceUrl": f"https://github.com/{repo}", "sourceType": "github", "ref": sha,
                      "skillPath": (sp + "/" if sp != "." else "") + "SKILL.md", "folder": d, "use": "flatten",
                      "renamedSkillFile": renamed, "date": date, "adopted": True}
    if not entries:
        raise EngineError(f"{skill_dir}: no per-source README names a GitHub source and commit, so there is nothing to adopt")
    return {"version": 1, "skill": {"name": os.path.basename(os.path.normpath(skill_dir)), "mode": "adopted"}, "skills": entries}


def load_or_adopt(skill_dir, adopt_ok):
    p = os.path.join(skill_dir, LOCK_NAME)
    if os.path.isfile(p):
        return read_json(p), False
    if not adopt_ok:
        raise EngineError(f"{skill_dir} has no {LOCK_NAME}; pass --adopt to build one from its per-source READMEs")
    return adopt(skill_dir), True


# ------------------------------------------------------------------ 2. upstream
def upstream(skill_dir, entry, ref=None, workdir=None):
    """What changed upstream for one locked source since its locked commit."""
    repo, old = entry["source"], entry["ref"]
    sp_dir = os.path.dirname(entry.get("skillPath") or "SKILL.md")
    new, date = fetchmod.resolve_ref(repo, ref)
    res = {"source": repo, "folder": entry.get("folder"), "old": old, "new": new, "date": date, "changed": [],
           "local_edits": [], "scan": None, "licence": None, "status": "up to date" if new == old else "changed"}
    old_root, _ = fetchmod.stage_github({"repo": repo, "ref": old})
    folder = os.path.join(skill_dir, entry.get("folder") or "")
    renamed = entry.get("renamedSkillFile") or renamed_skill_file(entry.get("folder") or "")
    # local edits: installed copies that differ from the source at the locked commit
    up_old = os.path.join(old_root, sp_dir)
    for rel, ap in iter_files(folder):
        if rel in ("README.md", "LICENSE", "NOTICE"):
            continue  # the compiler's own files
        src_rel = "SKILL.md" if rel == renamed else rel[len("SOURCE-"):] if rel.startswith("SOURCE-") and "/" not in rel else rel
        sp = os.path.join(up_old, src_rel)
        if os.path.isfile(sp) and sha256_file(sp) != sha256_file(ap):
            res["local_edits"].append(rel)
    if new == old:
        return res
    diffdir = os.path.join(workdir or fetchmod.STAGING_DIR, "diff", repo.replace("/", "__"))
    fetchmod.fetch_commits(repo, [old, new], diffdir)
    # -z and quotePath=false: names come back raw and NUL-separated, never quoted into something like ../"..."
    out = run(["git", "-c", "core.quotePath=false", "-C", diffdir, "diff", "--name-status", "--no-renames", "-z",
               old, new, "--", sp_dir or "."], timeout=120)
    new_root, _ = fetchmod.stage_github({"repo": repo, "ref": new})
    rec_files = {f["path"]: f for f in readmod.read_tree(os.path.join(new_root, sp_dir))}
    parts = [p for p in out.split("\0") if p]
    for status, path in zip(parts[0::2], parts[1::2]):
        rel = os.path.relpath(path, sp_dir) if sp_dir else path
        if rel.startswith("..") or os.path.isabs(rel):
            continue  # outside the skill's folder
        f = rec_files.get(rel)
        res["changed"].append({"status": status[0], "path": rel, "sha256": f["sha256"] if f else None,
                               "read": bool(f and f.get("read")), "bytes": f["size"] if f else 0,
                               "kind": f["kind"] if f else None, "encoding": f.get("encoding") if f else None,
                               "nul_bytes": f.get("nul_bytes") if f else None})
    changed_records = [rec_files[c["path"]] for c in res["changed"] if c["path"] in rec_files]
    findings, summary = scanmod.scan_files(changed_records)
    res["scan"] = {"summary": summary, "findings": [x for x in findings if x["severity"] != "info"]}
    new_fm = {}
    skill_md = os.path.join(new_root, sp_dir, "SKILL.md")
    if os.path.isfile(skill_md):
        from .util import parse_frontmatter as _pf
        new_fm = _pf(split_frontmatter(open(skill_md, encoding="utf-8", errors="replace").read())[0])[0]
    lic_rec = {"licence_files": readmod._licence_files(new_root, os.path.join(new_root, sp_dir))[0],
               "notice_files": [], "frontmatter": new_fm}
    res["licence"] = {k: v for k, v in licmod.assess(lic_rec).items() if k != "file_text"}
    res["new_root"], res["sp_dir"] = new_root, sp_dir
    res["findings_by_file"] = {}
    for fd in findings:
        res["findings_by_file"].setdefault(fd["file"], []).append(fd)
    if scanmod.blocked(findings):
        res["status"] = "blocked"
    elif res["licence"]["verdict"] != "flatten":
        res["status"] = "licence changed"
    return res


# ------------------------------------------------------------------ 3. gap
def search_candidates(gap, limit=8):
    """GitHub code search for skills that name the gap. Returns specs owner/repo:path."""
    seen, out = set(), []
    for q in (gap, gap + " design", gap + " ui"):
        try:
            raw = run(["gh", "search", "code", "--filename", "SKILL.md", q, "--limit", "20", "--json", "repository,path"], timeout=60)
        except EngineError:
            continue
        for r in json.loads(raw or "[]"):
            repo, path = r["repository"]["nameWithOwner"], os.path.dirname(r["path"])
            if repo in seen:
                continue
            seen.add(repo)
            out.append(f"{repo}:{path}" if path else repo)
        if len(out) >= limit:
            break
    return out[:limit]


def score_against_gap(texts, gap):
    sc = choose.Scorer([t for _, t in texts], job="", gap=gap).score_all()
    return [(label, s["gap"] or 0.0) for (label, _), s in zip(texts, sc)]


def score_gap(cands, current_sections, gap):
    """One scoring pass over every candidate piece and the installed skill's sections, so scores compare:
    1.00 is the best piece found anywhere. Returns the installed skill's best score."""
    docs = [(("cand", i, j), p["text"]) for i, c in enumerate(cands) if not c.get("error") for j, p in enumerate(c["pieces"])]
    docs += [(("cur", k, 0), s["text"]) for k, s in enumerate(current_sections)]
    if not docs:
        return 0.0
    scored = score_against_gap(docs, gap)
    best_current = 0.0
    for (kind, i, j), g in scored:
        if kind == "cand":
            cands[i]["pieces"][j]["gap"] = round(g, 3)
        else:
            best_current = max(best_current, g)
    for c in cands:
        if not c.get("error"):
            c["pieces"].sort(key=lambda p: -p["gap"])
            c["pieces"] = c["pieces"][:12]
            c["best_gap"] = c["pieces"][0]["gap"] if c["pieces"] else 0.0
    return round(best_current, 3)


def gap_candidates(specs, gap, exclude_repos=()):
    """Fetch, read, scan and licence each candidate; score its markdown sections against the gap."""
    out = []
    for spec in specs:
        try:
            src = fetchmod.fetch(spec)
        except EngineError as e:
            out.append({"spec": spec, "error": str(e)})
            continue
        if not src["skill_paths"]:
            out.append({"spec": spec, "error": "no SKILL.md"})
            continue
        if src["meta"]["source"] in exclude_repos:
            continue
        for rec in readmod.read_source(src):
            findings, summary = scanmod.scan_files(rec["files"])
            lic = licmod.assess(rec)
            units = []
            for s in rec["sections"]:
                if not choose.TRIGGER_TITLE_RE.search(s["title"]):
                    units.append(("SKILL.md", s))
            for f in rec["files"]:
                if f["kind"] == "markdown" and f["path"] != "SKILL.md" and f["size"] < 200_000 and not choose.REPO_DOCS.search(f["path"]):
                    for s in readmod.reference_sections(rec, f["path"]):
                        units.append((f["path"], s))
            pieces = [{"file": p, "id": s["id"], "title": s["title"], "lines": [s["start"], s["end"]],
                       "tokens": estimate_tokens(s["text"]), "gap": 0.0, "text": s["text"]} for p, s in units]
            blocked = scanmod.blocked(findings)
            verdict = "excluded" if blocked else ("flatten" if lic["verdict"] == "flatten" else "reference")
            out.append({"spec": rec["spec"], "alias": rec["alias"], "source": rec["meta"]["source"], "ref": rec["meta"]["sha"],
                        "date": rec["meta"].get("date"), "skill_path": rec["skill_path"], "staging": rec["skill_root"],
                        "repo_root": rec["root"], "licence": {k: v for k, v in lic.items() if k != "file_text"},
                        "scan": {"summary": summary, "findings": [x for x in findings if x["severity"] != "info"]},
                        "verdict": verdict, "why": (f"scanner: {blocked[0]['label']} at {blocked[0]['file']}:{blocked[0]['line']}" if blocked
                                                    else f"licence {lic['spdx']}, so it is named, not copied" if verdict == "reference" else ""),
                        "files": rec["files"], "description": str((rec.get("frontmatter") or {}).get("description") or ""),
                        "name": choose.safe_name((rec.get("frontmatter") or {}).get("name"), rec["alias"]),
                        "best_gap": 0.0, "pieces": pieces,
                        "files_read": rec["files_read"], "bytes_read": rec["bytes_read"]})
    return out


# ------------------------------------------------------------------ 4. propose
def _insert_after_section(text, anchor_title, block):
    lines = text.splitlines(keepends=True)
    body_start = len(text) - len(split_frontmatter(text)[1])
    offset = text[:body_start].count("\n")
    secs = parse_sections(split_frontmatter(text)[1])
    target = next((s for s in secs if s["title"] == anchor_title), None)
    if target is None:
        return text.rstrip() + "\n\n" + block
    end = target["end"] + offset
    # end of that section including its children
    for s in secs:
        if s["start"] > target["start"] and s["level"] <= target["level"] and s["level"] > 0:
            end = s["start"] - 1 + offset
            break
    else:
        end = len(lines)
    return "".join(lines[:end]).rstrip() + "\n\n" + block.rstrip() + "\n\n" + "".join(lines[end:]).lstrip("\n")


def _under(root, *parts):
    root = os.path.abspath(root)
    p = os.path.abspath(os.path.join(root, *parts))
    if os.path.commonpath([p, root]) != root:
        raise EngineError(f"refusing a path outside {root}: {p}")
    return p


def build_proposal(skill_dir, lock, ups, cands, gap, workdir, take=2, pieces_per=3, plain=False):
    name = lock["skill"]["name"]
    prop = _under(workdir, "proposal", name)
    if os.path.exists(prop):
        shutil.rmtree(prop)
    shutil.copytree(skill_dir, prop, ignore=shutil.ignore_patterns(".git", "__pycache__", ".DS_Store"))
    changes = []
    fixed = requote_frontmatter(os.path.join(prop, "SKILL.md"))
    if fixed:
        changes.append(f"SKILL.md frontmatter re-quoted so strict YAML loaders read it ({fixed})")
    # upstream changes, never over a local edit
    for u in ups:
        if u["status"] != "changed":
            continue
        folder = _under(prop, u["folder"])
        entry = lock["skills"][u["folder"]]
        renamed = entry.get("renamedSkillFile") or renamed_skill_file(u["folder"])
        kept = set(entry.get("kept") or [])
        dec_files = (lock.get("decisions") or {}).get("files") or {}
        for c in u["changed"]:
            target_rel = renamed if c["path"] == "SKILL.md" else vendored_name(u["folder"], c["path"])
            if target_rel in u["local_edits"]:
                changes.append(f"kept the local edit of `{u['folder']}/{target_rel}`; upstream changed it too, merge by hand")
                continue
            dest = os.path.normpath(os.path.join(folder, target_rel))
            if not dest.startswith(os.path.normpath(folder) + os.sep):
                changes.append(f"refused `{c['path']}`: it would land outside `{u['folder']}/`")
                continue
            if c["status"] != "D" and not c.get("read"):
                changes.append(f"not taken `{u['folder']}/{target_rel}`: the scanner could not read it")
                continue
            if dec_files.get(f"{u['folder']}:{c['path']}", {}).get("keep") is False or (kept and c["status"] == "M" and c["path"] not in kept):
                changes.append(f"not taken `{u['folder']}/{target_rel}`: the compiled skill leaves this file out")
                continue
            if c["status"] == "A":
                ok, why = choose.file_disposition({"path": c["path"], "kind": c["kind"], "encoding": c["encoding"],
                                                   "nul_bytes": c["nul_bytes"]}, u.get("findings_by_file", {}), "flatten")
                if not ok:
                    changes.append(f"not added `{u['folder']}/{target_rel}`: {why}")
                    continue
            if c["status"] == "D":
                if os.path.exists(dest):
                    os.remove(dest)
                    changes.append(f"removed `{u['folder']}/{target_rel}` (deleted upstream)")
                continue
            if c["status"] == "A" and not os.path.isdir(os.path.dirname(dest)):
                changes.append(f"not added `{u['folder']}/{target_rel}`: new upstream file outside the copied folders")
                continue
            os.makedirs(os.path.dirname(dest), exist_ok=True)
            shutil.copyfile(os.path.join(u["new_root"], u["sp_dir"], c["path"]), dest)
            changes.append(f"{'added' if c['status'] == 'A' else 'updated'} `{u['folder']}/{target_rel}` from {u['source']} @ {u['new'][:7]}")
    # gap pieces
    chosen = [c for c in cands if not c.get("error") and c["verdict"] != "excluded" and c["best_gap"] > 0]
    chosen.sort(key=lambda c: -c["best_gap"])
    added, refd = [], []
    for c in chosen[:take]:
        alias = _free_alias(prop, c["alias"])
        dest = os.path.join(prop, alias)
        os.makedirs(dest)
        if c["verdict"] == "flatten":
            for f in c["files"]:
                keep, why = choose.file_disposition(f, {}, "flatten")
                if not keep or f["kind"] in ("binary-exec", "archive", "symlink"):
                    continue
                rel = vendored_name(alias, f["path"])
                os.makedirs(os.path.dirname(os.path.join(dest, rel)), exist_ok=True)
                shutil.copyfile(os.path.join(c["staging"], f["path"]), os.path.join(dest, rel))
            if c["licence"].get("file"):
                shutil.copyfile(os.path.join(c["repo_root"], c["licence"]["file"]), os.path.join(dest, "LICENSE"))
            if c["licence"].get("notice"):
                write_text(os.path.join(dest, "NOTICE"), c["licence"]["notice"])
            added.append((alias, c))
        else:
            refd.append((alias, c))
        write_text(os.path.join(dest, "README.md"), _gap_readme(c, alias, gap))
        changes.append(f"{'added' if c['verdict'] == 'flatten' else 'named (not copied)'} `{alias}/` from {c['source']} @ {(c['ref'] or '')[:7]} for the gap")
    # SKILL.md: a short block beside the section that already covers the gap best
    skill_md = os.path.join(prop, "SKILL.md")
    text = open(skill_md, encoding="utf-8").read()
    secs = [s for s in parse_sections(split_frontmatter(text)[1]) if s["level"] in (2, 3)]
    anchor = None
    if secs and gap:
        scored = score_against_gap([(s["title"], s["text"]) for s in secs], gap)
        anchor = max(scored, key=lambda x: x[1])[0] if scored else None
    if added or refd:
        block = [f"**More for {gap} (added by update on {dt.date.today().isoformat()}):**", ""]
        for alias, c in added:
            for p in c["pieces"][:pieces_per]:
                where = f"{alias}/{vendored_name(alias, p['file'])}"
                block.append(f"- `{where}`, \"{p['title']}\": {_gist(p['text'])}")
        for alias, c in refd:
            block.append(f"- `{alias}` ({c['source']}; {c['why']}). Install it and run it for {gap}; see `{alias}/README.md`.")
        block_text = "\n".join(block) + "\n"
        if plain:  # house style applies to the lines this run writes, never to the installed text around them
            from .util import plain_dashes
            block_text = plain_dashes(block_text)
        text = _insert_after_section(text, anchor, block_text)
        write_text(skill_md, text)
        changes.append(f"SKILL.md: {len(block) - 2} pointer line(s) added after \"{anchor}\"")
    return prop, changes, added, refd, anchor


def requote_frontmatter(path):
    """A plain YAML value holding ': ' fails strict loaders (skills-ref; Claude Code then loads the skill with no
    fields). Re-emit the same keys and values, quoted where needed. Returns what was wrong, or None."""
    from .util import dump_frontmatter
    text = open(path, encoding="utf-8").read()
    block, body = split_frontmatter(text)
    if block is None:
        return None
    data, problems = parse_frontmatter(block)
    bad = [p for p in problems if "quote it" in p or "flow style" in p]
    if not bad or any(isinstance(v, (dict, list)) for k, v in data.items() if k != "metadata"):
        return None
    write_text(path, dump_frontmatter(data) + body)
    return "; ".join(bad)


def _gist(text, n=150):
    body = "\n".join(l for l in text.splitlines()[1:] if l.strip() and not l.strip().startswith(("#", "|", "```")))
    body = re.sub(r"[*_`]", "", body)
    body = re.sub(r"\s+", " ", body).strip()
    return (body[: n - 3].rsplit(" ", 1)[0] + "...") if len(body) > n else body


def _free_alias(prop, alias):
    a, n = alias, 2
    while os.path.exists(os.path.join(prop, a)):
        a = f"{alias}-{n}"
        n += 1
    return a


def _gap_readme(c, alias, gap):
    lic = c["licence"]
    lines = [f"# {c['name']} (from {c['source']})", ""]
    if c["verdict"] == "flatten":
        lines.append(f"Source: https://github.com/{c['source']}, commit {(c['ref'] or '')[:7]}" + (f" ({c['date']})" if c.get("date") else "") +
                     f", {lic['spdx']} licence (`LICENSE`). Added by an update run for the gap \"{gap}\", after every file was read in full and scanned.")
    else:
        lines.append(f"Source: https://github.com/{c['source']}, commit {(c['ref'] or '')[:7]}. **Referenced only:** {c['why']}.")
        lines += ["", "Install the original:", "", "```bash", f"npx skills add {c['source']}", f"gh skill install {c['source']}", "```"]
    sm = c["scan"]["summary"]
    lines += ["", "## Read and scanned", "", f"- {c['files_read']} files, {c['bytes_read']:,} bytes, read in full.",
              f"- Scanner: {sm['block']} blocking, {sm['review']} to review, {sm['info']} informational."]
    lines += ["", f"## Why it is here", "", f"Its best section for \"{gap}\" scored {c['best_gap']:.2f} against the gap. Top pieces:", ""]
    for p in c["pieces"][:5]:
        lines.append(f"- `{p['file']}` \"{p['title']}\" ({p['gap']:.2f})")
    lines += ["", "## Licence duties", "", f"- {lic.get('duties') or 'Not copied.'}"]
    return "\n".join(lines) + "\n"


# ------------------------------------------------------------------ the run
def plan_update(skill_dir, workdir, gap="", candidates=(), from_radar=None, search=False, adopt_ok=False, ref=None,
                evals=None, take=2, tolerance=0.05, plain=False):
    skill_dir = os.path.abspath(os.path.expanduser(skill_dir))
    os.makedirs(workdir, exist_ok=True)
    before = folder_hash(skill_dir)
    lock, adopted = load_or_adopt(skill_dir, adopt_ok)
    ups = []
    for alias, entry in lock["skills"].items():
        if entry.get("sourceType") == "github" and entry.get("use") == "flatten":
            log(f"upstream: {entry['source']} since {entry['ref'][:7]}")
            ups.append(upstream(skill_dir, entry, ref=ref, workdir=workdir))
    cand_specs = list(candidates)
    if from_radar:
        from .radar import parse_report, report_path
        entries = parse_report(report_path(from_radar))
        scored = score_against_gap([(e["spec"], e["description"]) for e in entries], gap) if gap else []
        cand_specs += [s for s, g in sorted(scored, key=lambda x: -x[1])[:5] if g > 0]
    if search and gap:
        cand_specs += search_candidates(gap)
    locked_repos = {e["source"] for e in lock["skills"].values()}
    cand_specs = list(dict.fromkeys(cand_specs))
    log(f"gap candidates: {len(cand_specs)}")
    cands = gap_candidates(cand_specs, gap, exclude_repos=locked_repos) if gap else []
    # how the installed skill scores on the gap today, on the same scale as the candidates
    text = open(os.path.join(skill_dir, "SKILL.md"), encoding="utf-8").read()
    secs = [s for s in parse_sections(split_frontmatter(text)[1]) if s["level"] in (2, 3)]
    current_gap = score_gap(cands, secs, gap) if gap else None
    prop, changes, added, refd, anchor = build_proposal(skill_dir, lock, ups, cands, gap, workdir, take=take, plain=plain)
    # lock for the proposal: refresh every changed source, not just its ref, so the proposal lock describes
    # the proposal's own files and a later update does not compare against stale hashes
    new_lock = dict(lock)
    new_lock["skills"] = dict(lock["skills"])
    for u in ups:
        if u["status"] != "changed":
            continue
        entry = dict(new_lock["skills"][u["folder"]])
        entry.update({"ref": u["new"], "date": u["date"], "licence": {k: v for k, v in u["licence"].items()
                                                                     if k in ("spdx", "verdict", "file")}})
        new_recs = readmod.read_tree(os.path.join(u["new_root"], u["sp_dir"]))
        entry["files"] = {r["path"]: r["sha256"] for r in new_recs if r.get("sha256")}
        entry["read"] = {"files": len(new_recs), "bytes": sum(r.get("size") or 0 for r in new_recs)}
        entry["scan"] = u["scan"]["summary"]
        entry["computedHash"] = folder_hash(os.path.join(u["new_root"], u["sp_dir"]))
        kept = set(entry.get("kept") or [])
        for c in u["changed"]:
            target_rel = (entry.get("renamedSkillFile") or renamed_skill_file(u["folder"])) if c["path"] == "SKILL.md" \
                else vendored_name(u["folder"], c["path"])
            dest = os.path.join(prop, u["folder"], target_rel)
            if c["status"] == "D":
                kept.discard(c["path"])
            elif os.path.exists(dest):
                kept.add(c["path"])
        entry["kept"] = sorted(kept)
        new_lock["skills"][u["folder"]] = entry
    for alias, c in added + refd:
        entry = {"source": c["source"], "sourceUrl": f"https://github.com/{c['source']}", "sourceType": "github",
                 "ref": c["ref"], "skillPath": (c["skill_path"].rstrip("/") + "/" if c["skill_path"] != "." else "") + "SKILL.md",
                 "computedHash": folder_hash(c["staging"]), "folder": alias,
                 "use": "flatten" if c["verdict"] == "flatten" else "reference",
                 "licence": {"spdx": c["licence"]["spdx"], "verdict": c["licence"]["verdict"]},
                 "read": {"files": c["files_read"], "bytes": c["bytes_read"]},
                 "scan": c["scan"]["summary"],
                 "files": {f["path"]: f["sha256"] for f in c["files"] if f.get("sha256")},
                 "kept": sorted(f["path"] for f in c["files"] if f.get("keep") and f.get("kind") != "symlink")}
        if c.get("date"):
            entry["date"] = c["date"]
        entry["gap"] = gap
        new_lock["skills"][alias] = entry
    new_lock["skills"] = dict(sorted(new_lock["skills"].items()))
    from .util import TOOL_NAME, TOOL_URL, TOOL_VERSION
    new_lock["tool"] = {"name": TOOL_NAME, "version": TOOL_VERSION, "url": TOOL_URL}
    new_lock["skill"] = {**lock["skill"], "computedHash": folder_hash(prop, exclude={LOCK_NAME})}
    # eval: current vs proposal
    eval_paths = list(evals or [])
    own_evals = os.path.join(skill_dir, "evals", "evals.json")
    if os.path.isfile(own_evals):
        eval_paths.append(own_evals)
    old_evals = evalmod.load_eval_set(eval_paths) if eval_paths else []
    gap_evals = _gap_probes(added, gap)
    arms_cur, arms_new = evalmod.folder_arm("originals", skill_dir), evalmod.folder_arm("compiled", prop)
    for alias, c in refd:  # a referenced skill stays installed, so its text is reachable in both arms
        arms_new["reach"].extend(evalmod._text_files(c["staging"]))
    old_static = evalmod.static_tier(old_evals, [arms_cur, arms_new]) if old_evals else None
    gap_static = evalmod.static_tier(gap_evals, [arms_cur, arms_new]) if gap_evals else None
    verdict, reasons = "pass", []
    if old_static and old_static["evals_scored"]:
        o, n = old_static["totals"]["originals"]["coverage"], old_static["totals"]["compiled"]["coverage"]
        if n + 1e-9 < o:
            verdict = "refuse"
            reasons.append(f"the proposal loses on the skill's existing evals ({n:.2f} against {o:.2f})")
        else:
            reasons.append(f"no loss on the existing evals ({n:.2f}, was {o:.2f})")
    else:
        reasons.append("the skill has no evals of its own; pass --evals to guard against a regression")
    if gap_static and gap_static["evals_scored"]:
        reasons.append(f"gap probes reachable: {gap_static['totals']['compiled']['coverage']:.2f}, was {gap_static['totals']['originals']['coverage']:.2f}")
    checks_new = checkmod.run_checks(prop, expect_lock=False)
    checks_cur = {c["name"]: c["ok"] for c in checkmod.run_checks(skill_dir, expect_lock=False)}
    blocking = [c for c in checks_new if not c["ok"] and checks_cur.get(c["name"], True)]
    for c in checks_new:
        if not c["ok"] and not checks_cur.get(c["name"], True):
            c["detail"] += " (already failing before this update; not caused by it)"
    if blocking:
        verdict = "refuse"
        reasons += [f"check {c['name']} fails only after the update: {c['detail']}" for c in blocking]
    if old_static:
        new_lock["eval"] = {"verdict": verdict, "tiers": ["static"],
                            "originals": old_static["totals"]["originals"],
                            "compiled": old_static["totals"]["compiled"],
                            "eval_set_hash": evalmod.eval_set_hash(old_evals), "tolerance": tolerance}
    write_json(os.path.join(prop, LOCK_NAME), new_lock)
    pid = hashlib.sha256((folder_hash(prop) + before).encode()).hexdigest()[:12] if verdict == "pass" else None
    state = {"skill_dir": skill_dir, "skill_hash": before, "proposal": prop, "proposal_hash": folder_hash(prop),
             "id": pid, "verdict": verdict, "adopted": adopted}
    write_json(os.path.join(workdir, "proposal.json"), state)
    diff = _diff(os.path.join(skill_dir, "SKILL.md"), os.path.join(prop, "SKILL.md"))
    md = _proposal_md(lock, adopted, ups, cands, gap, current_gap, changes, old_static, gap_static, checks_new, verdict, reasons, pid, diff, skill_dir, workdir)
    if plain:
        from .util import plain_dashes
        md = plain_dashes(md)
    write_text(os.path.join(workdir, "PROPOSAL.md"), md)
    return state, md


def _gap_probes(added, gap):
    evals = []
    from .choose import rules_of
    from .util import content_words
    for alias, c in added:
        for p in c["pieces"][:3]:
            rules = [r for _, r in rules_of(p["text"]) if len(content_words(r)) >= 4]
            if not rules:
                continue
            needs = [" ".join(re.sub(r"[`*_]", "", r).split()[:6]) for r in rules[:2]]
            evals.append({"id": len(evals) + 1, "name": f"gap-{alias}-{p['id']}"[:70], "prompt": f"{gap}: {p['title']}",
                          "needs": needs, "expectations": [], "origin": "gap-probe"})
    return evals


def _diff(a, b):
    la = open(a, encoding="utf-8").read().splitlines()
    lb = open(b, encoding="utf-8").read().splitlines()
    return "\n".join(difflib.unified_diff(la, lb, "SKILL.md (installed)", "SKILL.md (proposed)", lineterm="", n=2))


def _proposal_md(lock, adopted, ups, cands, gap, current_gap, changes, old_static, gap_static, checks, verdict, reasons, pid, diff, skill_dir, workdir):
    L = [f"# Update proposal for `{lock['skill']['name']}`", "", f"Installed skill: `{skill_dir}`. Nothing there has been changed.", ""]
    L.append(f"**Verdict: {verdict.upper()}.** " + " ".join(r[0].upper() + r[1:] + "." for r in reasons))
    if pid:
        L += ["", f"To apply: `update apply --work {workdir} --approve {pid}`. A backup of the installed folder is kept in the work folder."]
    else:
        L += ["", "No approval id: this proposal is refused."]
    if adopted:
        L += ["", "The skill had no lockfile, so one was adopted from what its per-source READMEs record; the proposal carries it."]
    L += ["", "## Upstream", "", "| Source | Locked | Now | Status | Changed files (all re-read and re-scanned) | Local edits kept |", "| --- | --- | --- | --- | --- | --- |"]
    for u in ups:
        changed = ", ".join(f"{c['status']} `{c['path']}`" for c in u["changed"][:8]) + (f" and {len(u['changed']) - 8} more" if len(u["changed"]) > 8 else "")
        L.append(f"| {u['source']} | {u['old'][:7]} | {u['new'][:7]} | {u['status']} | {changed or 'none'} | "
                 f"{', '.join('`' + e + '`' for e in u['local_edits'][:6]) or 'none'} |")
        if u.get("scan") and u["scan"]["findings"]:
            for f in u["scan"]["findings"][:8]:
                L.append(f"|  | | | {f['severity']} | `{f['file']}:{f['line']}` {f['label']} | |")
    if gap:
        L += ["", f"## The gap: \"{gap}\"", "", f"Scores are on one scale: 1.00 is the best piece found for the gap anywhere. The installed SKILL.md's best section scores {current_gap:.2f}.", "",
              "| Candidate | Licence | Scan (block / review) | Verdict | Best section for the gap | Score |", "| --- | --- | --- | --- | --- | --- |"]
        for c in sorted([c for c in cands if not c.get("error")], key=lambda c: -c["best_gap"]):
            best = c["pieces"][0] if c["pieces"] else None
            L.append(f"| {c['source']}:{c['skill_path']} | {c['licence']['spdx']} | {c['scan']['summary']['block']} / {c['scan']['summary']['review']} | "
                     f"{c['verdict']}{' (' + c['why'] + ')' if c['why'] else ''} | {('`' + best['file'] + '` ' + best['title'][:40]) if best else ''} | {c['best_gap']:.2f} |")
        for c in [c for c in cands if c.get("error")]:
            L.append(f"| {c['spec']} | | | skipped: {c['error'][:80]} | | |")
    L += ["", "## What the proposal changes", ""] + ([f"- {c}" for c in changes] or ["- Nothing."])
    L += ["", "## Eval: installed against proposed", ""]
    for label, st in (("Existing evals", old_static), ("Gap probes", gap_static)):
        if not st:
            continue
        t = st["totals"]
        L.append(f"- {label} ({st['evals_scored']}): reachable {t['originals']['coverage']:.2f} now, {t['compiled']['coverage']:.2f} proposed; "
                 f"context {t['originals']['context_tokens']:,} tokens now, {t['compiled']['context_tokens']:,} proposed.")
    L += ["", "## Checks on the proposal", ""] + [f"- {'PASS' if c['ok'] else 'FAIL'} {c['name']}: {c['detail']}" for c in checks]
    L += ["", "## SKILL.md diff", "", "```diff", diff or "(no change)", "```", ""]
    return "\n".join(L)


def apply_update(workdir, approve, to=None, force=False):
    state = read_json(os.path.join(workdir, "proposal.json"))
    if not state.get("id"):
        raise EngineError("this proposal was refused; there is nothing to apply")
    if approve != state["id"]:
        raise EngineError(f"approval id {approve!r} does not match this proposal ({state['id']})")
    target = os.path.abspath(os.path.expanduser(to or state["skill_dir"]))
    workdir_abs, prop_abs = os.path.abspath(workdir), os.path.abspath(state["proposal"])
    forbidden = {os.path.abspath(os.sep), os.path.abspath(os.path.expanduser("~")), os.path.abspath(os.getcwd()),
                 workdir_abs, prop_abs}
    if target in forbidden:
        raise EngineError(f"refusing to replace {target}: it is the working folder, the proposal, the current folder or home")
    protected = (workdir_abs, prop_abs, os.path.abspath(os.path.expanduser("~")), os.path.abspath(os.getcwd()),
                 os.path.abspath(state["skill_dir"]))
    for root in protected:
        if target != root and os.path.commonpath([target, root]) == target:
            raise EngineError(f"refusing to replace {target}: it contains {root}")
    if folder_hash(state["proposal"]) != state["proposal_hash"]:
        raise EngineError("the proposal folder changed after it was made; run update again")
    if os.path.abspath(target) == os.path.abspath(state["skill_dir"]) and folder_hash(target) != state["skill_hash"]:
        raise EngineError("the installed skill changed after the proposal was made; run update again")
    if os.path.exists(target) and target != os.path.abspath(state["skill_dir"]) and not force:
        raise EngineError(f"{target} exists; pass --force to replace it, or choose another --to")
    backup = os.path.join(workdir, "backup-" + dt.datetime.now().strftime("%Y%m%d-%H%M%S"))
    if os.path.exists(target):
        shutil.copytree(target, backup)
        shutil.rmtree(target)
    shutil.copytree(state["proposal"], target)
    return target, backup
