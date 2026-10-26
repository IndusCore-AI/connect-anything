# MERGE.md: how `apple-design` was made

Mode: `connect`. Job: Design, build or review any screen people see or touch: choose the design for new work, hold a floor against AI-looking UI, run the mechanical check, and finish with Apple's interaction pass

## Sources

| Source | Commit | Licence | Use | Read | Scan (block / review / info) |
| --- | --- | --- | --- | --- | --- |
| `apple-pass` ~/.claude/skills/apple-design/SKILL.md | 53731f8 | LicenseRef-Own (own) | copied | 1 files, 38,282 B | 0 / 1 / 0 |
| `hallmark` Nutlope/hallmark | 7ec8682 | MIT (flatten) | copied | 178 files, 6,841,340 B | 0 / 34 / 17 |
| `uiux-pro-max` nextlevelbuilder/ui-ux-pro-max-skill | d14efff | MIT (flatten) | copied | 73 files, 3,582,979 B | 0 / 38 / 5 |

## What wins, top first

1. The user's own words in the conversation
2. The project's locked system: its tokens, copy rules, i18n and screenshot checks (CLAUDE.md, design.md, token files). This skill refines; it never restyles a screen that already has a system
3. Honesty: no invented metric, testimonial, logo or quote (the Floor, rule 8)
4. Hallmark's Floor and its mechanical check, `hallmark/scripts/sloplint.mjs`
5. The Apple pass, on everything a person touches
6. UI UX Pro Max's product reasoning and UX rules; its palette and page-pattern picks give way to the Floor
7. Taste

## Conflicts (4 settled, 21 dismissed as not a conflict)

| # | Topic | Says | Says | Winner | Why |
| --- | --- | --- | --- | --- | --- |
| c12 | smooth | `apple-pass`: **Avoid CSS transitions and `@keyframes` for anything gesture-driven**, they can't be smoothly grabbed and reversed mid-flight. Springs... | `uiux-pro-max`: `state-transition` - State changes (hover / active / expanded / collapsed / modal) should animate smoothly, not snap | `apple-pass` | for anything a finger drives, a spring that can be grabbed mid-flight; a CSS transition stays fine for hover and state changes nothing... (agent confirmed) |
| c17 | bold | `hallmark`: **Display:** Switzer 500, `--tracking-display` on the hero head and -0.03em on section heads, line-height 1.02, sentence case, roman.... | `uiux-pro-max`: `weight-hierarchy` - Use font-weight to reinforce hierarchy: Bold headings (600 to 700), Regular body (400), Medium labels (500) (MD) | `hallmark` | on a new page the theme's display face and weight stand (rank 4); UI UX Pro Max's 600 to 700 heading weights are a generic default (agent confirmed) |
| c18 | bold | `hallmark`: **Display:** Young Serif 400, `--tracking-display`, line-height 1.02, sentence case, roman, one colour per head. Its one weight is the... | `uiux-pro-max`: `weight-hierarchy` - Use font-weight to reinforce hierarchy: Bold headings (600 to 700), Regular body (400), Medium labels (500) (MD) | `hallmark` | the same: the theme's display weight stands on a new page (agent confirmed) |
| c24 | spac | `hallmark`: **Scaffold:** `theme.mjs scaffold --custom`. Fill every `--color-*` and `--font-*`; the scale it writes is a start, not a style, so set... | `uiux-pro-max`: `spacing-scale` - Use 4pt/8dp incremental spacing system (Material Design) | `hallmark` | a new page takes the scale the theme scaffold writes; in a product the repo's own tokens win over both (rank 2) (agent confirmed) |

Dismissed:

- c1 (duration, enter, exit): Hallmark sets the duration tokens, UI UX Pro Max says an exit takes the shorter one; both hold
- c2 (hit, target): both hold: a 44px target, and about 10px of slop around it while a press is held
- c3 (hit, target): different subjects (press slop, button emphasis)
- c4 (mask, fade): different subjects
- c5 (lazy, load): the same rule: the hero image is eager, everything below the fold is lazy
- c6 (float, sticky): different subjects (scroll edges, nav height)
- c7 (padd, down): different subjects (press slop, grid spacing)
- c8 (highlight, down): different subjects (press slop, a theme's pill buttons)
- c9 (gap, target): different subjects (a theme's crop marks, target spacing)
- c10 (touch, target): both hold: 8px between targets, and press slop around each
- c11 (touch, target): both hold: inputs at least 44px tall, and press slop around them
- c13 (literal): different subjects
- c14 (silent): different subjects
- c15 (flow): complementary: dim for a modal task; never use a modal for primary navigation
- c16 (interaction): complementary
- c19 (animate): complementary: one hover signal; state changes animate rather than snap
- c20 (animate): complementary
- c21 (fall): different subjects
- c22 (heavier): different subjects
- c23 (transition): different subjects
- c25 (navig): a theme lends looks, never navigation; Android's top app bar is navigation. Both hold

## Duplicates folded: one copy per rule (0)

None found.

## Sections

| Source | Section | Lines | Tokens | Score | Use | Why |
| --- | --- | --- | --- | --- | --- | --- |
| `apple-pass` | Part C: The Apple pass | 147 to 152 | 194 | 0.343 | reference | the Apple pass's own introduction; its rules are inline below |
| `apple-pass` | The Core Idea | 153 to 160 | 160 | 0.05 | reference | kept in the source folder |
| `apple-pass` | 1. Response, kill latency | 161 to 176 | 239 | 0.085 | inline | press feedback is part of every interactive change |
| `apple-pass` | 2. Direct manipulation, 1:1 tracking | 177 to 193 | 219 | 0.098 | reference | score 0.098: kept in the source folder; the SKILL.md budget is full |
| `apple-pass` | 3. Interruptibility, the single most important... | 194 to 205 | 399 | 0.321 | inline | the principle the rest of the motion rules serve |
| `apple-pass` | 4. Behavior over animation, use springs | 206 to 240 | 535 | 0.341 | inline | the default spring values |
| `apple-pass` | 5. Velocity handoff, the seam between drag and... | 241 to 252 | 211 | 0.103 | reference | score 0.103: kept in the source folder; the SKILL.md budget is full |
| `apple-pass` | 6. Momentum projection, animate to where the... | 253 to 273 | 317 | 0.27 | reference | not in the chosen order for SKILL.md; kept in the source folder |
| `apple-pass` | 7. Spatial consistency, symmetric paths,... | 274 to 281 | 224 | 0.09 | inline | enter and exit on one path |
| `apple-pass` | 8. Hint in the direction of the gesture | 282 to 285 | 84 | 0.0 | reference | kept in the source folder |
| `apple-pass` | 9. Rubber-banding, soft boundaries | 286 to 296 | 151 | 0.0 | reference | kept in the source folder |
| `apple-pass` | 10. Gesture design details (the "feel" checklist) | 297 to 303 | 210 | 0.173 | reference | score 0.173: kept in the source folder; the SKILL.md budget is full |
| `apple-pass` | 11. Frame-level smoothness | 304 to 311 | 146 | 0.0 | reference | kept in the source folder |
| `apple-pass` | 12. Materials & depth, translucency conveys... | 312 to 331 | 574 | 0.029 | reference | kept in the source folder |
| `apple-pass` | 13. Multimodal feedback, motion + sound + haptics | 332 to 339 | 200 | 0.048 | reference | kept in the source folder |
| `apple-pass` | 14. Reduced motion & accessibility | 340 to 358 | 327 | 0.0 | inline | the fallback every animation needs |
| `apple-pass` | 15. Typography, optical sizing, tracking, leading | 359 to 379 | 417 | 0.07 | reference | score 0.07: kept in the source folder; the SKILL.md budget is full |
| `apple-pass` | 16. Design foundations, the eight principles | 380 to 399 | 1022 | 0.416 | reference | background reasoning; one read away in `apple-pass/APPLE-PASS.md` |
| `apple-pass` | 17. Process | 400 to 405 | 162 | 0.6 | reference | process advice; one read away |
| `apple-pass` | Quick Reference | 406 to 423 | 352 | 0.0 | inline | the values table, so the rest of the pass can stay one read away |
| `hallmark` | Hallmark | 10 to 15 | 88 | 0.551 | drop | Hallmark's own one-line introduction; the compiled intro replaces it |
| `hallmark` | The Floor | 16 to 38 | 610 | 0.339 | inline | the rules every output must meet; it carries the mechanical check |
| `hallmark` | Flow | 39 to 53 | 256 | 0.409 | inline | the order of work for a new page |
| `hallmark` | 0. Pre-flight | 54 to 59 | 268 | 0.116 | reference | score 0.116: kept in the source folder; the SKILL.md budget is full |
| `hallmark` | 1. Ask once | 60 to 71 | 575 | 0.364 | reference | score 0.364: kept in the source folder; the SKILL.md budget is full |
| `hallmark` | 2. Shape | 72 to 85 | 682 | 0.257 | reference | score 0.257: kept in the source folder; the SKILL.md budget is full |
| `hallmark` | 3. Direction | 86 to 101 | 340 | 0.315 | reference | long; Direct mode reads it from `hallmark/HALLMARK.md` |
| `hallmark` | 4. Load | 102 to 109 | 342 | 0.197 | reference | score 0.197: kept in the source folder; the SKILL.md budget is full |
| `hallmark` | 5. The Picks block | 110 to 128 | 346 | 0.101 | reference | score 0.101: kept in the source folder; the SKILL.md budget is full |
| `hallmark` | 6. Build | 129 to 141 | 961 | 0.324 | reference | score 0.324: kept in the source folder; the SKILL.md budget is full |
| `hallmark` | 7. Sweep | 142 to 151 | 349 | 0.521 | inline | how to run the check before handing back |
| `hallmark` | Branches | 152 to 154 | 120 | 0.26 | reference | score 0.26: kept in the source folder; the SKILL.md budget is full |
| `uiux-pro-max` | UI/UX Pro Max - Design Intelligence | 6 to 9 | 76 | 0.059 | reference | score 0.059: kept in the source folder; the SKILL.md budget is full |
| `uiux-pro-max` | When to Apply | 10 to 15 | 175 | 0.483 | drop | trigger or intro text; the compiled description covers it |
| `uiux-pro-max` | Rule Categories by Priority | 16 to 36 | 642 | 0.199 | reference | score 0.199: kept in the source folder; the SKILL.md budget is full |
| `uiux-pro-max` | Running the search tool | 37 to 46 | 133 | 0.314 | inline | the one command every mode uses |
| `uiux-pro-max` | Workflow | 47 to 48 | 4 | 0.0 | reference | kept in the source folder |
| `uiux-pro-max` | Query Contract | 49 to 64 | 658 | 0.391 | reference | long; read from `uiux-pro-max/UIUX-PRO-MAX.md` when a query needs it |
| `uiux-pro-max` | Step 1: Analyze User Requirements | 65 to 72 | 212 | 0.207 | reference | score 0.207: kept in the source folder; the SKILL.md budget is full |
| `uiux-pro-max` | Step 2: Generate Design System (REQUIRED for... | 73 to 87 | 191 | 0.143 | reference | score 0.143: kept in the source folder; the SKILL.md budget is full |
| `uiux-pro-max` | Step 2b: Persist Design System (Master +... | 88 to 110 | 437 | 0.443 | reference | writes design-system files into the project, which a repo with a locked system must... |
| `uiux-pro-max` | Step 2c: Design Dials (optional) | 111 to 133 | 427 | 0.034 | reference | kept in the source folder |
| `uiux-pro-max` | Step 3: Supplement with Detailed Searches (as... | 134 to 156 | 406 | 0.148 | reference | score 0.148: kept in the source folder; the SKILL.md budget is full |
| `uiux-pro-max` | Step 4: Stack Guidelines | 157 to 166 | 124 | 0.0 | reference | kept in the source folder |
| `uiux-pro-max` | If a search returns 0 results | 167 to 173 | 117 | 0.0 | reference | kept in the source folder |
| `uiux-pro-max` | Example Workflow | 174 to 190 | 181 | 0.064 | reference | score 0.064: kept in the source folder; the SKILL.md budget is full |
| `uiux-pro-max` | Output Formats | 191 to 194 | 59 | 0.062 | reference | score 0.062: kept in the source folder; the SKILL.md budget is full |
| `uiux-pro-max` | Tips for Better Results | 195 to 211 | 349 | 0.252 | reference | score 0.252: kept in the source folder; the SKILL.md budget is full |
| `uiux-pro-max` | Before Delivering App UI | 212 to 214 | 85 | 0.205 | reference | score 0.205: kept in the source folder; the SKILL.md budget is full |
| compiler | Pick the mode first | | 339 | | inline | written for this merge: none of the three sources says which of them leads for which... |

## Files left out

- `hallmark`: `agents/openai.yaml` (another agent's manifest; nothing here reads it); `references/comp.md` (generates comps through Together AI, a paid service the author works with; needs TOGETHER_API_KEY); `references/flow.md` (Hallmark's per-harness branches and its edit-time hook; this skill's modes replace them); `scripts/imagegen.mjs` (calls an external service that needs an API key); `scripts/install-hook.mjs` (installer or hook; the compiled skill is installed as a whole and changes no agent settings); `scripts/install.mjs` (installer or hook; the compiled skill is installed as a whole and changes no agent settings); `scripts/lint-hook.mjs` (installer or hook; the compiled skill is installed as a whole and changes no agent settings); `scripts/refcheck.mjs` (script that writes agent settings); `scripts/fixtures/slopped.html` (test code, not needed to use the skill); `scripts/fixtures/exemplars/atmospheric.html` (test code, not needed to use the skill); `scripts/fixtures/exemplars/editorial.html` (test code, not needed to use the skill); `scripts/fixtures/exemplars/modern-minimal.html` (test code, not needed to use the skill); `scripts/fixtures/exemplars/playful.html` (test code, not needed to use the skill); `scripts/fixtures/eyebrow-fail/index.html` (test code, not needed to use the skill); `scripts/fixtures/eyebrow-pass/index.html` (test code, not needed to use the skill); `scripts/fixtures/kept/after.html` (test code, not needed to use the skill); `scripts/fixtures/kept/before.html` (test code, not needed to use the skill); `scripts/fixtures/tailwind-fail/Feature.vue` (test code, not needed to use the skill); `scripts/fixtures/tailwind-fail/Hero.tsx` (test code, not needed to use the skill); `scripts/fixtures/tailwind-fail/index.html` (test code, not needed to use the skill); `scripts/fixtures/tailwind-fail/style.css` (test code, not needed to use the skill); `scripts/fixtures/tailwind-pass/Hero.tsx` (test code, not needed to use the skill); `scripts/fixtures/tailwind-pass/index.html` (test code, not needed to use the skill); `scripts/fixtures/tailwind-pass/style.css` (test code, not needed to use the skill); `scripts/fixtures/waiver/index.html` (test code, not needed to use the skill)
- `uiux-pro-max`: `data/catalog-summary.json` (read only by the data validator, which is left out); `data/data-provenance.json` (read only by the data validator, which is left out); `data/google-font-licenses.json` (read only by the data validator, which is left out); `data/phosphor-icons-upstream.json` (read only by the data validator, which is left out); `scripts/validate_data.py` (the source's data validator, for its maintainers); `scripts/tests/test_catalog_refresh.py` (test code, not needed to use the skill); `scripts/tests/test_catalog_summary_line_endings.py` (test code, not needed to use the skill); `scripts/tests/test_core.py` (test code, not needed to use the skill); `scripts/tests/test_core_data_quality.py` (test code, not needed to use the skill); `scripts/tests/test_data_contracts.py` (test code, not needed to use the skill); `scripts/tests/test_design_system_mode.py` (test code, not needed to use the skill); `scripts/tests/test_design_system_stack.py` (test code, not needed to use the skill); `scripts/tests/test_native_desktop_stack_freshness.py` (test code, not needed to use the skill); `scripts/tests/test_relevance_evaluator.py` (test code, not needed to use the skill); `scripts/tests/test_skill_script_paths.py` (test code, not needed to use the skill); `scripts/tests/test_style_taxonomy.py` (test code, not needed to use the skill); `scripts/tests/test_text_layout_resilience.py` (test code, not needed to use the skill); `scripts/tests/test_web_stack_freshness.py` (test code, not needed to use the skill); `scripts/tests/fixtures/relevance-baseline.json` (test code, not needed to use the skill); `scripts/tests/fixtures/relevance-cases.json` (test code, not needed to use the skill); `scripts/tests/fixtures/relevance-thresholds.json` (test code, not needed to use the skill); `scripts/tests/fixtures/catalogs/google-api.json` (test code, not needed to use the skill); `scripts/tests/fixtures/catalogs/google-catalog.json` (test code, not needed to use the skill); `scripts/tests/fixtures/catalogs/google-existing.csv` (test code, not needed to use the skill); `scripts/tests/fixtures/catalogs/google-metadata.json` (test code, not needed to use the skill); `scripts/tests/fixtures/catalogs/google-overrides.json` (test code, not needed to use the skill); `scripts/tests/fixtures/catalogs/icons-curated.csv` (test code, not needed to use the skill); `scripts/tests/fixtures/catalogs/phosphor-core.json` (test code, not needed to use the skill); `scripts/tests/fixtures/catalogs/phosphor-package.json` (test code, not needed to use the skill); `scripts/tests/fixtures/catalogs/phosphor-react-exports.json` (test code, not needed to use the skill); and 1 more, listed in `uiux-pro-max/README.md`

## Flagged for review (73)

- `apple-pass/SKILL.md:26` touches agent configuration
- `hallmark/SKILL.md:56` references an API key or token
- `hallmark/references/comp.md:3` references an API key or token
- `hallmark/references/comp.md:98` references an API key or token
- `hallmark/references/flow.md:14` touches agent configuration
- `hallmark/references/flow.md:101` references an API key or token
- `hallmark/references/flow.md:119` touches agent configuration
- `hallmark/references/fonts.md:20` depends on a paid or account-bound service
- `hallmark/references/genres/modern-minimal.md:3` depends on a paid or account-bound service
- `hallmark/references/imagery.md:13` references an API key or token
- `hallmark/references/imagery.md:79` references an API key or token
- `hallmark/references/layout.md:100` skill-radar pattern 16
- `hallmark/references/macrostructures/12-letter.md:8` skill-radar pattern 16
- `hallmark/references/themes/README.md:20` depends on a paid or account-bound service
- `hallmark/references/themes/atelier.md:85` depends on a paid or account-bound service
- `hallmark/references/themes/bloom.md:89` depends on a paid or account-bound service
- `hallmark/references/themes/bloom.md:90` depends on a paid or account-bound service
- `hallmark/references/themes/coral.md:9` depends on a paid or account-bound service
- `hallmark/references/themes/coral.md:89` depends on a paid or account-bound service
- `hallmark/references/themes/hum.md:88` depends on a paid or account-bound service
- `hallmark/references/themes/index.json:487` depends on a paid or account-bound service
- `hallmark/references/themes/kiln.md:94` depends on a paid or account-bound service
- `hallmark/references/themes/rim.md:81` depends on a paid or account-bound service
- `hallmark/references/themes/riso.md:81` depends on a paid or account-bound service
- `hallmark/scripts/fixtures/exemplars/modern-minimal.html:8` depends on a paid or account-bound service
- `hallmark/scripts/fixtures/exemplars/modern-minimal.html:11` depends on a paid or account-bound service
- `hallmark/scripts/imagegen.mjs:52` references an API key or token
- `hallmark/scripts/imagegen.mjs:57` references an API key or token
- `hallmark/scripts/imagegen.mjs:58` references an API key or token
- `hallmark/scripts/install-hook.mjs:15` touches agent configuration
- `hallmark/scripts/install-hook.mjs:16` touches agent configuration
- `hallmark/scripts/install-hook.mjs:54` touches agent configuration
- `hallmark/scripts/install-hook.mjs:55` touches agent configuration
- `hallmark/scripts/refcheck.mjs:84` touches agent configuration
- `hallmark/scripts/sloplint.mjs:1713` zero-width characters
- `uiux-pro-max/data/colors.csv:106` depends on a paid or account-bound service
- `uiux-pro-max/data/products.csv:106` depends on a paid or account-bound service
- `uiux-pro-max/data/products.csv:112` skill-radar pattern 9
- `uiux-pro-max/data/stacks/angular.csv:50` depends on a paid or account-bound service
- `uiux-pro-max/data/stacks/flutter.csv:2` depends on a paid or account-bound service
- `uiux-pro-max/data/stacks/flutter.csv:6` depends on a paid or account-bound service
- `uiux-pro-max/data/stacks/flutter.csv:7` depends on a paid or account-bound service
- `uiux-pro-max/data/stacks/flutter.csv:10` depends on a paid or account-bound service
- `uiux-pro-max/data/stacks/flutter.csv:11` depends on a paid or account-bound service
- `uiux-pro-max/data/stacks/flutter.csv:14` depends on a paid or account-bound service
- `uiux-pro-max/data/stacks/flutter.csv:16` depends on a paid or account-bound service
- `uiux-pro-max/data/stacks/flutter.csv:18` depends on a paid or account-bound service
- `uiux-pro-max/data/stacks/flutter.csv:19` depends on a paid or account-bound service
- `uiux-pro-max/data/stacks/flutter.csv:22` depends on a paid or account-bound service
- `uiux-pro-max/data/stacks/flutter.csv:24` depends on a paid or account-bound service
- `uiux-pro-max/data/stacks/flutter.csv:25` depends on a paid or account-bound service
- `uiux-pro-max/data/stacks/flutter.csv:26` depends on a paid or account-bound service
- `uiux-pro-max/data/stacks/flutter.csv:27` depends on a paid or account-bound service
- `uiux-pro-max/data/stacks/flutter.csv:28` depends on a paid or account-bound service
- `uiux-pro-max/data/stacks/flutter.csv:32` depends on a paid or account-bound service
- `uiux-pro-max/data/stacks/flutter.csv:34` depends on a paid or account-bound service
- `uiux-pro-max/data/stacks/flutter.csv:35` depends on a paid or account-bound service
- `uiux-pro-max/data/stacks/flutter.csv:36` depends on a paid or account-bound service
- `uiux-pro-max/data/stacks/flutter.csv:38` depends on a paid or account-bound service
- `uiux-pro-max/data/stacks/flutter.csv:39` depends on a paid or account-bound service

## Notes from the compiler

- Tracking: the Apple pass adds slight positive tracking to small text, while Hallmark's Floor (rule 9) keeps labels, captions and table heads untracked. The more specific rule wins for labels; the Apple pass's tracking applies to small running text. The conflict scan pairs these rules only loosely, so this one is recorded by hand.
- UI UX Pro Max's persist step writes `design-system/<project>/MASTER.md` into the project. In a repo with a locked system that is the system's job, so the step is referenced, not inline, and rank 2 of the list covers it.
- Glass: Hallmark's genre files and most themes refuse translucent panels, while the Apple pass builds toolbars from them. The theme wins on a new page (rank 4); the Apple pass's reduced-transparency fallback applies wherever glass is used. The conflict scan does not see this one because the two sources name it differently (glass, translucent); it is recorded here by hand.
- The default file rules keep `hallmark/scripts/capture.mjs` and `picture.mjs` (local puppeteer screenshots). The hand-made skill cut them because the team captures with Playwright; that is a team preference, so they stay here.

## Against `~/.claude/skills/apple-design`

Files: 196 in both, 1 only in the hand-made skill, 5 only here.
- Same file, another name: `uiux-pro-max/UIUX.md` there is `uiux-pro-max/UIUX-PRO-MAX.md` here.

Only in the hand-made skill:

- `scripts/` (1): `check.mjs`. The hand-made `scripts/check.mjs` is a wrapper written for that merge (it filters sloplint for locked repos). The compiler ships the source's own check, `hallmark/scripts/sloplint.mjs`, unchanged, and the sweep section says how to run it.

Only here:

- `apple-pass/` (2): `APPLE-PASS.md`, `README.md`. The hand-made skill keeps this text inline in its SKILL.md; here the selected section gets its own folder so its origin is recorded, and the parts that do not fit the budget are read from there.
- `hallmark/` (1): `SOURCE-LICENSE`. Kept here by the default file rules; the hand-made merge cut it by judgement. Set `keep: false` in the plan to match.
- `hallmark/scripts/` (2): `capture.mjs`, `picture.mjs`. Kept here by the default file rules; the hand-made merge cut it by judgement. Set `keep: false` in the plan to match.

SKILL.md, section by section (hand-made heading, closest heading here, word overlap):

| Hand-made | Here | Overlap | Reading |
| --- | --- | --- | --- |
| Apple Design | Apple Design | 0.26 | written by hand for the merge; no source has it. Add it as an extra section if it should be here |
| Start here: pick the mode | Pick the mode first | 0.30 | Hand-written glue in the hand-made skill. Here a shorter mode table is written for the merge as an extra section, recorded as such. |
| Part A: The Floor (every mode) | The Floor | 0.27 | The hand-made skill rewrote Hallmark's Floor in its own words with house exceptions. Here Hallmark's Floor is inline unchanged, and the house exceptions belong to the repo's locked system, which ranks second in the list. |
| Part B: Direct mode, choosing the design | Pick the mode first | 0.11 | Hand-written from Hallmark's flow. Here Hallmark's own flow and sweep are inline; the long steps stay in `hallmark/HALLMARK.md`. |
| Part B2: Extend mode, app screens | Pick the mode first | 0.15 | Hand-written house rules for app screens. Not in any source; the update example fills this gap from the field. |
| Check before calling it done | 7. Sweep | 0.17 | Hand-written. Here Hallmark's sweep is inline. |
| Where the library is | Apple Design | 0.11 | written by hand for the merge; no source has it. Add it as an extra section if it should be here |
| Part C: The Apple pass | 3. Interruptibility, the single most important... | 0.10 | The source of `apple-pass/`. The hand-made skill carries all of it inline (about 6,100 tokens). Here the parts every change needs are inline and the rest is one read away, so the whole SKILL.md stays under the spec's 5,000 tokens. |
| The Core Idea | Apple Design | 0.05 | in a source but not inline here: it is in the source folder |
| 1. Response, kill latency | 1. Response, kill latency | 1.00 | same text |
| 2. Direct manipulation, 1:1 tracking | Quick Reference | 0.09 | in a source but not inline here: it is in the source folder |
| 3. Interruptibility, the single most important... | 3. Interruptibility, the single most important... | 1.00 | same text |
| 4. Behavior over animation, use springs | 4. Behavior over animation, use springs | 1.00 | same text |
| 5. Velocity handoff, the seam between drag and... | 3. Interruptibility, the single most important... | 0.08 | in a source but not inline here: it is in the source folder |
| 6. Momentum projection, animate to where the... | Quick Reference | 0.09 | in a source but not inline here: it is in the source folder |
| 7. Spatial consistency, symmetric paths,... | 7. Spatial consistency, symmetric paths,... | 1.00 | same text |
| 8. Hint in the direction of the gesture | 7. Spatial consistency, symmetric paths,... | 0.03 | in a source but not inline here: it is in the source folder |
| 9. Rubber-banding, soft boundaries | Quick Reference | 0.04 | in a source but not inline here: it is in the source folder |
| 10. Gesture design details (the "feel" checklist) | Quick Reference | 0.07 | in a source but not inline here: it is in the source folder |
| 11. Frame-level smoothness | 14. Reduced motion & accessibility | 0.05 | in a source but not inline here: it is in the source folder |
| 12. Materials & depth, translucency conveys... | 14. Reduced motion & accessibility | 0.08 | in a source but not inline here: it is in the source folder |
| 13. Multimodal feedback, motion + sound + haptics | 1. Response, kill latency | 0.04 | in a source but not inline here: it is in the source folder |
| 14. Reduced motion & accessibility | 14. Reduced motion & accessibility | 1.00 | same text |
| 15. Typography, optical sizing, tracking, leading | Quick Reference | 0.07 | in a source but not inline here: it is in the source folder |
| 16. Design foundations, the eight principles | 3. Interruptibility, the single most important... | 0.05 | in a source but not inline here: it is in the source folder |
| 17. Process | Flow | 0.03 | in a source but not inline here: it is in the source folder |
| Quick Reference | Quick Reference | 1.00 | same text |

Size: the hand-made SKILL.md body is 419 lines and about 10352 tokens; this one is 215 lines and about 4865 tokens.

## Checks

- PASS spec: frontmatter valid, name matches the folder
- PASS size: SKILL.md 220 lines (limit 500), body about 4865 tokens (limit 5000)
- PASS refs: every path SKILL.md names exists
- PASS one-copy: no rule appears twice
- PASS nested: one SKILL.md
- PASS scan: 0 blocking, 61 to review across 204 files; 0 promotional lines in compiler-written files
- PASS install_skill.py review: 8 lines flagged in total; 0 dangerous, 0 self-promotion in compiler-written files
- PASS no self-credit: the compiler names itself only in the lockfile
- PASS house style: no em or en dashes in compiler-written files

## Eval

**Verdict: PASS.** The compiled skill matches or beats running the originals.

| Measure | Run the originals | Compiled | Change |
| --- | --- | --- | --- |
| Static coverage (6 evals with needs) | 1.00 | 1.00 | +0.00 |
| Needs already in context on activation | 0.83 | 0.50 | -0.33 |
| Context on activation (est. tokens) | 15,345 (3 SKILL.md) | 4,865 (1 SKILL.md) | -10,480 |
| Listing (description characters) | 1,566 | 566 | -1,000 |
| Live tier | not run (pass --live with --max-cost-usd) | | |

| Eval | Needs | Originals | Compiled | Missing in the compiled skill |
| --- | --- | --- | --- | --- |
| sheet-dismiss | 4 | 4 | 4 |  |
| pottery-landing | 4 | 4 | 4 |  |
| dashboard-buttons-review | 2 | 2 | 2 |  |
| bengali-fonts | 2 | 2 | 2 |  |
| app-settings-screen | 2 | 2 | 2 |  |
| cheap-motion | 2 | 2 | 2 |  |

Tolerance for sampled answers: 0.05. Static coverage has no tolerance.
