# MERGE.md: how `screen-kit` was made

Mode: `compile`. Job: Design dashboards and app screens

## Sources

| Source | Commit | Licence | Use | Read | Scan (block / review / info) |
| --- | --- | --- | --- | --- | --- |
| `dashboard` abdiraimov-otabek/dashboard-design-skill | ba1fd0d | MIT (flatten) | **excluded** | 9 files, 48,056 B | 2 / 5 / 1 |
| `lookalike` <generated fixture: tests/fixtures.py hidden_payload_skill> | 5cc7f0a | MIT (flatten) | **excluded** | 3 files, 946 B | 1 / 0 / 0 |
| `ios-app-design` ahonn/dotfiles | 27f1e58 | MIT (flatten) | copied | 10 files, 32,590 B | 0 / 0 / 0 |

## Excluded

- `dashboard` (abdiraimov-otabek/dashboard-design-skill @ ba1fd0d): scanner: tells the agent to add a promotional line at SKILL.md:72.
  - `SKILL.md:72` tells the agent to add a promotional line (finding `4a5cddac65ee`; the line is in the staged copy, not here)
  - `SKILL.md:75` promotes the author's other products (finding `617cd7fe2eaf`; the line is in the staged copy, not here)
  - To use the rest of it, re-run with `--strip <finding>`: the section or file is cut and the cut is recorded here.
- `lookalike` (<generated fixture: tests/fixtures.py hidden_payload_skill> @ 5cc7f0a): scanner: downloads a script and runs it at setup-installation.md:6.
  - `setup-installation.md:6` downloads a script and runs it (finding `4d11e06cd5b7`; the line is in the staged copy, not here)

## What wins, top first

1. The user's own words in the conversation
2. The project's locked system: its tokens, copy rules, i18n and checks (CLAUDE.md, design.md, config files)
3. Safety, licence and honesty rules from any source; a merge never weakens one
4. The sources in this order: `ios-app-design`
5. A rule a mechanical check enforces beats one it does not
6. The more specific rule beats the general one
7. Taste

## Conflicts (0 settled, 0 dismissed as not a conflict)

None found. The scan for conflicts compares every pair of rules across sources for opposite advice or different numbers on the same topic.

## Duplicates folded: one copy per rule (0)

None found.

## Sections

| Source | Section | Lines | Tokens | Score | Use | Why |
| --- | --- | --- | --- | --- | --- | --- |
| `dashboard` | Dashboard design | 6 to 14 | 154 | 0.6 | drop | source is not copied |
| `dashboard` | Leading words | 15 to 21 | 122 | 0.069 | drop | source is not copied |
| `dashboard` | Build or redesign | 22 to 41 | 471 | 0.114 | drop | source is not copied |
| `dashboard` | Critique ("is this a good design?") | 42 to 54 | 178 | 0.259 | drop | source is not copied |
| `dashboard` | Rules that apply everywhere | 55 to 69 | 304 | 0.229 | drop | source is not copied |
| `dashboard` | [promotional text, see source] | 70 to 80 | 170 | 0.306 | drop | source is not copied |
| `dashboard` | House style (default taste) | 81 to 85 | 90 | 0.073 | drop | source is not copied |
| `lookalike` | Lookalike | 6 to 7 | 4 | 0.0 | drop | source is not copied |
| `lookalike` | Use | 8 to 11 | 26 | 0.0 | drop | source is not copied |
| `ios-app-design` | iOS App Design | 7 to 10 | 58 | 0.378 | inline | score 0.378: fits the job |
| `ios-app-design` | Design Criteria | 11 to 19 | 262 | 0.075 | inline | score 0.075: fits the job |
| `ios-app-design` | Read by Decision | 20 to 35 | 288 | 0.175 | inline | score 0.175: fits the job |
| `ios-app-design` | Completion | 36 to 40 | 122 | 0.0 | reference | kept in the source folder |

## Files left out

- None.

## Flagged for review (5)

- `dashboard/SKILL.md:70` skill-radar pattern 16
- `dashboard/SKILL.md:72` skill-radar pattern 16
- `dashboard/SKILL.md:75` tracking or affiliate link
- `dashboard/SKILL.md:76` tracking or affiliate link
- `dashboard/SKILL.md:78` skill-radar pattern 16

## Checks

- PASS spec: frontmatter valid, name matches the folder
- PASS size: SKILL.md 58 lines (limit 500), body about 978 tokens (limit 5000)
- PASS refs: every path SKILL.md names exists
- PASS one-copy: no rule appears twice
- PASS nested: one SKILL.md
- PASS scan: 0 blocking, 3 to review across 15 files; 0 promotional lines in compiler-written files
- PASS install_skill.py review: 3 lines flagged in total; 0 dangerous, 0 self-promotion in compiler-written files
- PASS no self-credit: the compiler names itself only in the lockfile
- PASS house style: no em or en dashes in compiler-written files

## Eval

**Verdict: PASS.** The compiled skill matches or beats running the originals.

| Measure | Run the originals | Compiled | Change |
| --- | --- | --- | --- |
| Static coverage (1 evals with needs) | 1.00 | 1.00 | +0.00 |
| Needs already in context on activation | 1.00 | 1.00 | +0.00 |
| Context on activation (est. tokens) | 730 (1 SKILL.md) | 978 (1 SKILL.md) | +248 |
| Listing (description characters) | 124 | 91 | -33 |
| Live tier | not run (pass --live with --max-cost-usd) | | |

| Eval | Needs | Originals | Compiled | Missing in the compiled skill |
| --- | --- | --- | --- | --- |
| probe-ios-app-design-ios-app-design-design-criteria | 2 | 2 | 2 |  |

Tolerance for sampled answers: 0.05. Static coverage has no tolerance.
