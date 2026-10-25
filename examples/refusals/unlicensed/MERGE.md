# MERGE.md: how `mobile-screens` was made

Mode: `connect`. Job: Design mobile app screens

## Sources

| Source | Commit | Licence | Use | Read | Scan (block / review / info) |
| --- | --- | --- | --- | --- | --- |
| `mobile-app-design` awesome-skills/mobile-app-design | 83e4721 | NOASSERTION (reference) | named only | 16 files, 184,772 B | 0 / 0 / 15 |
| `pixel-perfect` UMDhodi/pixel-perfect-mobile | ee3ceee | NOASSERTION (reference) | named only | 5 files, 26,515 B | 0 / 0 / 0 |
| `podo` podo/design-agent-skills | 8eeb2a7 | MIT (flatten) | copied | 2 files, 2,955 B | 0 / 0 / 2 |

## Named, not copied

- `mobile-app-design` (awesome-skills/mobile-app-design): licence NOASSERTION: reference; never copied. The compiled SKILL.md names it; its README says how to install it.
- `pixel-perfect` (UMDhodi/pixel-perfect-mobile): licence NOASSERTION: reference; never copied. The compiled SKILL.md names it; its README says how to install it.

## What wins, top first

1. The user's own words in the conversation
2. The project's locked system: its tokens, copy rules, i18n and checks (CLAUDE.md, design.md, config files)
3. Safety, licence and honesty rules from any source; a merge never weakens one
4. The sources in this order: `podo`
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
| `mobile-app-design` | Mobile App Design Standards | 7 to 10 | 50 | 0.49 | reference | named only; the original stays installed |
| `mobile-app-design` | Purpose | 11 to 14 | 76 | 0.261 | reference | named only; the original stays installed |
| `mobile-app-design` | When to Use This Skill | 15 to 25 | 100 | 0.6 | reference | named only; the original stays installed |
| `mobile-app-design` | Core Design Principles | 26 to 91 | 598 | 0.173 | reference | named only; the original stays installed |
| `mobile-app-design` | Component Architecture | 92 to 130 | 274 | 0.289 | reference | named only; the original stays installed |
| `mobile-app-design` | Accessibility (a11y) | 131 to 159 | 226 | 0.259 | reference | named only; the original stays installed |
| `mobile-app-design` | Performance Optimization | 160 to 189 | 217 | 0.105 | reference | named only; the original stays installed |
| `mobile-app-design` | Design System Essentials | 190 to 217 | 212 | 0.054 | reference | named only; the original stays installed |
| `mobile-app-design` | 2026 Design Trends (Optional Enhancement) | 218 to 246 | 180 | 0.093 | reference | named only; the original stays installed |
| `mobile-app-design` | Workflow Integration | 247 to 275 | 255 | 0.093 | reference | named only; the original stays installed |
| `mobile-app-design` | Additional Resources | 276 to 307 | 527 | 0.187 | reference | named only; the original stays installed |
| `mobile-app-design` | Quick Reference | 308 to 330 | 133 | 0.0 | reference | named only; the original stays installed |
| `pixel-perfect` | Pixel-Perfect Mobile UI Skill | 13 to 19 | 62 | 0.298 | reference | named only; the original stays installed |
| `pixel-perfect` | Core Philosophy | 20 to 34 | 136 | 0.129 | reference | named only; the original stays installed |
| `pixel-perfect` | Typography System | 35 to 57 | 200 | 0.053 | reference | named only; the original stays installed |
| `pixel-perfect` | Color System | 58 to 78 | 132 | 0.0 | reference | named only; the original stays installed |
| `pixel-perfect` | Spacing & Layout | 79 to 99 | 105 | 0.132 | reference | named only; the original stays installed |
| `pixel-perfect` | Component Library | 100 to 112 | 116 | 0.0 | reference | named only; the original stays installed |
| `pixel-perfect` | Platform Output Formats | 113 to 129 | 171 | 0.056 | reference | named only; the original stays installed |
| `pixel-perfect` | Code Token Templates | 130 to 203 | 530 | 0.0 | reference | named only; the original stays installed |
| `pixel-perfect` | Good vs Bad Patterns | 204 to 223 | 181 | 0.0 | reference | named only; the original stays installed |
| `pixel-perfect` | How to Use This Skill | 224 to 231 | 152 | 0.215 | reference | named only; the original stays installed |
| `podo` | mobile-app-ui-design | 22 to 26 | 68 | 0.0 | reference | kept in the source folder |
| `podo` | Decision tree | 27 to 56 | 287 | 0.0 | reference | kept in the source folder |
| `podo` | Invoke after install | 57 to 61 | 41 | 0.21 | inline | score 0.21: fits the job |
| `podo` | What it does | 62 to 65 | 105 | 0.214 | inline | score 0.214: fits the job |
| `podo` | When NOT to use | 66 to 70 | 60 | 0.0 | reference | kept in the source folder |

## Files left out

- None.

## Checks

- PASS spec: frontmatter valid, name matches the folder
- PASS size: SKILL.md 46 lines (limit 500), body about 821 tokens (limit 5000)
- PASS refs: every path SKILL.md names exists
- PASS one-copy: no rule appears twice
- PASS nested: one SKILL.md
- PASS scan: 0 blocking, 3 to review across 9 files; 0 promotional lines in compiler-written files
- PASS install_skill.py review: 3 lines flagged in total; 0 dangerous, 0 self-promotion in compiler-written files
- PASS no self-credit: the compiler names itself only in the lockfile
- PASS house style: no em or en dashes in compiler-written files

## Eval

**Verdict: PASS.** The compiled skill matches or beats running the originals.

| Measure | Run the originals | Compiled | Change |
| --- | --- | --- | --- |
| Static coverage (4 evals with needs) | 1.00 | 1.00 | +0.00 |
| Needs already in context on activation | 1.00 | 0.25 | -0.75 |
| Context on activation (est. tokens) | 5,192 (3 SKILL.md) | 821 (1 SKILL.md) | -4,371 |
| Listing (description characters) | 1,121 | 140 | -981 |
| Live tier | not run (pass --live with --max-cost-usd) | | |

| Eval | Needs | Originals | Compiled | Missing in the compiled skill |
| --- | --- | --- | --- | --- |
| probe-mobile-app-design-mobile-app-design-standards-when-to- | 2 | 2 | 2 |  |
| probe-mobile-app-design-mobile-app-design-standards-componen | 2 | 2 | 2 |  |
| probe-pixel-perfect-pixel-perfect-mobile-ui-skill-how-to-use | 2 | 2 | 2 |  |
| probe-podo-mobile-app-ui-design-invoke-after-install | 1 | 1 | 1 |  |

Tolerance for sampled answers: 0.05. Static coverage has no tolerance.
