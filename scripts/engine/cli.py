"""Command line for the three entrances. Each script calls main(mode)."""
import argparse
import os
import sys

from . import pipeline, check as checkmod, lock as lockmod
from .util import EngineError, log, to_skill_name

EXIT_REFUSED = 3


def _common_plan_args(p):
    p.add_argument("--name", required=True, help="name of the compiled skill (lowercase, hyphens); also its folder name")
    p.add_argument("--job", default="", help="one sentence: what the compiled skill is for")
    p.add_argument("--profile", help="profile JSON (skill-radar's profile.json works as is)")
    p.add_argument("--work", help="working folder for the plan, build and eval (default ./<name>.connect-anything)")
    p.add_argument("--own", action="append", default=[], help="alias or spec of a local source you wrote yourself")
    p.add_argument("--allow", action="append", default=[], help="finding id a person read and judged harmless")
    p.add_argument("--strip", action="append", default=[], help="promotional finding id to cut from the copy")
    p.add_argument("--orchestrate", action="store_true", help="name every source instead of copying (thin orchestrator)")
    p.add_argument("--budget-lines", type=int, help="SKILL.md line budget (default 450)")
    p.add_argument("--budget-tokens", type=int, help="SKILL.md body token budget (default 4500)")
    p.add_argument("--evals", action="append", default=[], help="skill-creator evals.json to gate on (repeatable)")
    p.add_argument("--compare-to", help="a hand-made skill folder to diff against in MERGE.md")
    p.add_argument("--plain-dashes", action="store_true", help="replace em and en dashes in inline text (house style)")
    p.add_argument("--refresh", action="store_true", help="fetch again even when the commit is already staged")


def _common_build_args(p):
    p.add_argument("--work", help="working folder holding plan.json")
    p.add_argument("--name", help="find the working folder as ./<name>.connect-anything")
    p.add_argument("--out", help="where to emit the compiled skill (default ./<name>)")
    p.add_argument("--force", action="store_true", help="replace an existing folder at --out that this tool did not write")
    p.add_argument("--live", action="store_true", help="also run the live eval tier (needs --max-cost-usd)")
    p.add_argument("--dry-run", action="store_true", help="plan the live tier and print its cost without calling a model")
    p.add_argument("--max-cost-usd", type=float, help="hard ceiling for the live tier")
    p.add_argument("--model", help="model for the live tier answers (e.g. haiku, sonnet)")
    p.add_argument("--judge-model", help="model for grading expectations (default haiku)")
    p.add_argument("--trials", type=int, default=1, help="answers per eval per arm")
    p.add_argument("--runner", help="claude (default), command:'<template>', fixture:<file>")
    p.add_argument("--tolerance", type=float, default=0.05, help="live pass-rate tolerance (static coverage has none)")
    p.add_argument("--evals", action="append", default=[], help="add or replace the eval set at build time")
    p.add_argument("--compare-to", help="a hand-made skill folder to diff against in MERGE.md")
    p.add_argument("--plain-dashes", action="store_true")
    p.add_argument("--decisions", help="the agent's decisions file (default <work>/decisions.json)")


def _workdir(args):
    if getattr(args, "work", None):
        return os.path.abspath(os.path.expanduser(args.work))
    if getattr(args, "name", None):
        return os.path.abspath(f"{args.name}.connect-anything")
    raise EngineError("pass --work <folder> or --name <skill>")


def _budget(args):
    b = {}
    if getattr(args, "budget_lines", None):
        b["lines"] = args.budget_lines
    if getattr(args, "budget_tokens", None):
        b["tokens"] = args.budget_tokens
    return b or None


def cmd_plan(args, mode, specs):
    work = _workdir(args)
    plan = pipeline.make_plan(mode, args.name, specs, job=args.job, gap=getattr(args, "gap", "") or "",
                              profile_path=args.profile, own=args.own, allow=args.allow, strip=args.strip,
                              orchestrate=args.orchestrate, budget=_budget(args), refresh=args.refresh, workdir=work,
                              evals=args.evals, compare_to=args.compare_to, plain_dashes=args.plain_dashes,
                              fit_threshold=getattr(args, "fit", None))
    print(pipeline.summarize_plan(plan))
    reads = pipeline.files_to_read(plan)
    print(f"\nplan: {os.path.join(work, 'plan.json')}")
    print(f"read these {len(reads)} files before you change the plan (list: {os.path.join(work, 'read-list.txt')})")
    with open(os.path.join(work, "read-list.txt"), "w", encoding="utf-8") as f:
        f.write("\n".join(reads) + "\n")
    return plan


def cmd_build(args):
    work = _workdir(args)
    plan = pipeline.load_plan(work)
    if args.evals:
        plan["evals"] = [os.path.abspath(os.path.expanduser(e)) for e in args.evals]
    if args.compare_to:
        plan["compare_to"] = os.path.abspath(os.path.expanduser(args.compare_to))
    if args.plain_dashes:
        plan["options"]["plain_dashes"] = True
    report = pipeline.build(plan, out=args.out, live=args.live, runner=args.runner, model=args.model,
                            judge_model=args.judge_model, trials=args.trials, max_cost=args.max_cost_usd,
                            dry_run=args.dry_run, tolerance=args.tolerance, force=args.force,
                            decisions_path=os.path.abspath(os.path.expanduser(args.decisions)) if args.decisions else None)
    pipeline.print_report(report, plan)
    return 0 if report.get("emitted") else EXIT_REFUSED


def main(mode, argv=None):
    argv = sys.argv[1:] if argv is None else argv
    ap = argparse.ArgumentParser(prog=mode, description=f"connect-anything: {mode}")
    sub = ap.add_subparsers(dest="cmd")
    p_plan = sub.add_parser("plan", help="fetch, read, scan, check licences, and draft plan.json")
    if mode == "compile":
        p_plan.add_argument("sources", nargs="*", help="candidate specs (or use --from-radar)")
        p_plan.add_argument("--from-radar", help="a skill-radar report (path or 'latest')")
        p_plan.add_argument("--pick", type=int, default=5, help="how many radar candidates to take")
        p_plan.add_argument("--repos", help="comma-separated owner/repo picks from the radar report")
        p_plan.add_argument("--fit", type=float, help="minimum section score for a candidate to stay (default 0.2)")
    else:
        p_plan.add_argument("sources", nargs="+", help="source specs: owner/repo[@ref][:path], URL, or local path[#section]")
    _common_plan_args(p_plan)
    p_build = sub.add_parser("build", help="merge the plan, run the eval gate and the checks, emit if it passes")
    _common_build_args(p_build)
    p_check = sub.add_parser("check", help="run the mechanical checks on a skill folder")
    p_check.add_argument("skill_dir")
    p_check.add_argument("--no-lock", action="store_true", help="the folder has no lockfile (a hand-made skill)")
    p_verify = sub.add_parser("verify", help="check a compiled skill against its lockfile")
    p_verify.add_argument("skill_dir")
    if mode == "compile":
        p_cand = sub.add_parser("candidates", help="list candidates from a skill-radar report")
        p_cand.add_argument("--from-radar", default="latest")
    args = ap.parse_args(argv)
    try:
        if args.cmd == "plan":
            specs = list(args.sources)
            if mode == "compile" and args.from_radar:
                from .radar import candidates_from_report
                picks = candidates_from_report(args.from_radar, pick=args.pick, repos=args.repos)
                specs += [c["spec"] for c in picks]
                log("from the radar report: " + ", ".join(c["spec"] for c in picks))
            if not specs:
                raise EngineError("no sources given")
            cmd_plan(args, mode, specs)
            return 0
        if args.cmd == "build":
            return cmd_build(args)
        if args.cmd == "check":
            res = checkmod.run_checks(os.path.abspath(args.skill_dir), expect_lock=not args.no_lock)
            for c in res:
                print(f"{'PASS' if c['ok'] else 'FAIL'}  {c['name']}: {c['detail']}")
            return 0 if checkmod.all_ok(res) else 1
        if args.cmd == "verify":
            probs = lockmod.verify_lock(os.path.abspath(args.skill_dir))
            print("lock matches the folder" if not probs else "\n".join(probs))
            return 0 if not probs else 1
        if args.cmd == "candidates":
            from .radar import candidates_from_report
            for c in candidates_from_report(args.from_radar, pick=999):
                print(f"{c['spec']:<55} {c['licence']:<12} stars {c['stars']:<6} {c['section']}  {c['description'][:70]}")
            return 0
        ap.print_help()
        return 2
    except EngineError as e:
        print(f"{mode}: {e}", file=sys.stderr)
        return 2
