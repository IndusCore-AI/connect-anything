#!/usr/bin/env python3
"""Rebuild every example from its pinned sources and copy the files the compiler wrote into <example>/output/.

  python3 examples/build.py                 all of them (fetches from GitHub; needs gh or git)
  python3 examples/build.py apple-design    one of them

The copied third-party files are not committed here; each example's lockfile names the exact commits, so
this script reproduces them. Paths on this machine are written as ~ in the outputs.
"""
import json
import os
import re
import shutil
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OUT = os.environ.get("CA_EXAMPLES_OUT") or HERE  # the tests write elsewhere so the committed outputs stay as they are
sys.path.insert(0, os.path.join(ROOT, "scripts"))
sys.path.insert(0, os.path.join(ROOT, "tests"))

from engine import pipeline, update  # noqa: E402
from engine.util import LOCK_NAME, plain_dashes  # noqa: E402

HOME = os.path.expanduser("~")
APPLE_DESIGN = os.path.join(HOME, ".claude", "skills", "apple-design")
APPLE_JOB = ("Design, build or review any screen people see or touch: choose the design for new work, hold a floor against "
             "AI-looking UI, run the mechanical check, and finish with Apple's interaction pass")
APPLE_SOURCES = ["apple-pass=" + os.path.join(APPLE_DESIGN, "SKILL.md") + "#part-c-the-apple-pass",
                 "hallmark=Nutlope/hallmark@7ec8682",
                 "uiux-pro-max=nextlevelbuilder/ui-ux-pro-max-skill@d14efff:.claude/skills/ui-ux-pro-max"]
RESEARCH_JOB = ("Research a market, product or company from public evidence and write a short brief where every number and "
                "claim carries its source and plain writing")


def scrub(text, extra=()):
    for a, b in extra:
        text = text.replace(a, b)
    text = text.replace(HOME, "~")
    return re.sub(r"/(private/)?(var|tmp)/[^\s`)'\"]*?(?=/[A-Za-z0-9._-]+\.(connect-anything|update)\b|[\s`)'\"])", "<work>", text)


def keep_compiler_files(build_dir, dest, extra=()):
    """Copy SKILL.md, MERGE.md, the lockfile, every source README and the eval files."""
    if os.path.isdir(dest):
        shutil.rmtree(dest)
    for dirpath, _, files in os.walk(build_dir):
        for fn in files:
            rel = os.path.relpath(os.path.join(dirpath, fn), build_dir)
            if rel in ("SKILL.md", "MERGE.md", LOCK_NAME) or rel.startswith("evals/") or (rel.count("/") == 1 and fn == "README.md"):
                text = open(os.path.join(dirpath, fn), encoding="utf-8").read()
                os.makedirs(os.path.dirname(os.path.join(dest, rel)), exist_ok=True)
                with open(os.path.join(dest, rel), "w", encoding="utf-8") as f:
                    f.write(scrub(text, extra))


def need_apple_design():
    p = os.path.join(APPLE_DESIGN, "SKILL.md")
    if not os.path.isfile(p) or "# Part C: The Apple pass" not in open(p, encoding="utf-8").read():
        sys.exit(f"{p} is missing or is the old single-file version. Run `ctx update` (it installs apple-design v2), then try again.")


def build(mode, name, specs, work, out, decisions=None, evals=None, **kw):
    pipeline.make_plan(mode, name, specs, workdir=work, evals=evals, plain_dashes=True, **kw)
    plan = pipeline.load_plan(work)
    return pipeline.build(plan, out=out, decisions_path=decisions, force=True)


def apple_design(scratch):
    need_apple_design()
    work, out = os.path.join(scratch, "apple-design.connect-anything"), os.path.join(scratch, "out", "apple-design")
    ex = os.path.join(HERE, "apple-design")
    rep = build("connect", "apple-design", APPLE_SOURCES, work, out, decisions=os.path.join(ex, "decisions.json"),
                evals=[os.path.join(ex, "evals.json")], own=["apple-pass"], job=APPLE_JOB, compare_to=APPLE_DESIGN)
    keep_compiler_files(rep["emitted"] or rep["build"], os.path.join(OUT, "apple-design", "output"))
    return rep


def research_compile(scratch):
    from engine.radar import candidates_from_report
    ex = os.path.join(HERE, "research-compile")
    picks = candidates_from_report(os.path.join(ex, "radar-report.md"), pick=5)
    work, out = os.path.join(scratch, "research-brief.connect-anything"), os.path.join(scratch, "out", "research-brief")
    rep = build("compile", "research-brief", [p["spec"] for p in picks], work, out, decisions=os.path.join(ex, "decisions.json"),
                evals=[os.path.join(ex, "evals.json")], profile_path=os.path.join(ex, "profile.json"), job=RESEARCH_JOB)
    keep_compiler_files(rep["emitted"] or rep["build"], os.path.join(OUT, "research-compile", "output"))
    return rep


def update_app_screens(scratch):
    need_apple_design()
    ex = os.path.join(HERE, "update-app-screens")
    copy = os.path.join(scratch, "installed", "apple-design")  # plan never writes to the skill; a copy makes that moot
    if os.path.isdir(copy):
        shutil.rmtree(copy)
    shutil.copytree(APPLE_DESIGN, copy)
    work = os.path.join(scratch, "apple-design.update")
    cands = json.load(open(os.path.join(ex, "candidates.json")))["candidates"]
    state, md = update.plan_update(copy, work, gap="app screens", candidates=cands, adopt_ok=True,
                                   evals=[os.path.join(HERE, "apple-design", "evals.json")], plain=True)
    dest = os.path.join(OUT, "update-app-screens", "output")
    if os.path.isdir(dest):
        shutil.rmtree(dest)
    os.makedirs(dest)
    swaps = [(copy, "~/.claude/skills/apple-design"), (work, "<work>")]
    with open(os.path.join(dest, "PROPOSAL.md"), "w", encoding="utf-8") as f:
        f.write(scrub(md, swaps))
    prop = state["proposal"]
    for rel in [LOCK_NAME] + [os.path.join(d, "README.md") for d in os.listdir(prop)
                              if os.path.isfile(os.path.join(prop, d, "README.md")) and not os.path.isdir(os.path.join(copy, d))]:
        text = open(os.path.join(prop, rel), encoding="utf-8").read()
        os.makedirs(os.path.dirname(os.path.join(dest, rel)), exist_ok=True)
        with open(os.path.join(dest, rel), "w", encoding="utf-8") as f:
            f.write(scrub(plain_dashes(text), swaps))
    return state


def refusals(scratch):
    import fixtures as fx
    reps = {}
    # 1. two real unlicensed skills are named, never copied; the MIT one is copied
    work, out = os.path.join(scratch, "mobile-screens.connect-anything"), os.path.join(scratch, "out", "mobile-screens")
    reps["unlicensed"] = build("connect", "mobile-screens",
                               ["mobile-app-design=awesome-skills/mobile-app-design@83e4721",
                                "pixel-perfect=UMDhodi/pixel-perfect-mobile",
                                "podo=podo/design-agent-skills@8eeb2a7:skills/mobile-app-ui-design"],
                               work, out, job="Design mobile app screens")
    keep_compiler_files(reps["unlicensed"]["emitted"] or reps["unlicensed"]["build"], os.path.join(OUT, "refusals", "unlicensed"))
    # 2. a real sign-off and a generated hidden download-and-run step are excluded and named
    fixture_root = tempfile.mkdtemp(prefix="fixture-", dir=scratch)
    lookalike = fx.hidden_payload_skill(fixture_root)
    work, out = os.path.join(scratch, "screen-kit.connect-anything"), os.path.join(scratch, "out", "screen-kit")
    reps["scanner"] = build("compile", "screen-kit",
                            ["dashboard=abdiraimov-otabek/dashboard-design-skill@ba1fd0d:skills/dashboard-design",
                             f"lookalike={lookalike}",
                             "ios-app-design=ahonn/dotfiles@27f1e58:.claude/skills/ios-app-design"],
                            work, out, job="Design dashboards and app screens", fit_threshold=0.0)
    keep_compiler_files(reps["scanner"]["emitted"] or reps["scanner"]["build"], os.path.join(OUT, "refusals", "scanner"),
                        extra=[(lookalike, "<generated fixture: tests/fixtures.py hidden_payload_skill>")])
    # 3. a leaner apple-design without UI UX Pro Max loses an eval, so it is refused
    need_apple_design()
    dec = json.load(open(os.path.join(HERE, "apple-design", "decisions.json")))
    dec["sources"] = {"uiux-pro-max": {"mode": "excluded", "why": "a leaner merge, to show the gate"}}
    dec["order"] = [k for k in dec["order"] if not k.startswith("uiux-pro-max:")]
    dec["sections"] = {k: v for k, v in dec["sections"].items() if not k.startswith("uiux-pro-max:")}
    dec["files"] = {k: v for k, v in dec["files"].items() if not k.startswith("uiux-pro-max:")}
    dec["extra_sections"] = [{"id": "pick-the-mode", "title": "Pick the mode first", "why": "written for this merge",
                              "text": "## Pick the mode first\n\n- A screen in a repo with a system: keep the system, apply the Floor where it fits, then the Apple pass.\n"
                                      "- A new page: follow Hallmark's flow below, then the sweep and the Apple pass.\n"}]
    dpath = os.path.join(scratch, "lean-decisions.json")
    json.dump(dec, open(dpath, "w"))
    work, out = os.path.join(scratch, "apple-design-lean.connect-anything"), os.path.join(scratch, "out", "apple-design-lean")
    reps["gate"] = build("connect", "apple-design", APPLE_SOURCES, work, out, decisions=dpath,
                         evals=[os.path.join(HERE, "apple-design", "evals.json")], own=["apple-pass"], job=APPLE_JOB)
    os.makedirs(os.path.join(OUT, "refusals", "gate"), exist_ok=True)
    with open(os.path.join(OUT, "refusals", "gate", "REFUSED.md"), "w", encoding="utf-8") as f:
        f.write(scrub(open(os.path.join(work, "REFUSED.md"), encoding="utf-8").read()))
    return reps


EXAMPLES = {"apple-design": apple_design, "research-compile": research_compile,
            "update-app-screens": update_app_screens, "refusals": refusals}

if __name__ == "__main__":
    names = sys.argv[1:] or list(EXAMPLES)
    scratch = tempfile.mkdtemp(prefix="ca-examples-")
    for n in names:
        print(f"== {n}", flush=True)
        r = EXAMPLES[n](scratch)
        if isinstance(r, dict) and "verdict" in r:
            print(f"   {r['verdict']}: {'; '.join(r.get('reasons') or [])}" + (f" approval id {r['id']}" if r.get("id") else ""))
        elif isinstance(r, dict):
            for k, v in r.items():
                print(f"   {k}: {v['verdict'] if 'verdict' in v else v}: {'; '.join(v.get('reasons', []))}")
    print(f"scratch: {scratch}")
