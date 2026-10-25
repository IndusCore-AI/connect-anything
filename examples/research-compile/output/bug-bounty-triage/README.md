# bug-bounty-triage (from Sequester-AG/bug-bounty-triage)

Source: https://github.com/Sequester-AG/bug-bounty-triage, commit 9684e1b (2026-10-09), MIT licence (`LICENSE`). Merged into `research-brief` on 2026-10-25, after every file was read in full and scanned.

## Read and scanned

- 4 files, 29,986 bytes, read in full (every byte, secondary files included).
- Scanner: 0 blocking, 0 to review, 5 informational.
- No script makes network calls.

## What is here

- `BUG-BOUNTY-TRIAGE.md`: the original SKILL.md, unchanged, renamed so agents never load it as a second skill. Its own file references still hold relative to this folder.
- `SOURCE-README.md`: the source's own README, unchanged (this file is the compiler's).
- `./` (3): `.gitignore`, `LICENSE`, `README.md`

Inline in `../SKILL.md`: "Knowledge-Assumption Audit".

## Changes made

- "Knowledge-Assumption Audit" (lines 319 to 335 of the original): rewritten by the compiler (see MERGE.md).

## Left out, and why

- Nothing.
- Section "Bug Bounty Report Triage, Validation & Severity Escalation" of SKILL.md: score 0.08: does not fit the profile.
- Section "PHASE 1: INTAKE" of SKILL.md: score 0.013: does not fit the profile.

## Licence duties

- Keep the copyright and permission notice in every copy: LICENSE travels in the source folder.

## Updating

Run the `update-skills` skill on `../`: it diffs Sequester-AG/bug-bounty-triage against commit 9684e1b, re-reads every changed file, re-runs the eval and asks before replacing anything.
