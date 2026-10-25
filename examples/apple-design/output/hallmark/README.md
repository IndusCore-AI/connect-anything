# hallmark (from Nutlope/hallmark)

Source: https://github.com/Nutlope/hallmark, commit 7ec8682 (2026-10-22), MIT licence (`LICENSE`). Merged into `apple-design` on 2026-10-25, after every file was read in full and scanned.

## Read and scanned

- 178 files, 6,841,340 bytes, read in full (every byte, secondary files included).
- Scanner: 0 blocking, 34 to review, 17 informational.
- Scripts that make network calls: `scripts/imagegen.mjs`, `scripts/sloplint-render.mjs`, `scripts/sloplint.mjs`, `scripts/theme.mjs`.
- Flagged for review (34), with what was done:
  - `SKILL.md:56` references an API key or token (kept)
  - `references/comp.md:3` references an API key or token (left out)
  - `references/comp.md:98` references an API key or token (left out)
  - `references/flow.md:14` touches agent configuration (left out)
  - `references/flow.md:101` references an API key or token (left out)
  - `references/flow.md:119` touches agent configuration (left out)
  - `references/fonts.md:20` depends on a paid or account-bound service (kept)
  - `references/genres/modern-minimal.md:3` depends on a paid or account-bound service (kept)
  - `references/imagery.md:13` references an API key or token (kept)
  - `references/imagery.md:79` references an API key or token (kept)
  - `references/layout.md:100` skill-radar pattern 16 (kept)
  - `references/macrostructures/12-letter.md:8` skill-radar pattern 16 (kept)
  - `references/themes/README.md:20` depends on a paid or account-bound service (kept)
  - `references/themes/atelier.md:85` depends on a paid or account-bound service (kept)
  - `references/themes/bloom.md:89` depends on a paid or account-bound service (kept)
  - `references/themes/bloom.md:90` depends on a paid or account-bound service (kept)
  - `references/themes/coral.md:9` depends on a paid or account-bound service (kept)
  - `references/themes/coral.md:89` depends on a paid or account-bound service (kept)
  - `references/themes/hum.md:88` depends on a paid or account-bound service (kept)
  - `references/themes/index.json:487` depends on a paid or account-bound service (kept)
  - `references/themes/kiln.md:94` depends on a paid or account-bound service (kept)
  - `references/themes/rim.md:81` depends on a paid or account-bound service (kept)
  - `references/themes/riso.md:81` depends on a paid or account-bound service (kept)
  - `scripts/fixtures/exemplars/modern-minimal.html:8` depends on a paid or account-bound service (left out)
  - `scripts/fixtures/exemplars/modern-minimal.html:11` depends on a paid or account-bound service (left out)
  - and 9 more in MERGE.md

## What is here

- `HALLMARK.md`: the original SKILL.md, unchanged, renamed so agents never load it as a second skill. Its own file references still hold relative to this folder.
- `./` (1): `LICENSE`
- `references/` (22): `anatomy.md`, `brand-truth.md`, `craft.md`, `dark-mode.md`, `data-viz.md`, `design-md.md`, `direction.md`, `export-formats.md`, `fonts.md`, `gates.md`, `imagery.md`, `interaction-and-states.md`, `layout.md`, `macrostructures.md` and 8 more
- `scripts/` (6): `capture.mjs`, `photos.json`, `picture.mjs`, `sloplint-render.mjs`, `sloplint.mjs`, `theme.mjs`
- `references/genres/` (4): `atmospheric.md`, `editorial.md`, `modern-minimal.md`, `playful.md`
- `references/macrostructures/` (21): `01-bento-grid.md`, `02-long-document.md`, `03-marquee-hero.md`, `04-stat-led.md`, `05-workbench.md`, `06-conversational-faq.md`, `07-manifesto.md`, `08-photographic.md`, `09-quote-led.md`, `10-specimen.md`, `11-catalogue.md`, `12-letter.md`, `13-index-first.md`, `14-narrative-workflow.md` and 7 more
- `references/themes/` (98): `README.md`, `almanac.jpg`, `almanac.md`, `arcade.jpg`, `arcade.md`, `atelier.jpg`, `atelier.md`, `bloom.jpg`, `bloom.md`, `blueprint.jpg`, `blueprint.md`, `broadside.jpg`, `broadside.md`, `brutal.jpg` and 84 more

Inline in `../SKILL.md`: "The Floor", "Flow", "7. Sweep".

## Changes made

- "The Floor" (lines 16 to 38 of the original): 3 relative path(s) pointed at `hallmark/`.
- "Flow" (lines 39 to 53 of the original): 2 relative path(s) pointed at `hallmark/`.
- "7. Sweep" (lines 142 to 151 of the original): 3 relative path(s) pointed at `hallmark/`.

## Left out, and why

- `scripts/fixtures/slopped.html`, `scripts/fixtures/exemplars/atmospheric.html`, `scripts/fixtures/exemplars/editorial.html`, `scripts/fixtures/exemplars/modern-minimal.html`, `scripts/fixtures/exemplars/playful.html`, `scripts/fixtures/eyebrow-fail/index.html`, `scripts/fixtures/eyebrow-pass/index.html`, `scripts/fixtures/kept/after.html` and 9 more: test code, not needed to use the skill.
- `scripts/install-hook.mjs`, `scripts/install.mjs`, `scripts/lint-hook.mjs`: installer or hook; the compiled skill is installed as a whole and changes no agent settings.
- `agents/openai.yaml`: another agent's manifest; nothing here reads it.
- `references/comp.md`: generates comps through Together AI, a paid service the author works with; needs TOGETHER_API_KEY.
- `references/flow.md`: Hallmark's per-harness branches and its edit-time hook; this skill's modes replace them.
- `scripts/imagegen.mjs`: calls an external service that needs an API key.
- `scripts/refcheck.mjs`: script that writes agent settings.
- Section "Hallmark" of SKILL.md: Hallmark's own one-line introduction; the compiled intro replaces it.

## Licence duties

- Keep the copyright and permission notice in every copy: LICENSE travels in the source folder.

## Updating

Run the `update-skills` skill on `../`: it diffs Nutlope/hallmark against commit 7ec8682, re-reads every changed file, re-runs the eval and asks before replacing anything.
