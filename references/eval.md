# The eval gate

A compiled skill is emitted only if it matches or beats running the originals on the eval set. If it loses, nothing is written to `--out`, `REFUSED.md` in the working folder says why, and the scoreboard is printed.

## The eval file

Anthropic's skill-creator format (`evals/evals.json`, Apache-2.0, https://github.com/anthropics/skills), so the same file works in both tools, with two optional fields added:

```json
{
  "skill_name": "research-brief",
  "evals": [
    {
      "id": 1,
      "name": "company-brief",
      "prompt": "Research Northwind Fabrics and write me a one-page brief for an investor call tomorrow.",
      "expected_output": "Claims tagged observed, inferred or unknown, with a source each, and open questions listed.",
      "files": [],
      "expectations": ["Tags each claim as observed, inferred or unknown", "Gives a source for every number"],
      "needs": ["Never write an inferred item as if it were observed", "Open questions"],
      "output_checks": [{"text": "uses the three tags", "regex": "observed[\\s\\S]{0,4000}inferred"}]
    }
  ]
}
```

- `expectations` (skill-creator): what a good answer does. Graded by a model on a live run.
- `needs` (added): short phrases copied from the sources that the task depends on. Matching ignores case, markdown, punctuation and dashes.
- `output_checks` (added): `regex` must match the answer, `not_regex` must not. Graded for free on a live run.

Write the set before you build. Two rules make it measure something:

- **`needs` must be distinctive.** Matching ignores case and punctuation, so a generic phrase (`--stack`, `google-fonts`) is satisfied by any mention of the word. Copy a phrase only one source has (`--domain google-fonts`, `touch-target-size`).
- **Live prompts must be self-contained.** The agent answers in an empty folder with read access to the skill folders only. Put the code or text in the prompt, or the input files in `files`; a prompt that says "fix our accordion" with nothing attached measures how the agent copes with a missing file.

 A source's own `evals/evals.json` joins the set automatically. With no eval set at all, the engine writes mechanical probes from the highest-scoring sections of each source, labelled as such; they guard against cutting what the job ranked highest, and they are weaker than evals a person wrote for the job.

## Two arms

- **Run the originals:** every usable original SKILL.md in context at once, as if each had been invoked, and every file of every original one read away. This is the strongest fair baseline: all of them, all loaded.
- **Compiled:** the one compiled SKILL.md in context, and its folder one read away. A source that is named, not copied, stays installed, so its files count as reachable in this arm too.

## Two tiers

**Static, always.** Free and deterministic. For each eval, the share of `needs` reachable in each arm; how many of them are already in context on activation; the estimated tokens in context on activation (3.6 characters per token, leaning high); and the listing cost (description characters). The gate: compiled coverage is not below the originals'. No tolerance.

**Live, with a budget.** Each eval prompt runs in both arms through `claude -p` with read-only tools (`Read, Glob, Grep`), `--safe-mode` so no installed skill, plugin or CLAUDE.md leaks in, and the arm's skills placed in the prompt the way an invoked skill enters the conversation. Arms alternate in random order. The answer is graded on `output_checks`, and on `expectations` by a grader model (haiku by default) in skill-creator's `grading.json` shape (`text`, `passed`, `evidence`). The gate: the compiled pass rate is not below the originals' by more than the tolerance (0.05 by default, because sampled answers vary; set `--tolerance 0` for a strict gate). A run that stops at the budget before both arms finish is a refusal.

```bash
connect build --name x --dry-run                                  # planned calls and an estimate, no model called
connect build --name x --live --max-cost-usd 2 --model haiku --trials 2
connect build --name x --live --max-cost-usd 2 --runner "command:my-agent --prompt-file {prompt_file}"   # any agent CLI
```

`--max-cost-usd` is required for a live run: agree the budget before any model is called. Results go to `<work>/eval/`: `scoreboard.md`, `scoreboard.json`, per-run `answer.md` and `grading.json`, and `benchmark.json` in skill-creator's shape (its viewer groups by `with_skill` and `without_skill`, so the compiled skill is `with_skill` and the originals `without_skill`; `metadata.configurations` says so).

## Reading the scoreboard

```
| Measure                               | Run the originals   | Compiled          | Change   |
| Static coverage (6 evals with needs)  | 1.00                | 1.00              | +0.00    |
| Needs already in context on activation| 0.94                | 0.69              | -0.25    |
| Context on activation (est. tokens)   | 15,345 (3 SKILL.md) | 4,849 (1 SKILL.md)| -10,496  |
| Listing (description characters)      | 1,566               | 566               | -1,000   |
```

Coverage is the gate. "In context" shows the price of a lean SKILL.md: more of the knowledge is one read away. The context and listing rows are what the merge saves on every activation and in every session's skill listing.

## What the gate cannot tell you

Static coverage shows the compiled skill still reaches what the evals need; it does not show the agent will use it well. Only a live run measures behaviour, and a small live run is noisy: two trials per arm on six evals is a smoke test, not a benchmark. Report it as such.
