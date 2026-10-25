"""Eval step: the gate. The compiled skill must match or beat "run the originals" on the eval set, or it is
not emitted and the scores are shown.

The eval file is Anthropic skill-creator's evals/evals.json (skill_name, evals[] with id, prompt,
expected_output, files, expectations), with two optional fields this tool adds:

  needs          phrases the skill must make reachable for the task (static tier, free, deterministic)
  output_checks  [{"text", "regex" | "not_regex"}] checked against the agent's answer (live tier, free to grade)

Tiers
  static  always runs. For each arm it collects what the agent would have in context on activation (every
          original SKILL.md, as if all were invoked, against the one compiled SKILL.md) and what is one read
          away (every text file in the skill folders). Coverage is the share of `needs` reachable. Context
          cost and listing cost are reported beside it.
  live    runs only with a budget (--max-cost-usd). Each eval prompt runs in both arms through `claude -p`
          (read-only tools, --safe-mode so no installed skill or CLAUDE.md leaks in), the answer is graded
          on output_checks and, with an LLM grader, on expectations (skill-creator's grading.json shape).
          A fixture runner replays recorded answers for tests.

Verdict: pass when compiled >= originals on static coverage and, when live ran, the compiled pass rate is
no lower than the originals' minus the tolerance (default 0.05, because sampled answers vary).
"""
import hashlib
import json
import os
import random
import re
import shutil
import subprocess
import tempfile
import time

from .util import EngineError, estimate_tokens, iter_files, read_json, split_frontmatter, write_json, write_text, log, content_words

TEXT_KINDS_EXT = (".md", ".txt", ".json", ".csv", ".py", ".mjs", ".js", ".ts", ".sh", ".yaml", ".yml", ".toml", ".html", ".css")


def norm(text):
    """Letters and digits only, so markdown, punctuation and dashes never decide a match."""
    return re.sub(r"[^a-z0-9]+", " ", text.lower()).strip()


# ------------------------------------------------------------------ eval sets
def load_eval_set(paths):
    """Merge one or more skill-creator eval files. Ids are renumbered so each stays unique."""
    evals, names = [], []
    for p in paths:
        data = read_json(p)
        names.append(data.get("skill_name", os.path.basename(os.path.dirname(os.path.dirname(p)))))
        for e in data.get("evals", []):
            e = dict(e)
            e.setdefault("name", f"eval-{e.get('id', len(evals) + 1)}")
            e["origin"] = p
            evals.append(e)
    for i, e in enumerate(evals, 1):
        e["id"] = i
    return evals


def auto_probes(plan, per_source=3):
    """When no eval set is given: mechanical probes from the highest-scoring sections of each copied source.

    Each probe needs the opening words of that section's most distinctive rules. A merge that cuts the
    knowledge the job ranked highest loses these probes.
    """
    from .choose import rules_of
    evals = []
    for src in plan["sources"]:
        if not in_baseline(src):
            continue
        if plan.get("mode") == "compile" and src["mode"] == "excluded":
            continue  # compile exists to leave parts out; only connect probes every source the user named
        secs = sorted([s for s in src["sections"] if s.get("score") is not None], key=lambda s: -(s.get("score") or 0))
        for sec in secs[:per_source]:
            rules = [r for _, r in rules_of(sec["text"]) if len(content_words(r)) >= 4]
            if not rules:
                continue
            needs = []
            for r in sorted(rules, key=lambda r: -len(set(content_words(r))))[:2]:
                plain = re.sub(r"[`*_]", "", r)
                plain = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", plain)
                w = plain.split()
                needs.append(" ".join(w[:7]))
            evals.append({"id": len(evals) + 1, "name": f"probe-{src['alias']}-{sec['id']}"[:80],
                          "prompt": f"Using the skill, apply its guidance on \"{sec['title']}\" to the job: {plan.get('job') or 'the task'}",
                          "expected_output": f"Follows \"{sec['title']}\" from {src['alias']}.",
                          "files": [], "expectations": [f"Applies the guidance in \"{sec['title']}\""],
                          "needs": needs, "origin": "auto-probe"})
    return evals


def eval_set_hash(evals):
    blob = json.dumps([{k: e.get(k) for k in ("prompt", "expectations", "needs", "output_checks")} for e in evals], sort_keys=True)
    return hashlib.sha256(blob.encode()).hexdigest()[:16]


# ------------------------------------------------------------------ arms
def in_baseline(src):
    """Every source the user named counts in 'run the originals', whatever the merge decided to leave out.
    Only a source the scanner blocked (unsafe to run) and a version copy inside a repo are not in it."""
    return not (src["mode"] == "excluded" and src.get("excluded_by") in ("scanner", "copy", None))


def originals_arm(plan):
    """What 'run the originals' puts in front of the agent: every original the user named, whole. Leaving a
    source out of the merge never lowers this bar."""
    context, reach, descs = [], [], []
    for src in plan["sources"]:
        if not in_baseline(src):
            continue
        root = src["staging"]
        main = os.path.join(root, os.path.basename(src.get("skillPath") or "SKILL.md"))
        if src.get("section_selector"):
            body = "".join(s["text"] for s in src["sections"])
        else:
            body = split_frontmatter(open(main, encoding="utf-8", errors="replace").read())[1] if os.path.isfile(main) else ""
        context.append((src["alias"], body))
        if not src.get("section_selector"):
            reach.extend(_text_files(root))
        descs.append(src.get("description") or "")
    dirs = sorted({s["staging"] for s in plan["sources"] if in_baseline(s)})
    return {"name": "originals", "context": context, "reach": reach, "descriptions": descs, "root": None, "dirs": dirs,
            "root_for": {s["alias"]: s["staging"] for s in plan["sources"] if in_baseline(s)}}


def folder_arm(name, skill_dir):
    """An installed skill as it stands (update compares the current folder with the proposal)."""
    text = open(os.path.join(skill_dir, "SKILL.md"), encoding="utf-8").read()
    fm, body = split_frontmatter(text)
    from .util import parse_frontmatter
    desc = parse_frontmatter(fm)[0].get("description", "") if fm else ""
    return {"name": name, "context": [(name, body)], "reach": _text_files(skill_dir), "descriptions": [desc],
            "root": skill_dir, "root_for": {name: skill_dir}}


def compiled_arm(plan, out_dir):
    body = split_frontmatter(open(os.path.join(out_dir, "SKILL.md"), encoding="utf-8").read())[1]
    reach = _text_files(out_dir)
    for src in plan["sources"]:
        if src["mode"] == "reference":  # the compiled skill tells the agent to run the installed original
            reach.extend(_text_files(src["staging"]))
            main = os.path.join(src["staging"], "SKILL.md")
            if os.path.isfile(main):
                reach.append(open(main, encoding="utf-8", errors="replace").read())
    return {"name": "compiled", "context": [(plan["name"], body)], "reach": reach,
            "descriptions": [plan["description"]], "root": out_dir, "root_for": {plan["name"]: out_dir}}


def _text_files(root):
    out = []
    for rel, ap in iter_files(root):
        if rel.endswith(TEXT_KINDS_EXT) and os.path.getsize(ap) < 2_000_000:
            out.append(open(ap, encoding="utf-8", errors="replace").read())
    return out


# ------------------------------------------------------------------ static tier
def static_tier(evals, arms):
    rows, totals = [], {}
    corp = {}
    for arm in arms:
        corp[arm["name"]] = (norm("\n".join(b for _, b in arm["context"])), norm("\n".join(arm["reach"])))
    scored = [e for e in evals if e.get("needs")]
    for e in scored:
        row = {"id": e["id"], "name": e["name"], "needs": len(e["needs"])}
        for arm in arms:
            ctx, reach = corp[arm["name"]]
            in_ctx = sum(1 for n in e["needs"] if norm(n) in ctx)
            reached = sum(1 for n in e["needs"] if norm(n) in ctx or norm(n) in reach)
            row[arm["name"]] = {"reachable": reached, "in_context": in_ctx, "score": reached / len(e["needs"]),
                                "missing": [n for n in e["needs"] if norm(n) not in ctx and norm(n) not in reach]}
        rows.append(row)
    for arm in arms:
        n = len(rows) or 1
        totals[arm["name"]] = {
            "coverage": round(sum(r[arm["name"]]["score"] for r in rows) / n, 4) if rows else None,
            "in_context": round(sum(r[arm["name"]]["in_context"] / r["needs"] for r in rows) / n, 4) if rows else None,
            "context_tokens": sum(estimate_tokens(b) for _, b in arm["context"]),
            "skills_loaded": len(arm["context"]),
            "listing_chars": sum(len(d) for d in arm["descriptions"]),
        }
    return {"rows": rows, "totals": totals, "evals_scored": len(rows), "evals_live_only": len(evals) - len(rows)}


# ------------------------------------------------------------------ live tier
class Budget:
    def __init__(self, cap):
        self.cap, self.spent, self.calls, self.last = cap, 0.0, 0, 0.05

    def allow(self):
        return self.spent + self.last <= self.cap

    def add(self, cost):
        self.calls += 1
        self.spent += cost or 0.0
        self.last = max(cost or 0.0, 0.005)


def _arm_prompt(arm, task):
    parts = ["These skills are loaded for this task. Follow them where they apply; read the files they point to when a step sends you there.", ""]
    for name, body in arm["context"]:
        root = arm.get("root_for", {}).get(name, "")
        parts.append(f"<skill name=\"{name}\"{' path=' + json.dumps(root) if root else ''}>\n{body.strip()}\n</skill>")
    parts += ["", "Task:", task.strip()]
    return "\n".join(parts)


def run_claude(prompt, cwd, add_dirs, model, budget_per_call, tools="Read,Glob,Grep"):
    if not shutil.which("claude"):
        raise EngineError("claude CLI not found; use --runner command:'<cmd>' or --runner fixture:<file>")
    cmd = ["claude", "-p", prompt, "--output-format", "json", "--safe-mode", "--no-session-persistence",
           "--tools", tools, "--max-budget-usd", f"{budget_per_call:.2f}"]
    if model:
        cmd += ["--model", model]
    for d in add_dirs:
        cmd += ["--add-dir", d]
    env = {k: v for k, v in os.environ.items() if k != "CLAUDECODE"}
    t0 = time.time()
    p = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=900, env=env)
    try:
        data = json.loads(p.stdout)
    except ValueError:
        raise EngineError(f"claude -p returned no JSON (exit {p.returncode}): {(p.stderr or p.stdout)[:300]}")
    return {"text": data.get("result") or "", "cost": float(data.get("total_cost_usd") or 0.0),
            "seconds": round(time.time() - t0, 1), "error": data.get("is_error", False)}


def run_command(template, prompt, cwd):
    pf = os.path.join(cwd, ".prompt.txt")
    write_text(pf, prompt)
    cmd = template.replace("{prompt_file}", pf).replace("{cwd}", cwd)
    p = subprocess.run(cmd, shell=True, cwd=cwd, capture_output=True, text=True, timeout=900)
    return {"text": p.stdout, "cost": 0.0, "seconds": 0, "error": p.returncode != 0}


class Runner:
    """claude (default), command:<template with {prompt_file} {cwd}>, or fixture:<json> for tests."""

    def __init__(self, spec, model=None, judge_model=None, per_call=0.5):
        self.spec = spec or "claude"
        self.model, self.judge_model, self.per_call = model, judge_model or "haiku", per_call
        self.fixture = None
        if self.spec.startswith("fixture:"):
            self.fixture = read_json(self.spec.split(":", 1)[1])

    def answer(self, arm, e, trial, cwd, add_dirs):
        if self.fixture is not None:
            rec = self.fixture.get(arm["name"], {}).get(str(e["id"])) or self.fixture.get(arm["name"], {}).get(e["name"], "")
            text = rec[trial % len(rec)] if isinstance(rec, list) else rec
            return {"text": text, "cost": 0.0, "seconds": 0, "error": False}
        prompt = _arm_prompt(arm, e["prompt"])
        if self.spec.startswith("command:"):
            return run_command(self.spec.split(":", 1)[1], prompt, cwd)
        return run_claude(prompt, cwd, add_dirs, self.model, self.per_call)

    def grade(self, e, answer_text, cwd):
        """skill-creator's grading.json expectations: [{text, passed, evidence}]."""
        out = []
        for c in e.get("output_checks") or []:
            if "regex" in c:
                ok = bool(re.search(c["regex"], answer_text, re.I | re.S))
            else:
                ok = not re.search(c["not_regex"], answer_text, re.I | re.S)
            out.append({"text": c.get("text") or c.get("regex") or c.get("not_regex"), "passed": ok,
                        "evidence": "regex check on the answer", "grader": "regex"})
        exps = e.get("expectations") or []
        if exps and self.fixture is None and not self.spec.startswith("command:"):
            prompt = ("You grade an answer against expectations. For each expectation decide passed true or false and quote "
                      "the evidence from the answer. Be strict: no evidence means false. Reply with JSON only: "
                      '{"expectations": [{"text": "...", "passed": true, "evidence": "..."}]}\n\n'
                      f"Task given:\n{e['prompt']}\n\nExpectations:\n" + "\n".join(f"- {x}" for x in exps) +
                      f"\n\nAnswer to grade:\n<answer>\n{answer_text[:60000]}\n</answer>")
            r = run_claude(prompt, cwd, [], self.judge_model, self.per_call, tools="")
            self.last_grade_cost = r["cost"]
            m = re.search(r"\{.*\}", r["text"], re.S)
            try:
                graded = json.loads(m.group(0))["expectations"] if m else []
            except (ValueError, KeyError):
                graded = []
            for g in graded:
                g["grader"] = "llm"
            out.extend(graded)
        elif exps and self.fixture is not None:
            for x in exps:
                ok = bool(re.search(re.escape(x[:30]), answer_text, re.I)) or x.lower() in answer_text.lower()
                out.append({"text": x, "passed": ok, "evidence": "fixture: substring", "grader": "fixture"})
        return out


def live_tier(evals, arms, runner, budget, trials=1, workdir=None, dry_run=False, seed=7):
    calls_per = sum(1 + (1 if (e.get("expectations") and runner.fixture is None) else 0) for e in evals)
    planned = calls_per * trials * len(arms)
    if dry_run:
        return {"dry_run": True, "planned_calls": planned, "estimate_usd": round(planned * budget.last, 2), "cap_usd": budget.cap}
    rnd = random.Random(seed)
    if workdir:
        os.makedirs(workdir, exist_ok=True)
    results = {a["name"]: [] for a in arms}
    incomplete = False
    for e in evals:
        for trial in range(trials):
            order = arms[:]
            rnd.shuffle(order)  # alternate which arm runs first so rate limits and caching do not favour one
            for arm in order:
                if runner.fixture is None and not budget.allow():
                    incomplete = True
                    break
                cwd = tempfile.mkdtemp(prefix="eval-", dir=workdir)
                for f in e.get("files") or []:
                    if os.path.isfile(f):
                        shutil.copy2(f, cwd)
                add_dirs = [arm["root"]] if arm.get("root") else arm.get("dirs", [])
                ans = runner.answer(arm, e, trial, cwd, add_dirs)
                budget.add(ans["cost"])
                runner.last_grade_cost = 0.0
                graded = runner.grade(e, ans["text"], cwd)
                budget.add(getattr(runner, "last_grade_cost", 0.0))
                passed = sum(1 for g in graded if g.get("passed"))
                results[arm["name"]].append({"eval_id": e["id"], "eval_name": e["name"], "run_number": trial + 1,
                                             "result": {"pass_rate": passed / len(graded) if graded else None, "passed": passed,
                                                        "failed": len(graded) - passed, "total": len(graded),
                                                        "time_seconds": ans["seconds"], "cost_usd": round(ans["cost"], 4)},
                                             "expectations": graded, "answer_chars": len(ans["text"])})
                if workdir:
                    d = os.path.join(workdir, "runs", f"eval-{e['id']}", arm["name"], f"run-{trial + 1}")
                    write_text(os.path.join(d, "answer.md"), ans["text"])
                    write_json(os.path.join(d, "grading.json"), {"expectations": graded,
                               "summary": {"passed": passed, "failed": len(graded) - passed, "total": len(graded),
                                           "pass_rate": passed / len(graded) if graded else None}})
                shutil.rmtree(cwd, ignore_errors=True)
    summary = {}
    for name, runs in results.items():
        rates = [r["result"]["pass_rate"] for r in runs if r["result"]["pass_rate"] is not None]
        summary[name] = {"pass_rate": round(sum(rates) / len(rates), 4) if rates else None, "runs": len(runs)}
    return {"runs": results, "summary": summary, "incomplete": incomplete, "spent_usd": round(budget.spent, 4),
            "calls": budget.calls, "trials": trials, "model": runner.model, "judge_model": runner.judge_model}


# ------------------------------------------------------------------ gate
def gate(static, live=None, tolerance=0.05):
    t = static["totals"]
    o, c = t["originals"]["coverage"], t["compiled"]["coverage"]
    reasons, verdict = [], "pass"
    if static["evals_scored"] == 0 and not live:
        return "refuse", ["no eval has `needs` and no live run was made, so nothing shows the merge is as good as the originals"]
    if o is not None and c is not None and c + 1e-9 < o:
        verdict = "refuse"
        reasons.append(f"static coverage {c:.2f} is below the originals' {o:.2f}")
    if live and not live.get("dry_run"):
        if live.get("incomplete"):
            verdict = "refuse"
            reasons.append(f"the live run stopped at the budget (${live['spent_usd']:.2f}) before both arms finished")
        lo, lc = live["summary"]["originals"]["pass_rate"], live["summary"]["compiled"]["pass_rate"]
        if lo is not None and lc is not None and lc + tolerance < lo:
            verdict = "refuse"
            reasons.append(f"live pass rate {lc:.2f} is below the originals' {lo:.2f} by more than {tolerance:.2f}")
    if verdict == "pass":
        reasons.append("the compiled skill matches or beats running the originals")
    return verdict, reasons


def scoreboard_lines(static, live, verdict, reasons, tolerance):
    t = static["totals"]
    o, c = t["originals"], t["compiled"]
    fmt = lambda v: "n/a" if v is None else f"{v:.2f}"
    L = [f"**Verdict: {verdict.upper()}.** " + " ".join(r[0].upper() + r[1:] + "." for r in reasons), "",
         "| Measure | Run the originals | Compiled | Change |", "| --- | --- | --- | --- |"]
    if o["coverage"] is not None:
        d = c["coverage"] - o["coverage"]
        L.append(f"| Static coverage ({static['evals_scored']} evals with needs) | {fmt(o['coverage'])} | {fmt(c['coverage'])} | {d:+.2f} |")
        L.append(f"| Needs already in context on activation | {fmt(o['in_context'])} | {fmt(c['in_context'])} | {c['in_context'] - o['in_context']:+.2f} |")
    L.append(f"| Context on activation (est. tokens) | {o['context_tokens']:,} ({o['skills_loaded']} SKILL.md) | {c['context_tokens']:,} (1 SKILL.md) | {c['context_tokens'] - o['context_tokens']:+,} |")
    L.append(f"| Listing (description characters) | {o['listing_chars']:,} | {c['listing_chars']:,} | {c['listing_chars'] - o['listing_chars']:+,} |")
    if live and not live.get("dry_run"):
        lo, lc = live["summary"]["originals"]["pass_rate"], live["summary"]["compiled"]["pass_rate"]
        dl = (lc - lo) if (lo is not None and lc is not None) else None
        L.append(f"| Live pass rate ({live['trials']} trial(s), {live.get('model') or 'default model'}) | {fmt(lo)} | {fmt(lc)} | "
                 f"{'n/a' if dl is None else f'{dl:+.2f}'} |")
        L.append(f"| Live spend | | | ${live['spent_usd']:.2f} over {live['calls']} calls |")
    elif live and live.get("dry_run"):
        L.append(f"| Live tier | not run: dry run plans {live['planned_calls']} calls, about ${live['estimate_usd']:.2f} | | |")
    else:
        L.append("| Live tier | not run (pass --live with --max-cost-usd) | | |")
    if static["rows"]:
        L += ["", "| Eval | Needs | Originals | Compiled | Missing in the compiled skill |", "| --- | --- | --- | --- | --- |"]
        for r in static["rows"]:
            miss = "; ".join(r["compiled"]["missing"])[:120]
            L.append(f"| {r['name'][:60]} | {r['needs']} | {r['originals']['reachable']} | {r['compiled']['reachable']} | {miss} |")
    L.append("")
    L.append(f"Tolerance for sampled answers: {tolerance:.2f}. Static coverage has no tolerance.")
    return L


def run_eval(plan, out_dir, eval_paths=None, live=False, runner_spec=None, model=None, judge_model=None, trials=1,
             max_cost=None, dry_run=False, tolerance=0.05, workdir=None):
    evals = load_eval_set(eval_paths) if eval_paths else []
    if not evals:
        evals = auto_probes(plan)
    arms = [originals_arm(plan), compiled_arm(plan, out_dir)]
    static = static_tier(evals, arms)
    live_res = None
    if live or dry_run:
        if not runner_spec or not runner_spec.startswith("fixture:"):
            if max_cost is None:
                raise EngineError("a live eval needs --max-cost-usd: agree the budget before any model is called")
        runner = Runner(runner_spec, model=model, judge_model=judge_model)
        live_res = live_tier(evals, arms, runner, Budget(max_cost or 0.0), trials=trials, workdir=workdir, dry_run=dry_run)
    verdict, reasons = gate(static, live_res, tolerance)
    result = {"verdict": verdict, "reasons": reasons, "tiers": ["static"] + (["live"] if live_res and not live_res.get("dry_run") else []),
              "originals": {"static": static["totals"]["originals"], "live": (live_res or {}).get("summary", {}).get("originals")},
              "compiled": {"static": static["totals"]["compiled"], "live": (live_res or {}).get("summary", {}).get("compiled")},
              "eval_set_hash": eval_set_hash(evals), "tolerance": tolerance, "evals": len(evals),
              "auto_probes": all(e.get("origin") == "auto-probe" for e in evals)}
    lines = scoreboard_lines(static, live_res, verdict, reasons, tolerance)
    if workdir:
        write_json(os.path.join(workdir, "scoreboard.json"), {**result, "static": static, "live": live_res})
        write_text(os.path.join(workdir, "scoreboard.md"), "\n".join(lines) + "\n")
        if live_res and not live_res.get("dry_run"):
            write_json(os.path.join(workdir, "benchmark.json"), _benchmark(plan, live_res))
    return result, lines, evals


def _benchmark(plan, live):
    """skill-creator's benchmark.json. Its viewer groups by with_skill / without_skill, so the compiled skill is
    with_skill and the originals are without_skill; metadata.configurations says so."""
    runs = []
    for arm, conf in (("compiled", "with_skill"), ("originals", "without_skill")):
        for r in live["runs"][arm]:
            runs.append({**r, "configuration": conf})
    return {"metadata": {"skill_name": plan["name"], "executor_model": live.get("model"), "runs_per_configuration": live["trials"],
                         "configurations": {"with_skill": "compiled", "without_skill": "originals"}}, "runs": runs}
