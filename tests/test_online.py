"""Acceptance tests: the six checks Pulkit runs. They fetch the real sources from GitHub (gh or git) and read
~/.claude/skills/apple-design, so they run only with `python3 tests/run.py --online`. No model is called."""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "examples"))
SCRATCH = tempfile.mkdtemp(prefix="ca-online-", dir=os.environ.get("CA_TEST_TMP"))
os.environ["CA_EXAMPLES_OUT"] = os.path.join(SCRATCH, "examples")  # never rewrite the committed outputs

import build as examples  # noqa: E402
from engine import check  # noqa: E402
from engine.util import LOCK_NAME, folder_hash  # noqa: E402

_cache = {}


def once(name):
    if name not in _cache:
        _cache[name] = examples.EXAMPLES[name](SCRATCH)
    return _cache[name]


def skills_ref(path):
    exe = shutil.which("skills-ref")
    if not exe:
        return None
    return subprocess.run([exe, "validate", path], capture_output=True, text=True).returncode == 0


class Acceptance(unittest.TestCase):
    def test_1_recreate_apple_design(self):
        rep = once("apple-design")
        out = rep["emitted"]
        self.assertTrue(out, rep["reasons"])
        for rel in ("hallmark/README.md", "hallmark/LICENSE", "uiux-pro-max/README.md", "uiux-pro-max/LICENSE",
                    "hallmark/scripts/sloplint.mjs", "hallmark/HALLMARK.md", "uiux-pro-max/UIUX-PRO-MAX.md", "MERGE.md", LOCK_NAME):
            self.assertTrue(os.path.isfile(os.path.join(out, rel)), rel)
        lock = json.load(open(os.path.join(out, LOCK_NAME)))
        self.assertTrue(lock["skills"]["hallmark"]["ref"].startswith("7ec8682"))
        self.assertTrue(lock["skills"]["uiux-pro-max"]["ref"].startswith("d14efff"))
        merge_md = open(os.path.join(out, "MERGE.md")).read()
        self.assertIn("## Against `~/.claude/skills/apple-design`", merge_md)
        self.assertIn("Only in the hand-made skill", merge_md)

    def test_2_compile_research_from_five_radar_candidates(self):
        rep = once("research-compile")
        out = rep["emitted"]
        self.assertTrue(out, rep["reasons"])
        lock = json.load(open(os.path.join(out, LOCK_NAME)))
        repos = {e["source"] for e in lock["skills"].values()}
        self.assertEqual(len(repos), 5, repos)
        merge_md = open(os.path.join(out, "MERGE.md")).read()
        self.assertIn("## Conflicts", merge_md)
        plan = json.load(open(os.path.join(SCRATCH, "research-brief.connect-anything", "plan.built.json")))
        for c in plan["conflicts"]:
            self.assertIn(c["id"], merge_md)  # every conflict is listed, settled or dismissed

    def test_3_update_apple_design_for_app_screens(self):
        before = folder_hash(examples.APPLE_DESIGN)
        state = once("update-app-screens")
        self.assertEqual(folder_hash(examples.APPLE_DESIGN), before, "nothing may be written to the installed skill")
        self.assertTrue(state["id"])
        proposal = open(os.path.join(examples.OUT, "update-app-screens", "output", "PROPOSAL.md")).read()
        self.assertIn("## The gap: \"app screens\"", proposal)
        self.assertIn("named (not copied)", proposal)
        self.assertIn("added `ios-app-design/`", proposal)
        self.assertIn("No loss on the existing evals", proposal)
        self.assertIn("update apply", proposal)

    def test_4_refusals(self):
        reps = once("refusals")
        lic = json.load(open(os.path.join(reps["unlicensed"]["emitted"], LOCK_NAME)))
        self.assertEqual(lic["skills"]["mobile-app-design"]["use"], "reference")
        self.assertEqual(lic["skills"]["pixel-perfect"]["use"], "reference")
        for alias in ("mobile-app-design", "pixel-perfect"):
            self.assertEqual(os.listdir(os.path.join(reps["unlicensed"]["emitted"], alias)), ["README.md"])
        sc = json.load(open(os.path.join(reps["scanner"]["emitted"], LOCK_NAME)))
        self.assertEqual(sc["skills"]["dashboard"]["use"], "excluded")
        self.assertEqual(sc["skills"]["lookalike"]["use"], "excluded")
        merge_md = open(os.path.join(reps["scanner"]["emitted"], "MERGE.md")).read()
        self.assertIn("tells the agent to add a promotional line", merge_md)
        self.assertIn("downloads a script and runs it at setup-installation.md", merge_md)

    def test_5_the_gate_refuses_a_losing_merge(self):
        reps = once("refusals")
        self.assertEqual(reps["gate"]["verdict"], "refuse")
        self.assertIsNone(reps["gate"]["emitted"])
        refused = open(os.path.join(examples.OUT, "refusals", "gate", "REFUSED.md")).read()
        self.assertIn("Static coverage", refused)
        self.assertIn("--domain google-fonts", refused)

    def test_6_every_skill_validates_and_stays_under_500_lines(self):
        emitted = [once("apple-design")["emitted"], once("research-compile")["emitted"]]
        reps = once("refusals")
        emitted += [reps["unlicensed"]["emitted"], reps["scanner"]["emitted"]]
        pack = [os.path.join(ROOT, "skills", n) for n in ("connect-skills", "compile-skills", "update-skills")]
        for d in pack + emitted:
            self.assertFalse(check.spec_problems(d), d)
            lines, _ = check.size_check(d)
            self.assertLess(lines, 500, d)
            ok = skills_ref(d)
            if ok is not None:
                self.assertTrue(ok, f"skills-ref validate failed: {d}")
        for d in emitted:
            results = check.run_checks(d)
            self.assertTrue(all(r["ok"] for r in results), [r for r in results if not r["ok"]])


if __name__ == "__main__":
    unittest.main()
