# ui-ux-pro-max (from nextlevelbuilder/ui-ux-pro-max-skill)

Source: https://github.com/nextlevelbuilder/ui-ux-pro-max-skill, commit d14efff (2026-10-23), MIT licence (`LICENSE`). Merged into `apple-design` on 2026-10-26, after every file was read in full and scanned.

## Read and scanned

- 73 files, 3,582,979 bytes, read in full (every byte, secondary files included).
- Scanner: 0 blocking, 38 to review, 5 informational.
- Scripts that make network calls: `scripts/tests/test_web_stack_freshness.py`. None of them is kept.
- Flagged for review (38), with what was done:
  - `data/colors.csv:106` depends on a paid or account-bound service (kept)
  - `data/products.csv:106` depends on a paid or account-bound service (kept)
  - `data/products.csv:112` skill-radar pattern 9 (kept)
  - `data/stacks/angular.csv:50` depends on a paid or account-bound service (kept)
  - `data/stacks/flutter.csv:2` depends on a paid or account-bound service (kept)
  - `data/stacks/flutter.csv:6` depends on a paid or account-bound service (kept)
  - `data/stacks/flutter.csv:7` depends on a paid or account-bound service (kept)
  - `data/stacks/flutter.csv:10` depends on a paid or account-bound service (kept)
  - `data/stacks/flutter.csv:11` depends on a paid or account-bound service (kept)
  - `data/stacks/flutter.csv:14` depends on a paid or account-bound service (kept)
  - `data/stacks/flutter.csv:16` depends on a paid or account-bound service (kept)
  - `data/stacks/flutter.csv:18` depends on a paid or account-bound service (kept)
  - `data/stacks/flutter.csv:19` depends on a paid or account-bound service (kept)
  - `data/stacks/flutter.csv:22` depends on a paid or account-bound service (kept)
  - `data/stacks/flutter.csv:24` depends on a paid or account-bound service (kept)
  - `data/stacks/flutter.csv:25` depends on a paid or account-bound service (kept)
  - `data/stacks/flutter.csv:26` depends on a paid or account-bound service (kept)
  - `data/stacks/flutter.csv:27` depends on a paid or account-bound service (kept)
  - `data/stacks/flutter.csv:28` depends on a paid or account-bound service (kept)
  - `data/stacks/flutter.csv:32` depends on a paid or account-bound service (kept)
  - `data/stacks/flutter.csv:34` depends on a paid or account-bound service (kept)
  - `data/stacks/flutter.csv:35` depends on a paid or account-bound service (kept)
  - `data/stacks/flutter.csv:36` depends on a paid or account-bound service (kept)
  - `data/stacks/flutter.csv:38` depends on a paid or account-bound service (kept)
  - `data/stacks/flutter.csv:39` depends on a paid or account-bound service (kept)
  - and 13 more in MERGE.md

## What is here

- `UIUX-PRO-MAX.md`: the original SKILL.md, unchanged, renamed so agents never load it as a second skill. Its own file references still hold relative to this folder.
- `data/` (13): `app-interface.csv`, `charts.csv`, `colors.csv`, `google-fonts.csv`, `icons.csv`, `landing.csv`, `motion.csv`, `products.csv`, `react-performance.csv`, `styles.csv`, `typography.csv`, `ui-reasoning.csv`, `ux-guidelines.csv`
- `references/` (2): `pro-rules.md`, `quick-reference.md`
- `scripts/` (4): `core.py`, `design_system.py`, `reasoning_contract.py`, `search.py`
- `data/stacks/` (22): `angular.csv`, `astro.csv`, `avalonia.csv`, `flutter.csv`, `html-tailwind.csv`, `javafx.csv`, `jetpack-compose.csv`, `laravel.csv`, `nextjs.csv`, `nuxt-ui.csv`, `nuxtjs.csv`, `react-native.csv`, `react.csv`, `shadcn.csv` and 8 more

Inline in `../SKILL.md`: "Running the search tool".

## Changes made

- "Running the search tool" (lines 37 to 46 of the original): em and en dashes replaced (house style).

## Left out, and why

- `scripts/tests/test_catalog_refresh.py`, `scripts/tests/test_catalog_summary_line_endings.py`, `scripts/tests/test_core.py`, `scripts/tests/test_core_data_quality.py`, `scripts/tests/test_data_contracts.py`, `scripts/tests/test_design_system_mode.py`, `scripts/tests/test_design_system_stack.py`, `scripts/tests/test_native_desktop_stack_freshness.py` and 18 more: test code, not needed to use the skill.
- `data/catalog-summary.json`, `data/data-provenance.json`, `data/google-font-licenses.json`, `data/phosphor-icons-upstream.json`: read only by the data validator, which is left out.
- `scripts/validate_data.py`: the source's data validator, for its maintainers.
- Section "When to Apply" of SKILL.md: trigger or intro text; the compiled description covers it.

## Licence duties

- Keep the copyright and permission notice in every copy: LICENSE travels in the source folder.

## Updating

Run the `update-skills` skill on `../`: it diffs nextlevelbuilder/ui-ux-pro-max-skill against commit d14efff, re-reads every changed file, re-runs the eval and asks before replacing anything.
