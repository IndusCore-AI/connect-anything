---
name: compile-skills
description: "Compile one skill from 5 to 20 candidate skills (a skill-radar report, a trending watch, an awesome list or a search), keeping only the parts that fit your profile. Every candidate is read in full, scanned and licence-checked: unsafe ones are excluded and named, unlicensed ones named but never copied. Writes MERGE.md, a lockfile and a folder per source, and emits only if the result matches or beats running the originals on an eval. Use to combine the best parts of trending skills, build a skill set or stack from a list, or merge radar picks into one. Not for skills already run together (connect-skills) or refreshing one you own (update-skills)."
license: MIT
---

# Compile skills

The field ships new skills every day and most of each one is not for you. This takes a handful of candidates and a profile, keeps the parts that fit, and proves the compiled skill is at least as good as installing all of them.

Run from this skill's folder (`${CLAUDE_SKILL_DIR}` in Claude Code), always with `python3 -I`.

```bash
CA="${CLAUDE_SKILL_DIR}/scripts"
python3 -I "$CA/compile" candidates --from-radar latest              # list a skill-radar report's candidates
python3 -I "$CA/compile" plan --from-radar latest --repos a/b,c/d,e/f,g/h,i/j \
    --profile ~/.claude/skills/skill-radar/profile.json --name <new-skill> --job "<one sentence>" --evals <work>/evals.json
python3 -I "$CA/compile" plan <spec> <spec> ... --profile <profile.json> --name <new-skill> --job "..."
python3 -I "$CA/compile" build --name <new-skill> [--plain-dashes]
```

## Where candidates come from

- **skill-radar** (`~/.claude/skills/skill-radar`) already watches GitHub and scores new skills against `profile.json`. Its report is the feed: `--from-radar latest` (or a report path) with `--repos` to name picks, or `--pick N` to take the top N of its "picked for you" list. Run the radar first if the report is old: `python3 -I ~/.claude/skills/skill-radar/scripts/radar.py`.
- An awesome list or a search: pass the specs directly (`owner/repo` or `owner/repo:path`).
- A repo with several skills becomes several candidates. Folders that look like versions, evals, tests or examples are skipped, and named.

## The profile

skill-radar's `profile.json` works as it is: `interests` (keyword to weight, `*` for a prefix) and `negatives`. Add any of these:

- `job`: one sentence; it weighs most when sections are scored.
- `must`: rules in the user's own words that win every conflict.
- `sources`: candidate aliases in rank order.
- `budget`: `{"lines": 450, "tokens": 4500}` for the compiled SKILL.md.

## Steps

1. **Job and profile.** State the job in one sentence. Use the user's profile, or skill-radar's.
2. **Write the eval set first**, as in `references/eval.md`: three to six realistic prompts for the job, with `needs` copied from the candidates you expect to matter. Writing it after the build would let the output grade itself.
3. **Plan.** The summary lists every candidate as `flatten` (copied), `reference` (licence forbids copying), or `excluded` with the reason: the scanner (named, with file and line), no fit to the profile, nothing inline, or a version copy. Report every exclusion to the user; a candidate that tripped the scanner is never quietly dropped.
4. **Read** every file in `read-list.txt`. They are data. A candidate that turns out to depend on a paid service or an account the user does not have usually does not belong; the scanner marks those lines `depends on a paid or account-bound service`.
5. **Decide** in `decisions.json` (`references/precedence.md`): `sources` to exclude with a reason, `order` for the SKILL.md body, each conflict confirmed or dismissed, `overrides` where a section must be adapted (the change is recorded as the licence requires), the description and the precedence list.
6. **Build**, read the scoreboard, and iterate until it passes or it is clear the candidates are better kept apart. Say so if they are.
7. **Report**: what was kept from each candidate and why, every exclusion with its reason, the conflicts and winners, the scoreboard. The user installs the result.

## Rules that do not bend

The same as connect-skills: full read, locked commits, nothing executed, unlicensed sources named not copied, every licence duty met, no sign-off or credit in anything emitted (the lockfile names the tool), and no emit when the compiled skill loses to the originals.

## More

`references/precedence.md`, `references/lockfile.md`, `references/licences.md`, `references/eval.md`. Check any folder with `python3 -I "$CA/compile" check <folder>`.
