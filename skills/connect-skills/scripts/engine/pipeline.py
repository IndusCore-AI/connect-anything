"""The pipeline shared by connect, compile and update: fetch, read, scan, licence, choose, then merge, eval,
lock, check, and emit only when the gate passes."""
import json
import os
import re
import shutil
import sys

from . import check as checkmod
from . import choose, decisions as decmod, eval as evalmod, fetch as fetchmod, licence as licmod, lock as lockmod, merge, read as readmod, scan as scanmod
from .util import (LOCK_NAME, EngineError, log, read_json, sha256_bytes, skill_name_ok, to_skill_name, write_json, write_text)


def prepare(specs, mode, own=(), allow=(), strip=(), refresh=False):
    """Fetch, read, scan and assess every source. Returns (records, assessments, scans)."""
    recs, assessments, scans = [], {}, {}
    for spec in specs:
        src = fetchmod.fetch(spec, refresh=refresh)
        if len(src["skill_paths"]) > 1 and mode != "compile":
            raise EngineError(f"{src['spec']} holds {len(src['skill_paths'])} skills; name one with owner/repo:path. "
                              f"Paths: {', '.join(src['skill_paths'][:12])}")
        if not src["skill_paths"]:
            log(f"skip {src['spec']}: no SKILL.md in it (not a skill)")
            continue
        for rec in readmod.read_source(src):
            alias = rec["alias"]
            n = 2
            while alias in assessments:
                alias = f"{rec['alias']}-{n}"
                n += 1
            rec["alias"] = alias
            findings, summary = scanmod.scan_files(rec["files"], allow=set(allow) | set(strip))
            strip_ranges = []
            for f in findings:
                if f["id"] in strip:
                    if not f["rule"].startswith("promo"):
                        raise EngineError(f"--strip {f['id']}: only promotional findings can be cut; this is {f['rule']}. "
                                          "Use --allow after a person has read it, or leave the source out.")
                    f["stripped"] = True
                    strip_ranges.append(_strip_range(rec, f))
            rec["strip_ranges"] = strip_ranges
            assessments[alias] = licmod.assess(rec, own=alias in own or rec["spec"] in own)
            scans[alias] = (findings, summary)
            recs.append(rec)
    return recs, assessments, scans


def _strip_range(rec, finding):
    """The section of a markdown file that holds a promotional finding, as a line range to cut."""
    f = next((x for x in rec["files"] if x["path"] == finding["file"]), None)
    if f is None or f["kind"] != "markdown":
        return {"file": finding["file"], "start": None, "end": None, "finding": finding["id"]}
    from .util import parse_sections
    for sec in parse_sections(f["text"], f["path"]):
        if sec["level"] and sec["start"] <= finding["line"] <= sec["end"]:
            return {"file": f["path"], "start": sec["start"], "end": sec["end"], "finding": finding["id"], "title": sec["title"]}
    return {"file": finding["file"], "start": finding["line"], "end": finding["line"], "finding": finding["id"]}


def make_plan(mode, name, specs, job="", gap="", profile_path=None, own=(), allow=(), strip=(), orchestrate=False,
              budget=None, refresh=False, workdir=None, evals=None, compare_to=None, plain_dashes=False, fit_threshold=None):
    if not skill_name_ok(name):
        raise EngineError(f"--name {name!r} must be lowercase letters, digits and single hyphens (it becomes the folder name)")
    profile = choose.load_profile(profile_path)
    job = job or profile.get("job", "")
    gap = gap or profile.get("gap", "")
    recs, assessments, scans = prepare(specs, mode, own=own, allow=allow, strip=strip, refresh=refresh)
    if not recs:
        raise EngineError("no usable source: every spec was empty or not a skill")
    plan = choose.build_plan(mode, name, recs, assessments, scans, profile, job=job, gap=gap, budget=budget,
                             per_repo=3 if mode == "compile" else None)
    by_alias = {r["alias"]: r for r in recs}
    for src in plan["sources"]:
        src["strip_ranges"] = by_alias[src["alias"]].get("strip_ranges", [])
        for rng in src["strip_ranges"]:
            if rng["file"] == "SKILL.md" and rng["start"]:
                for sec in src["sections"]:
                    if not (sec["lines"][1] < rng["start"] or sec["lines"][0] > rng["end"]):
                        sec["action"], sec["why"] = "drop", f"cut: promotional (finding {rng['finding']})"
            elif rng["start"] is None:
                for f in src["files"]:
                    if f["path"] == rng["file"]:
                        f["keep"], f["why"] = False, f"cut: promotional (finding {rng['finding']})"
        if orchestrate and src["mode"] == "flatten":
            src["mode"], src["excluded_reason"] = "reference", "orchestrated: --orchestrate keeps the originals live"
            for f in src["files"]:
                f["keep"], f["why"] = False, "source is referenced, not copied"
            for sec in src["sections"]:
                sec["action"], sec["why"] = "reference", "named only; the original stays installed"
    if mode == "compile" or orchestrate or strip:
        if mode == "compile":
            _compile_fit(plan, fit_threshold if fit_threshold is not None else 0.2)
        plan["duplicates"], plan["conflicts"] = choose.find_pairs(plan["sources"], recs, profile)
    plan["options"]["plain_dashes"] = plain_dashes
    if evals:
        plan["evals"] = [os.path.abspath(os.path.expanduser(e)) for e in evals]
    if compare_to:
        plan["compare_to"] = os.path.abspath(os.path.expanduser(compare_to))
    plan["description"] = plan["description"] or choose.draft_description(plan)
    if workdir:
        save_plan(plan, workdir)
    return plan


SKIP_COPIES = re.compile(r"(^|/)(evals?|tests?|fixtures|examples?|archive|old|versions?|skill-versions|history|benchmarks?|evidence)(/|$)", re.I)


def _compile_fit(plan, threshold):
    """Compile keeps only the candidates that contribute: a section inline, or a strong fit. Version, eval and
    example copies inside a repo are skipped. Every cut carries its reason."""
    for src in plan["sources"]:
        if src["mode"] == "excluded":
            continue
        sp = os.path.dirname(src.get("skillPath") or "")
        if sp and SKIP_COPIES.search(sp):
            src["mode"], src["excluded_reason"], src["excluded_by"] = "excluded", f"a version, eval or example copy inside the repo ({sp})", "copy"
            for f in src["files"]:
                f["keep"] = False
            for s in src["sections"]:
                s["action"], s["why"] = "drop", "candidate skipped"
            continue
        best = max((s.get("score") or 0 for s in src["sections"]), default=0)
        src["fit"] = round(best, 3)
        if best < threshold:
            src["mode"], src["excluded_reason"], src["excluded_by"] = "excluded", f"does not fit the profile (best section score {best:.2f} < {threshold})", "fit"
            for f in src["files"]:
                f["keep"] = False
            for s in src["sections"]:
                s["action"], s["why"] = "drop", "candidate does not fit the profile"
        else:
            for s in src["sections"]:
                if s["action"] == "reference" and (s.get("score") or 0) < threshold / 2:
                    s["action"], s["why"] = "drop", f"score {s.get('score')}: does not fit the profile"
            if not any(s["action"] == "inline" for s in src["sections"]) and best < 2 * threshold:
                src["mode"], src["excluded_reason"], src["excluded_by"] = "excluded", f"nothing from it made the cut (best section {best:.2f}, none inline)", "fit"
                for f in src["files"]:
                    f["keep"] = False
                for s in src["sections"]:
                    s["action"], s["why"] = "drop", "candidate contributes nothing inline"


def save_plan(plan, workdir):
    os.makedirs(workdir, exist_ok=True)
    write_json(os.path.join(workdir, "plan.json"), plan)


def load_plan(workdir):
    plan = read_json(os.path.join(workdir, "plan.json"))
    plan["_workdir"] = os.path.abspath(workdir)
    return plan


def summarize_plan(plan):
    L = [f"plan for `{plan['name']}` ({plan['mode']})"]
    for s in plan["sources"]:
        sm = s["scan"]["summary"]
        inline = sum(1 for x in s["sections"] if x["action"] == "inline")
        ref = sum(1 for x in s["sections"] if x["action"] == "reference")
        kept = sum(1 for f in s["files"] if f["keep"])
        L.append(f"  {s['alias']:<22} {s['mode']:<9} {s['licence']['spdx']:<14} read {s['files_read']} files"
                 f"  scan {sm['block']}/{sm['review']}/{sm['info']}  sections inline {inline}, ref {ref}  files kept {kept}"
                 + (f"  ({s['excluded_reason']})" if s.get("excluded_reason") else ""))
        for f in s["scan"]["findings"]:
            if f["severity"] == "block":
                tag = "stripped" if f.get("stripped") else "allowed" if f.get("allowed") else "BLOCK"
                L.append(f"      {tag} {f['id']} {f['file']}:{f['line']} {f['label']}")
    L.append(f"  conflicts proposed: {len(plan['conflicts'])}, duplicates: {len(plan['duplicates'])}")
    return "\n".join(L)


def files_to_read(plan):
    """The text files the agent must read itself before deciding: kept ones and flagged ones."""
    out = []
    for s in plan["sources"]:
        if s["mode"] == "excluded":
            continue
        flagged = {f["file"] for f in s["scan"]["findings"]}
        for f in s["files"]:
            if f["kind"] in ("markdown", "script", "text") and (f["keep"] or f["path"] in flagged or s["mode"] == "reference"):
                out.append(os.path.join(s["staging"], f["path"]))
    return out


# ------------------------------------------------------------------ build
def build(plan, out=None, live=False, runner=None, model=None, judge_model=None, trials=1, max_cost=None,
          dry_run=False, tolerance=0.05, force=False, emit=True, decisions_path=None):
    workdir = plan["_workdir"]
    name = plan["name"]
    build_dir = os.path.join(workdir, "build", name)
    dpath = decisions_path or os.path.join(workdir, "decisions.json")
    decisions = read_json(dpath) if os.path.isfile(dpath) else None
    if decisions:
        base = os.path.dirname(os.path.abspath(dpath))
        decisions = dict(decisions)
        if decisions.get("overrides"):
            decisions["overrides"] = {k: (v if isinstance(v, dict) or os.path.isabs(v) else os.path.join(base, v))
                                      for k, v in decisions["overrides"].items()}
        unmatched = decmod.apply(plan, decisions)
        for u in unmatched:
            log(f"decision not applied, nothing matches it any more: {u}")
        plan["decisions_unmatched"] = unmatched
    merge.write_folder(plan, build_dir)
    _apply_strips(plan, build_dir)
    eval_paths = list(plan.get("evals") or [])
    source_evals = []
    for s in plan["sources"]:  # the sources' own skill-creator evals join the set (static tier only)
        p = os.path.join(s["staging"], "evals", "evals.json")
        if s["mode"] != "excluded" and os.path.isfile(p):
            source_evals.append(p)
    eval_dir = os.path.join(workdir, "eval")
    result, lines, evals = evalmod.run_eval(plan, build_dir, eval_paths, source_evals=source_evals, live=live, runner_spec=runner, model=model,
                                            judge_model=judge_model, trials=trials, max_cost=max_cost, dry_run=dry_run,
                                            tolerance=tolerance, workdir=eval_dir)
    from .util import plain_dashes as _pd
    clean = (lambda v: json.loads(_pd(json.dumps(v, ensure_ascii=False)))) if plan["options"].get("plain_dashes") else (lambda v: v)
    write_json(os.path.join(build_dir, "evals", "evals.json"),
               clean({"skill_name": name, "evals": [{k: v for k, v in e.items() if k != "origin"} for e in evals]}))
    lines = [(_pd(l) if plan["options"].get("plain_dashes") else l) for l in lines]
    write_text(os.path.join(build_dir, "evals", "scoreboard.md"), "\n".join(lines) + "\n")
    compare = merge.compare_with(plan, build_dir, plan["compare_to"]) if plan.get("compare_to") else None
    style = bool(plan["options"].get("plain_dashes"))
    allowed = allowed_in_output(plan)
    pre = checkmod.run_checks(build_dir, expect_lock=False, house_style=style, allow_where=allowed)
    write_text(os.path.join(build_dir, "MERGE.md"), merge.merge_md(plan, compare=compare, checks=pre, scoreboard=lines))
    lock = lockmod.write_lock(plan, build_dir, eval_result=result, decisions=_portable(decisions, workdir))
    final = checkmod.run_checks(build_dir, expect_lock=True, house_style=style, allow_where=allowed)
    # the generated plan.json stays as it was; the plan with decisions applied is kept beside it
    write_json(os.path.join(workdir, "plan.built.json"), {k: v for k, v in plan.items() if k != "_workdir"})
    report = {"build": build_dir, "verdict": result["verdict"], "reasons": result["reasons"], "checks": final,
              "scoreboard": lines, "lock": lock}
    ok_checks = checkmod.all_ok(final)
    if result["verdict"] != "pass" or not ok_checks:
        report["emitted"] = None
        write_text(os.path.join(workdir, "REFUSED.md"), "\n".join(
            ["# Not emitted", "", *[f"- {r}" for r in result["reasons"]],
             *[f"- check failed: {c['name']}: {c['detail']}" for c in final if not c["ok"]], "", *lines]) + "\n")
        return report
    if dry_run:
        report["emitted"] = None
        report["dry_run"] = True
        return report
    if emit:
        target = os.path.abspath(os.path.expanduser(out or os.path.join(os.getcwd(), name)))
        _emit(build_dir, target, name, force)
        report["emitted"] = target
        refused = os.path.join(workdir, "REFUSED.md")
        if os.path.exists(refused):
            os.remove(refused)
    return report


def allowed_in_output(plan):
    """(path in the compiled folder, line, rule) for every finding a person allowed at plan time."""
    out = set()
    for s in plan["sources"]:
        for f in s["scan"]["findings"]:
            if f.get("allowed") and not f.get("stripped"):
                out.add((f"{s['alias']}/{merge.vendored_name(s['alias'], f['file'])}", f["line"], f["rule"]))
    return out


def _portable(decisions, workdir):
    """Decisions as the lock carries them: override files inlined, so update can re-apply them anywhere."""
    if not decisions:
        return None
    d = dict(decisions)
    if d.get("overrides"):
        inl = {}
        for k, v in d["overrides"].items():
            path = v if os.path.isabs(v) else os.path.join(workdir, v)
            inl[k] = {"text": open(path, encoding="utf-8").read()} if os.path.isfile(path) else v
        d["overrides"] = inl
    return d


def _apply_strips(plan, build_dir):
    """Cut promotional sections out of copied files (the source README records each cut). Ranges in one file are
    merged first and cut from the bottom up, so one cut never shifts another onto real content."""
    for s in plan["sources"]:
        by_file = {}
        for rng in s.get("strip_ranges") or []:
            if rng.get("start"):
                by_file.setdefault(rng["file"], []).append(rng)
        for rel_src, ranges in by_file.items():
            merged = []
            for r in sorted(ranges, key=lambda r: r["start"]):
                if merged and r["start"] <= merged[-1]["end"] + 1:
                    merged[-1]["end"] = max(merged[-1]["end"], r["end"])
                    merged[-1]["findings"].append(r["finding"])
                else:
                    merged.append({**r, "findings": [r["finding"]]})
            rel = merge.renamed_skill_file(s["alias"]) if rel_src == "SKILL.md" else merge.vendored_name(s["alias"], rel_src)
            p = os.path.join(build_dir, s["alias"], rel)
            if not os.path.isfile(p):
                continue
            lines = open(p, encoding="utf-8").read().splitlines(keepends=True)
            for r in sorted(merged, key=lambda r: -r["start"]):
                del lines[r["start"] - 1:r["end"]]
            write_text(p, "".join(lines))
            notes = "".join(
                f"- `{rel}` lines {r['start']} to {r['end']}"
                f"{' (section ' + json.dumps(r.get('title')) + ')' if r.get('title') else ''}: promotional instructions "
                f"(finding{'s' if len(r['findings']) > 1 else ''} {', '.join('`' + f + '`' for f in r['findings'])}), cut at the compiler's request.\n"
                for r in merged)
            with open(os.path.join(build_dir, s["alias"], "README.md"), "a", encoding="utf-8") as fh:
                fh.write("\n## Cut from the copy\n\n" + notes)


def _emit(build_dir, target, name, force):
    if os.path.exists(target):
        ours = os.path.isfile(os.path.join(target, LOCK_NAME))
        if not ours and not force:
            raise EngineError(f"{target} exists and was not made by this tool; pass --force to replace it, or choose --out")
        if ours and not force:
            prev = read_json(os.path.join(target, LOCK_NAME))
            if prev.get("skill", {}).get("name") != name:
                raise EngineError(f"{target} holds a different compiled skill ({prev.get('skill', {}).get('name')}); pass --force")
        shutil.rmtree(target)
    shutil.copytree(build_dir, target)


def print_report(report, plan):
    print("")
    for l in report["scoreboard"]:
        print(l)
    print("")
    for c in report["checks"]:
        print(f"{'PASS' if c['ok'] else 'FAIL'}  {c['name']}: {c['detail']}")
    print("")
    if report.get("dry_run"):
        print(f"dry run: nothing emitted. The build is at {report['build']}")
    elif report.get("emitted"):
        print(f"emitted {plan['name']} -> {report['emitted']}")
    else:
        print(f"NOT EMITTED. The build is kept for inspection at {report['build']}; reasons in {os.path.join(plan['_workdir'], 'REFUSED.md')}")
