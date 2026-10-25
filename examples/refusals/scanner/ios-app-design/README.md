# ios-app-design (from ahonn/dotfiles)

Source: https://github.com/ahonn/dotfiles, commit 27f1e58 (2026-10-08), MIT licence (`LICENSE`). Merged into `screen-kit` on 2026-10-25, after every file was read in full and scanned.

## Read and scanned

- 10 files, 32,590 bytes, read in full (every byte, secondary files included).
- Scanner: 0 blocking, 0 to review, 0 informational.
- No script makes network calls.

## What is here

- `IOS-APP-DESIGN.md`: the original SKILL.md, unchanged, renamed so agents never load it as a second skill. Its own file references still hold relative to this folder.
- `references/` (9): `accessibility.md`, `color-and-theme.md`, `haptics-and-feedback.md`, `icons-and-imagery.md`, `layout.md`, `liquid-glass.md`, `motion.md`, `navigation.md`, `typography.md`

Inline in `../SKILL.md`: "iOS App Design", "Design Criteria", "Read by Decision".

## Changes made

- "iOS App Design" (lines 7 to 10 of the original): heading levels shifted down one.
- "Read by Decision" (lines 20 to 35 of the original): 9 relative path(s) pointed at `ios-app-design/`.

## Left out, and why

- Nothing.

## Licence duties

- Keep the copyright and permission notice in every copy: LICENSE travels in the source folder.

## Updating

Run the `update-skills` skill on `../`: it diffs ahonn/dotfiles against commit 27f1e58, re-reads every changed file, re-runs the eval and asks before replacing anything.
