# claims-audit (from loootai/reverse-engineer)

Source: https://github.com/loootai/reverse-engineer, commit 4aa911d (2026-10-11), MIT licence (`LICENSE`). Merged into `research-brief` on 2026-10-26, after every file was read in full and scanned.

## Read and scanned

- 1 files, 4,630 bytes, read in full (every byte, secondary files included).
- Scanner: 0 blocking, 2 to review, 0 informational.
- No script makes network calls.
- Flagged for review (2), with what was done:
  - `SKILL.md:42` installs something that keeps running (kept)
  - `SKILL.md:43` installs something that keeps running (kept)

## What is here

- `REVERSE-ENGINEER-CLAIMS-AUDIT.md`: the original SKILL.md, unchanged, renamed so agents never load it as a second skill. Its own file references still hold relative to this folder.

## Left out, and why

- Nothing.
- Section "When to use" of SKILL.md: trigger or intro text; the compiled description covers it.
- Section "Failure handling" of SKILL.md: score 0.0: does not fit the profile.

## Licence duties

- Keep the copyright and permission notice in every copy: LICENSE travels in the source folder.

## Updating

Run the `update-skills` skill on `../`: it diffs loootai/reverse-engineer against commit 4aa911d, re-reads every changed file, re-runs the eval and asks before replacing anything.
