# work-humanizer (from phuryn/work-humanizer)

Source: https://github.com/phuryn/work-humanizer, commit 0a90657 (2026-10-10), MIT licence (`LICENSE`). Merged into `research-brief` on 2026-10-26, after every file was read in full and scanned.

## Read and scanned

- 3 files, 29,817 bytes, read in full (every byte, secondary files included).
- Scanner: 0 blocking, 1 to review, 0 informational.
- No script makes network calls.
- Flagged for review (1), with what was done:
  - `SKILL.md:151` skill-radar pattern 16 (kept)

## What is here

- `WORK-HUMANIZER-WORK-HUMANIZER.md`: the original SKILL.md, unchanged, renamed so agents never load it as a second skill. Its own file references still hold relative to this folder.
- `./` (2): `check.py`, `tells.md`

Inline in `../SKILL.md`: "The tells, strongest first".

## Changes made

- "The tells, strongest first" (lines 72 to 131 of the original): rewritten by the compiler (see MERGE.md); 1 relative path(s) pointed at `work-humanizer-work-humanizer/`.

## Left out, and why

- Nothing.

## Licence duties

- Keep the copyright and permission notice in every copy: LICENSE travels in the source folder.

## Updating

Run the `update-skills` skill on `../`: it diffs phuryn/work-humanizer against commit 0a90657, re-reads every changed file, re-runs the eval and asks before replacing anything.
