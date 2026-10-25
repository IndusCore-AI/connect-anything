# Update proposal for `apple-design`

Installed skill: `~/.claude/skills/apple-design`. Nothing there has been changed.

**Verdict: PASS.** No loss on the existing evals (1.00, was 1.00). Gap probes reachable: 1.00, was 0.00.

To apply: `update apply --work <work> --approve 2e1047992c62`. A backup of the installed folder is kept in the work folder.

The skill had no lockfile, so one was adopted from what its per-source READMEs record; the proposal carries it.

## Upstream

| Source | Locked | Now | Status | Changed files (all re-read and re-scanned) | Local edits kept |
| --- | --- | --- | --- | --- | --- |
| Nutlope/hallmark | 7ec8682 | 7ec8682 | up to date | none | `references/brand-truth.md`, `references/design-md.md` |
| nextlevelbuilder/ui-ux-pro-max-skill | d14efff | d14efff | up to date | none | none |

## The gap: "app screens"

Scores are on one scale: 1.00 is the best piece found for the gap anywhere. The installed SKILL.md's best section scores 0.83.

| Candidate | Licence | Scan (block / review) | Verdict | Best section for the gap | Score |
| --- | --- | --- | --- | --- | --- |
| ahonn/dotfiles:.claude/skills/ios-app-design | MIT | 0 / 0 | flatten | `references/liquid-glass.md` Where Liquid Glass Appears | 1.00 |
| awesome-skills/mobile-app-design:. | NOASSERTION | 0 / 0 | reference (licence NOASSERTION, so it is named, not copied) | `references/platform-differences.md` Settings | 0.97 |
| sonanh08t4/mobile-ui-design-os:. | Apache-2.0 | 0 / 81 | flatten | `research/source/Codex Mobile UI Design OS.md` Anti-generic detector bắt buộc | 0.80 |
| alinaqi/maggy:skills/ui-mobile | MIT | 0 / 0 | flatten | `SKILL.md` Core Philosophy | 0.35 |
| podo/design-agent-skills:skills/mobile-app-ui-design | MIT | 0 / 0 | flatten | `SKILL.md` mobile-app-ui-design | 0.00 |

## What the proposal changes

- SKILL.md frontmatter re-quoted so strict YAML loaders read it (description: plain value contains ': ' or ' #'; quote it)
- added `ios-app-design/` from ahonn/dotfiles @ 27f1e58 for the gap
- named (not copied) `mobile-app-design/` from awesome-skills/mobile-app-design @ 83e4721 for the gap
- SKILL.md: 4 pointer line(s) added after "Part B2: Extend mode, app screens"

## Eval: installed against proposed

- Existing evals (6): reachable 1.00 now, 1.00 proposed; context 10,352 tokens now, 10,576 proposed.
- Gap probes (2): reachable 0.00 now, 1.00 proposed; context 10,352 tokens now, 10,576 proposed.

## Checks on the proposal

- PASS spec: frontmatter valid, name matches the folder
- FAIL size: SKILL.md 430 lines (limit 500), body about 10576 tokens (limit 5000) (already failing before this update; not caused by it)
- FAIL refs: missing: references/anatomy.md (relative to a source folder), references/brand-truth.md (relative to a source folder), references/craft.md (relative to a source folder), references/direction.md (relative to a source folder), references/gates.md (relative to a source folder), references/imagery.md (relative to a source folder), references/layout.md (relative to a source folder), references/macrostructures.md (relative to a source folder) (already failing before this update; not caused by it)
- PASS one-copy: no rule appears twice
- PASS nested: one SKILL.md
- PASS scan: 0 blocking, 58 to review across 211 files; 0 promotional lines in compiler-written files
- PASS install_skill.py review: 5 lines flagged in total; 0 dangerous, 0 self-promotion in compiler-written files
- PASS no self-credit: the compiler names itself only in the lockfile

## SKILL.md diff

```diff
--- SKILL.md (installed)
+++ SKILL.md (proposed)
@@ -1,5 +1,5 @@
 ---
 name: apple-design
-description: The team's default skill for every design task, new or changed. It covers websites, landing pages, B2C launch pages, claude.ai artifacts, app screens, components, reviews and polish. For new work it picks the design: product reasoning from UI UX Pro Max's 192 product profiles, then genre, theme, page shape, layout and pictures from Hallmark's 48 themes and 21 page shapes. It also carries UI UX Pro Max's 119 UX rules, stack guidance (Next.js, React, shadcn, Tailwind), Google Fonts and chart advice. On every change it enforces a floor against AI-looking UI, runs a mechanical check, and runs Apple's interaction pass (instant feedback, interruptible spring motion, enter and exit on one path, materials, typography, reduced-motion fallbacks). Use whenever anything people see or touch is designed, built or changed.
+description: "The team's default skill for every design task, new or changed. It covers websites, landing pages, B2C launch pages, claude.ai artifacts, app screens, components, reviews and polish. For new work it picks the design: product reasoning from UI UX Pro Max's 192 product profiles, then genre, theme, page shape, layout and pictures from Hallmark's 48 themes and 21 page shapes. It also carries UI UX Pro Max's 119 UX rules, stack guidance (Next.js, React, shadcn, Tailwind), Google Fonts and chart advice. On every change it enforces a floor against AI-looking UI, runs a mechanical check, and runs Apple's interaction pass (instant feedback, interruptible spring motion, enter and exit on one path, materials, typography, reduced-motion fallbacks). Use whenever anything people see or touch is designed, built or changed."
 ---
 
@@ -119,4 +119,11 @@
 - **Native or mobile app screens:** finish with `uiux-pro-max/references/pro-rules.md`, its pre-delivery checklist.
 
+**More for app screens (added by update on 2026-10-25):**
+
+- `ios-app-design/references/liquid-glass.md`, "Where Liquid Glass Appears": - Tab bars and toolbars - Navigation bars - Control Center - Lock Screen time display - Dock and Home Screen icons - Widgets - Alerts and action...
+- `ios-app-design/references/icons-and-imagery.md`, "Icons & Imagery": SF Symbols, app icons, and image handling for iOS.
+- `ios-app-design/references/icons-and-imagery.md`, "Common Mistakes": - Custom icon sets when SF Symbols has equivalent, check SF Symbols app first - Inconsistent icon weight, match SF Symbol weight to text weight...
+- `mobile-app-design` (awesome-skills/mobile-app-design; licence NOASSERTION, so it is named, not copied). Install it and run it for app screens; see `mobile-app-design/README.md`.
+
 ## Check before calling it done
 
```
