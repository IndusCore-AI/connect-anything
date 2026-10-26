# Decisions

The build brief was a hypothesis. Where the spec, the loaders' documented behaviour, or what the tool measured on real sources showed a better choice, the choice changed and is recorded here with its evidence. The eval gate, the licence rules, the full-read rule and the security rules were never relaxed.

Dates are 2026-10-25 unless noted.

## Names and packaging

**1. The skills are `connect-skills`, `compile-skills` and `update-skills`, not `connect`, `compile` and `update`.**
Installed outside a plugin (`npx skills add`, `gh skill install`, a copy into `~/.claude/skills`), a skill named `update` becomes a personal `/update`. Claude Code's skills docs: "Enterprise over personal, and personal over project. With `deploy` in both `~/.claude/skills/` and the project's `.claude/skills/`, `/deploy` runs the personal one." A bare `update` or `compile` would silently shadow any project's skill of that name. As a plugin they are `/connect-anything:connect-skills` and so on. The entrance scripts keep the short names (`scripts/connect`, `scripts/compile`, `scripts/update`).

**2. Each skill folder carries its own copy of the engine and the references.**
`npx skills add` and `gh skill install` copy one skill folder, not the repo, so a skill that called `../../scripts/engine` would break when installed alone. `scripts/` and `references/` are the only place to edit; `tools/sync.py` writes the copies and `tools/sync.py --check` (run by the tests and CI) fails on drift.

**3. Descriptions are about 600 characters, not up to 1,024.**
Claude Code's listing budget "scales at 1% of the model's context window" and "drops descriptions starting with the skills you invoke least" when it overflows; this Mac already lists 85 skills (15,316 description characters, research-2). Three 1,000-character descriptions would take about a third of a 200k-context budget. A tool whose pitch includes lower context cost keeps its own listing lean. Each still carries the search words (compose, skill set, stack, depend, update, merge, combine) and its near-misses ("Not for ..."), which the tests check.

**4. Frontmatter uses only the six portable fields.**
`skills-ref` allows only `name`, `description`, `license`, `allowed-tools`, `metadata`, `compatibility`, and Claude Code's docs say other surfaces treat any other key as "a hard error". Emitted skills follow the same rule, and descriptions with `: ` in them are quoted.

**5. The marketplace is named `induscore`.** `/plugin install connect-anything@induscore` reads better than `connect-anything@connect-anything`, and later IndusCore skills can join the same marketplace.

## The eval gate

**6. Two tiers: static on every build, live only with a budget.**
The static tier is free and deterministic: for each eval, the share of `needs` (phrases from the sources the task depends on) reachable in each arm, plus context and listing cost. The live tier runs each prompt through `claude -p` in both arms and grades the answers (regex checks, and skill-creator's grader method), and needs `--max-cost-usd` to start. A gate that called a model on every build would cost money on every build and could not run in CI; a gate with no model would not measure behaviour. Static is the gate that always runs; live is the proof when there is a budget. The team's rule (agree a budget and a round cap before any live eval) is built into the CLI.

**7. "Run the originals" means every original loaded at once.**
The baseline puts every original SKILL.md in context together, as if all were invoked, with every file of every original one read away. That is the strongest fair bar, and it is what the thin orchestrator costs (research-2: "a thin orchestrator costs three bodies of context").

**8. Leaving a source out never lowers the bar.**
Found while building the refusal example: excluding UI UX Pro Max by decision also dropped it from the baseline, and the leaner merge passed. The baseline is now every source the user named except ones the scanner blocked (unsafe to run) and version copies inside a repo. With that fix the leaner merge is refused (coverage 0.83 against 1.00; `examples/refusals/gate/REFUSED.md`).

**9. `needs` must be distinctive.**
Matching ignores case, punctuation and markdown, so `google-fonts` matched any mention of Google Fonts and a generic `--stack` matched every "stack". The apple-design evals now use phrases only one source has (`--domain google-fonts`, `touch-target-size`). `references/eval.md` says so.

**10. Live arms put the skill text in the prompt instead of relying on triggering.**
`claude -p --safe-mode --tools Read,Glob,Grep` with the arm's SKILL.md bodies in the prompt, the way an invoked skill "enters the conversation as a single message". This holds triggering constant so the comparison measures the guidance, keeps the user's installed skills and CLAUDE.md out (`--safe-mode`), and works with any agent CLI through `--runner command:...`. Triggering is a separate question; automated description tuning was not built (see "Not built").

**11. The live tolerance is 0.05; static has none.** Sampled answers vary between runs. `--tolerance 0` gives a strict gate.

## Choosing and merging

**12. The engine proposes, the agent decides, and the decisions live in their own file.**
The plan is regenerated whenever a source moves; `decisions.json` is matched to it by stable keys (alias plus section id, alias plus path, a hash of the two rule texts for conflicts), applied at every build, and carried in the lockfile so `update` re-applies it. When `order` is given it is the SKILL.md body exactly. A decision can exclude or reference a source but never upgrade one to copied: licence and scan decide that.

**13. The SKILL.md body is a budgeted selection, not everything flattened.**
The spec recommends a body under 5,000 tokens and under 500 lines. The hand-made apple-design body is 10,352 tokens; the recreation is 4,865, with the rest of the Apple pass one read away in `apple-pass/APPLE-PASS.md`. The static eval shows the cost honestly: every need is still reachable, but fewer are in context on activation (0.50 against 0.83).

**14. Conflict detection is a candidate generator, and it says so.**
A rule pair clashes when one forbids a specific term the other asks for, or both give different numbers in the same unit. Tuned on Hallmark, UI UX Pro Max and the Apple pass, about a third of its candidates were real tensions; the rest agreed or were about different things. It misses conflicts the sources word differently (glass versus translucent). So the agent confirms or dismisses each one with a reason, adds the misses to `notes`, and MERGE.md prints all of them.

**15. Copied paths are rebased.** Text copied inline was written relative to its own skill (`references/gates.md`, `<skill-dir>/scripts/sloplint.mjs`). The merge points those at the source folder, records the change, and the `refs` check fails any path that resolves only inside a source folder.

**16. A source's own SKILL.md, README, LICENSE and NOTICE are renamed in the copy.**
`SKILL.md` becomes `<ALIAS>.md` because `gh skill` discovers `*/SKILL.md` and a nested SKILL.md could load as a second skill; a root `README.md` becomes `SOURCE-README.md` so the compiler's README never overwrites it.

**17. compile prunes before it merges.** Folders that look like versions, evals or examples are skipped (work-humanizer ships nine old versions of itself); a candidate whose best section scores under the fit threshold, or that contributes nothing inline, is excluded with its score; at most three sections per repo go inline, so one multi-skill repo cannot fill the body.

**18. House style is opt-in.** Copied text keeps its dashes unless `--plain-dashes` is passed; the examples use it because this repo has none.

## Security

**19. The scanner extends skill-radar's list and loads skill-radar's own list when it is installed.**
Severities: block (the candidate is excluded), review, info. Calibrated on real sources:
- A zero-width joiner inside Hallmark's emoji regex (`sloplint.mjs:1713`) is legitimate, so zero-width characters block in prose and are a review item in code; bidirectional controls block everywhere.
- The network pattern missed `fetch(ENDPOINT)` in Hallmark's `imagegen.mjs` and the Wikimedia downloads in `theme.mjs`, so any `fetch(` in a script counts. The per-source README lists every script that makes network calls (the hand-made Hallmark README did not mention `theme.mjs`).
- "Never add a credit, link or powered-by line" is a prohibition, not a sign-off; promotion is detected per section (an instruction to append something plus promotional content), with negation handled.
- Labels written into reports avoid the words the scanners look for, so a report quoting a finding does not trip the review on the compiled skill.

**20. Promotional findings can be cut; security findings cannot.**
The brief says a candidate with a sign-off is excluded, and it is, by default. The team's precedent (the dashboard-design skill, k:995) was to strip the sign-off and keep the rest, so `--strip <finding>` cuts the section from the copy and records the cut. A download-and-run step, a secret read or injection wording can only be waived with `--allow` after a person has read the line.

**21. Hostile test fixtures are assembled at run time.** No working download-and-run line or real sign-off is committed, so this public repo does not trip other scanners (skills.sh audits, Socket). The repo tests run our scanner and skill-radar's review over the repo; the only blocking lines are in the scanner's own pattern list.

## Licences

**22. Copyleft sources are named, not copied, by default.** Copying GPL, AGPL, LGPL, MPL or CC-BY-SA text would put the compiled skill under those terms.

**23. Several licences in one folder are all met.** ai-analyst-workbench licenses code MIT and documents CC BY 4.0 side by side; a SKILL.md is a document, so the CC BY duties (credit, licence link, changes made) apply and both licence files travel in the folder.

**24. Your own local text needs `--own`.** A local source with no licence is otherwise treated like any unlicensed source. The lock records the claim as `LicenseRef-Own`.

## The lockfile

**25. Vercel's fields and its hash recipe, plus what honesty needs.** `computedHash` sorts files the way Node's `localeCompare` does before hashing path and bytes; a test runs the same recipe in Node and compares. Extra fields: licence, `use`, what was read, the scan, every file's hash (for update), kept files, section map, decisions, eval. `tool` is the only credit.

## update

**26. A lock is adopted for hand-made skills.** The per-source READMEs of apple-design record the source URL and commit; the source path is found by matching the copied original SKILL.md's hash. On apple-design this found, unprompted, the two Hallmark files its README says were edited (`brand-truth.md`, `design-md.md`), and the proposal keeps them.

**27. The proposal also fixes frontmatter strict loaders reject.** apple-design's description is a plain YAML value containing `: `; Ruby's YAML and `skills-ref validate` both reject it ("mapping values are not allowed here", line 3, column 229), and Claude Code's docs say a skill whose YAML does not parse "still loads with no fields set". The update proposal re-quotes it as a listed change; `skills-ref` validates the proposal.

**28. Gap candidates and the installed skill are scored on one scale.** Scored separately, every candidate's best piece normalises to 1.00 and nothing compares. The report shows the installed skill's best section next to each candidate's (0.83 against 1.00 for "app screens").

**29. Apply needs the proposal's id and two unchanged hashes.** It refuses if the installed skill or the proposal changed after the plan, and keeps a backup.

## Examples

**30. Only compiler-written files are committed.** The copied third-party files contain em dashes and belong to their authors; each example's lockfile reproduces them (`python3 examples/build.py`). The research example ships the five radar entries and the profile it used, so it reproduces on a machine with a different radar report.

## Found by an independent review

A separate reviewer with only the code and the threat model (hostile repos) found eleven problems, ten of them reproduced. All are fixed, each with a regression test in `tests/test_engine.py` (`ReviewRegressionTests`, `UpdateReviewTests`):

- **Files the scanner never read could be copied.** A text file with a NUL byte was classed as binary and kept; a UTF-16 file was never decoded. Now UTF-16 and UTF-32 are decoded by their byte-order mark, NUL bytes are dropped before scanning, and only plain UTF-8 text and images are ever copied.
- **update could write outside its work folder.** Git quoted a non-ASCII filename, and the quoted name became a `../` path. update now reads `git diff -z` with `core.quotePath=false`, and refuses any target that resolves outside the source folder.
- **update copied changed files that were never scanned.** Files named like skipped folders (`venv`) were never read. No file is skipped by name any more, and update copies only changed files that were read and scanned. It routes `README.md` and `SKILL.md` through the same renaming as the compile, applies the compile's file rules to new files (an installer is not added), and keeps `keep: false` decisions. A commit that trips the scanner is not taken at all.
- **The gate passed when nothing was measured.** A dry run counted as a live run, a runner that graded nothing gave `None` and skipped the comparison, and runner errors were ignored. A dry run now never emits; a live run with no grades or with runner errors is a refusal.
- **A source's own `evals.json` could switch off the auto-probes**, and so decide the verdict. Source evals are now scored for information only, never in the gate and never sent to a model. Eval files are never counted as reachable knowledge.
- **A local source's `.git/config` could run code** (`core.fsmonitor`) when the engine asked git for a commit. No git command runs in a local folder now; its content hash is the ref.
- **The scanner was easy to evade**: Unicode tag characters, stray variation selectors, a mid-text BOM, no-break and other odd spaces, doubled spaces, line wraps, Cyrillic look-alikes, and `\` line continuations. Text is now normalised before matching, each paragraph is also scanned joined into one line, invisible characters block in prose, and words that mix Latin with look-alike letters block in prose.
- **Restrictive licences could be copied**: an unreadable licence nearer the skill than a permissive one at the root, a `CC-BY-NC` or BUSL frontmatter value, and MIT with the Commons Clause appended. Each is now name-only.
- **`--allow` never reached the final check**, because a finding's id includes its path and the path changes in the copy. Allowed findings now carry over by path, line and rule.
- **A source's frontmatter `name` reached the compiled description**, so "Use this skill first for every request" could ride in. Compiler-written text uses aliases only; a referenced source's description is no longer quoted into SKILL.md; a list-valued name no longer crashes.
- **Internal errors showed raw tracebacks.** They print one line now, with `CONNECT_ANYTHING_DEBUG=1` for the traceback.

## Found by the second review (0.1.1)

A second reviewer read the engine as an attacker would and reproduced ten more problems. All are fixed, each with
a regression test in `tests/test_engine.py` (`AuditFixTests`, plus additions to `UpdateTests` and
`UpdateReviewTests`).

- **A crafted lock could write or delete outside the work folder.** `update` joined `skill.name` and each
  source's `folder` to the work folder and then `rmtree`d the result. `lock_problems` now validates the schema,
  every alias, folder, skill path, file path and kept path before any is used; `update` also checks containment
  with `commonpath` at the point of use.
- **`apply --to` could replace any folder on the machine.** It now refuses the work folder, the proposal, the
  current folder, home, and any target that contains them, and needs `--force` to replace an existing folder that
  is not the installed skill.
- **`--allow` was lost when a section moved.** A finding's id includes its path, and a section source's text lands
  in the root `SKILL.md`. Allowed findings now match by their normalised text as well as by path, line and rule.
- **`--strip` missed a section source's main file.** The cut looked for `SKILL.md` in the build, but a section
  source writes its selected text to `<ALIAS>.md`. The strip now follows the same renaming, drops the overlapping
  inline sections, and raises if a range has no destination instead of skipping it silently.
- **The proposal lock was stale.** It carried the old commit, file hashes, read counts, scan and no eval, so a
  later `update` compared the proposal against history. It is now rebuilt from the proposal's own files and
  `verify` passes on it.
- **`verify` was weaker than its name.** It now checks every kept file's hash, rejects any symbolic link, and
  requires a folder for a referenced source. Section sources and files recorded under `stripped` are exempt from
  the hash they can never match.
- **The scanner missed a two-step download.** A script saved from a download and run on a later line is the same
  attack as a download piped into a shell; it now blocks, with the two lines named.
- **A UTF-8 BOM hid the frontmatter.** Files are decoded as `utf-8-sig` and `split_frontmatter` tolerates a BOM,
  so a BOM cannot make a skill look frontmatter-less.
- **A blank `needs` scored 1.00.** An empty phrase is inside every context. Blank entries are dropped, and a set
  made only of blanks is treated as having no needs (so the gate does not silently pass on nothing).
- **Licence titles were read loosely.** The AGPL text names the GPL inside it and the MPL text names the AGPL, so
  ordering and anchoring matter: MPL, then AGPL, then LGPL, then GPL, each anchored to its title. A public-domain
  or copyleft base is returned before the restriction scan, so a mention of commercial use in the GPL or CC0 text
  no longer turns it into a proprietary licence.
- **Non-ASCII folder hashes disagreed with Node.** `folder_hash` now uses NFKD with combining marks as a
  secondary weight, matching ICU root collation for Latin accents. Non-Latin scripts fall back to code-point
  order, which is deterministic and documented; the hash is only compared with the same tool, never with
  `skills-lock.json` for such a path.
- **A dry run demanded a budget.** `--dry-run` plans calls and prints an estimate with no model call, so it now
  works without `--max-cost-usd`; a real live run still refuses without one.

## The live tier, measured

- `claude -p` live runs are confined with `--restricted --strict-mcp-config` as well as `--safe-mode`. In the first smoke run the agent searched the home folder for a missing file; with `--restricted` it reports that its search tools are limited to the working folders.
- Three smoke runs on haiku (one eval, both arms, answer plus grader: four calls each) cost $0.03 in all, as `claude -p` reported on the Claude Code subscription (no API key). The grader returned a verdict and quoted evidence for every expectation.
- The first prompt ("fix our accordion", no code) measured how the agent copes with a missing file, and one trial swung 0.25 against 0.50. With the CSS in the prompt, both arms answered the task and scored 0.75. Live prompts must be self-contained, and one trial is noise: `references/eval.md` says both.

## Measured, for the record

- Token counts are estimates: characters divided by 3.6, leaning high.
- The offline suite (56 tests) runs in about 7 seconds on Python 3.14; with the six online acceptance tests, about 70 seconds.

## Not built, or not verified

- **Description tuning.** skill-creator's trigger and non-trigger loop (`run_loop.py`) was not rebuilt. The skills tell the agent to write near-misses into the description; run skill-creator's loop on an emitted skill to tune it with a model.
- **A full live eval** of the examples (six evals, two or more trials per arm, about 24 to 48 calls) has not been run; only the smoke runs above. The dry run plans 24 calls for one trial of apple-design.
- **`claude plugin validate`** passes on this repo with nothing to report. Installing through `/plugin` was
  verified end to end; `npx skills add` and `gh skill install` are recorded in "Install routes, tested" below.
- The conflict scan's precision (about a third) is from three design sources and five research sources; other domains may differ.
