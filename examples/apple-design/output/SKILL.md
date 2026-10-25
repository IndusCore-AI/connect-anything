---
name: apple-design
description: "The default skill for any design task: websites, landing pages, app screens, components, claude.ai artifacts, reviews and polish. For new work it picks the design with Hallmark's themes and page shapes and UI UX Pro Max's product reasoning; on every change it holds Hallmark's floor against AI-looking UI, runs its mechanical check, and finishes with Apple's interaction pass: instant press feedback, interruptible spring motion, enter and exit on one path, reduced-motion fallbacks. Use whenever anything people see or touch is designed, built, reviewed or changed."
license: MIT. Each source folder holds its own LICENSE
---

# Apple Design

One design skill made from three. Hallmark (`hallmark/`) chooses and checks the design, UI UX Pro Max (`uiux-pro-max/`) reasons about the product and carries the UX rules, and the Apple pass (`apple-pass/`) sets how anything a person touches responds and moves. When they disagree, the list below settles it; `MERGE.md` names each disagreement and the winner.

**What wins, top first:**
1. The user's own words in the conversation
2. The project's locked system: its tokens, copy rules, i18n and screenshot checks (CLAUDE.md, design.md, token files). This skill refines; it never restyles a screen that already has a system
3. Honesty: no invented metric, testimonial, logo or quote (the Floor, rule 8)
4. Hallmark's Floor and its mechanical check, `hallmark/scripts/sloplint.mjs`
5. The Apple pass, on everything a person touches
6. UI UX Pro Max's product reasoning and UX rules; its palette and page-pattern picks give way to the Floor
7. Taste

## Pick the mode first

| The task | Mode | Do |
| --- | --- | --- |
| Change a screen in a repo that has a design system (tokens, a Tailwind theme, `design.md`) | Refine | Keep the system. Apply the Floor where it does not contradict the system. Search the concern with `uiux-pro-max/scripts/search.py "<concern>" --domain ux`. Then the sweep and the Apple pass. |
| A new screen inside an existing product | Extend | Inherit the product's tokens and components. Controls 32 to 40px with a 44px hit target. For phones, finish with `uiux-pro-max/references/pro-rules.md`. |
| A new page with no system yet | Direct | Follow Hallmark's flow below: theme, shape, build, sweep. Product reasoning first: `uiux-pro-max/scripts/search.py "<product> <industry>" --design-system`. |
| One component | Component | The Floor, every control state, the Apple pass. |
| A review with no build | Review | Run the sweep's check, walk the Floor, `uiux-pro-max/references/quick-reference.md` priorities 1 to 3, and the Apple pass. Rank findings by what a user would notice. |

Paths are relative to this skill's folder (in Claude Code, `${CLAUDE_SKILL_DIR}`). Run the search with plain `python3`, not `-I`: it imports its own `core.py`.

## The Floor

Binds every output in every harness, none of it waivable, even when nothing else is read.

1. Every colour and every font goes through a token declared at `:root` (or a declared theme block). No literal colour or `font-family` past the token block. (48)
2. Never `transition: all`. Never animate `width`, `height`, `top` or `left`. (10a)
3. Never one italic word inside a roman heading. (38i)
4. `overflow-x: clip` on both `html` and `body`. Never `hidden`, never `100vw`. (34)
5. Image-bearing grid tracks use `minmax(0, 1fr)`; display heads carry `overflow-wrap: break-word; min-width: 0`. (50)
6. Every interactive element has `:focus-visible`, appearing instantly. (26a, 15)
7. Every animation has a `prefers-reduced-motion: reduce` fallback, and content is visible with scripting off. (27, 62)
8. Never an invented metric, testimonial, logo wall or case-study count. (46a)
9. Never an eyebrow, and never a label in tracked capitals or small caps: labels, captions, table heads, tags and nav links are the body face (or the theme's label face), a step smaller, sentence or lower case, untracked. (54, 67)
10. Never middle-dot-joined meta strings, arrows glued to link text, or decorative status dots. (63)
11. Never a purple-to-blue gradient, a card inside a card, an emoji as an icon, or a hand-drawn browser or OS window. (2a, 4, 30a, 47a)
12. The hero's headline, one sentence and primary action are all visible at 1280 x 800 without scrolling. (44b)
13. About 80 words on any one screen; the hero's text is the headline, one sentence and its actions. (58)
14. The container is capped and centred: at 1920 the gutters grow, the measure and the grids do not. (44d)
15. The first non-empty line of the CSS source is the Hallmark stamp, then the critique line, then any waivers. (20)
16. If Node is available, run `node <skill-dir>/hallmark/scripts/sloplint.mjs <output> --render` before handing back. Fix every `FAIL`; fix or waive every `REFLEX`.

Above the Floor, a **Reflex** gate is a default a model falls into, waivable on the record with a real reason, and a **Finish** check is craft detail, answered, never blocking ([`hallmark/references/gates.md`](hallmark/references/gates.md) § 1 and § 2).

## Flow

0. Pre-flight: read the project before asking anything.
1. Ask once: material, audience, use, tone.
2. Shape: design the page, then name it.
3. Direction: deal a theme, or design freely when asked for custom.
4. Load the layout, imagery, craft, genre and theme files and `gates.md` § 1 to § 4.
5. The Picks block, once.
6. Build: the hero first, then the page; stamp, `tokens.css`, log.
7. Sweep: `sloplint --render` until clean, the judged gates, the finish review, the material ask.

**Verbs,** only when the user names Hallmark: `redesign <target>` (a full redesign keeping content and wiring) and `audit <target>` (a report); read [`hallmark/references/redesign.md`](hallmark/references/redesign.md) first. Any other change to an existing design is not a Hallmark run: do it as asked, in the project's own system.

Codex CLI and OpenCode read `references/flow.md` § Harnesses first; other harnesses run this file as written.

### 7. Sweep

1. `node <skill-dir>/hallmark/scripts/sloplint.mjs <files> --genre <genre> --render` (`--scope component` or `--scope app` where it applies; in a framework project, `--url http://localhost:<port>/<route>` with the dev server running). Fix every FAIL and re-run until clean. The render tier writes the screenshots; never drive a browser by hand.
2. Load [`hallmark/references/gates.md`](hallmark/references/gates.md) § 5 and walk the J and R/J gates. Confirm or dismiss every WARN. Fix every open Floor finding; fix or waive every Reflex one; answer every Finish one.
3. The finish review in fresh context (`gates.md` § 6; the reviewer reads its prompt, you never open `review-*.md`): act on its first word (`recapture`, `rebuild`, `fix`, `ship`) and score the fixes yourself.
4. Close with the material ask: every slot, its size and what belongs there, then the one piece of material that would most improve the page.
5. Update the Picks block: any row the build changed, and the last row with the outcome (`Floor 0 FAIL · Reflex 2 (1 waived: 47b) · finish-review: subagent, 3 resolved`). A fabricated pass is itself slop.

Verification is budgeted: one batched inspection, one fix batch, at most one confirming round; each review adds one fix batch and its recapture.

## Running the search tool

The search script lives inside this skill's own directory, not the project directory. Always invoke it by its full path, do not assume a particular working directory:

```bash
python "${CLAUDE_PLUGIN_ROOT}/.claude/skills/ui-ux-pro-max/scripts/search.py" "<query>" --domain <domain>
```

If `python` is not found, try `python3`, then `py -3`. Requires Python 3.x, no external dependencies (see README for install instructions if Python is missing).

## 1. Response, kill latency

The moment lag appears, the feeling of directness "falls off a cliff." Response is the foundation everything else is built on.

- **Respond on pointer-down, not on release.** Highlight a button the instant it's pressed. Waiting for `click`/touch-up to show feedback feels dead.
- **Be vigilant about every latency.** Audit debounces, artificial timers, transition waits, and the ~300ms tap delay. Anything on the input path that isn't essential is a regression.
- **Feedback must be continuous *during* the interaction, not just at the end.** For a drag, slider, or drawer, update the UI 1:1 with the pointer the whole way through, never animate only when the gesture completes.

```css
/* Feedback lives on the press, and it's instant */
.button:active {
  transform: scale(0.97);
  transition: transform 100ms ease-out;
}
```

## 3. Interruptibility, the single most important principle

> "The thought and the gesture happen in parallel."

Every animation must be interruptible and redirectable at any moment. A user must be able to grab a moving element mid-flight and reverse it without waiting for the animation to finish. A closing modal the user grabs again should follow the finger, not finish closing first, then reopen.

- **Never lock out input during a transition.**
- **Always animate from the *presentation* (current) value, never the target value.** On interrupt, read the element's live on-screen transform and start the new animation from there. Starting from the logical/target value causes a visible jump.
- **Avoid CSS transitions and `@keyframes` for anything gesture-driven**, they can't be smoothly grabbed and reversed mid-flight. Springs animate from the current value by default, which is exactly what interruption needs.
- **When a gesture reverses, blend velocity, don't hard-cut it.** Replacing one animation with another at a reversal creates a velocity discontinuity, a "brick wall." Spring libraries that carry velocity through a re-target avoid it. (This is what iOS's *additive animations* do natively; on the web, choose a spring library that re-targets from the current velocity.)
- **Decompose 2D motion into independent X and Y springs.** A single spring on a 2D distance desyncs when X and Y have different velocities.

## 4. Behavior over animation, use springs

> "Think of animation as a conversation between you and the object, not something prescribed by the interface."

A pre-scripted, fixed-duration animation can't respond to new input. A spring can, new input just changes the target, and the motion stays continuous. Reach for springs for anything a user can touch.

Apple deliberately replaced the physics triplet (mass/stiffness/damping) with two designer-friendly parameters. Think in these:

- **Damping ratio**, controls overshoot. `1.0` = critically damped, no bounce, smooth settle. `< 1.0` = overshoots and oscillates. Lower = bouncier.
- **Response**, how quickly the value reaches the target, in seconds. Lower = snappier. **This is not "duration"**, a spring has no fixed duration; its settle time emerges from the parameters.

**Defaults:**
- Start most UI at **damping `1.0`** (critically damped), graceful and non-distracting.
- Add bounce (**damping ~`0.8`**) **only when the gesture itself carried momentum** (a flick, a throw, a drag release). Overshoot on a menu that just faded in feels wrong; overshoot on a card you flicked feels right.

**Concrete values Apple ships:**

| Interaction | Damping | Response |
| --- | --- | --- |
| Move / reposition (e.g. PiP) | `1.0` | `0.4` |
| Rotation | `0.8` | `0.4` |
| Drawer / sheet | `0.8` | `0.3` |

**Web mapping (Motion / Framer Motion):** the `bounce` + `duration` spring API maps closely to Apple's damping + response. A safe house style is `damping: 1.0` springs everywhere by default; reserve bounce for momentum-driven, physical interactions.

```js
import { animate } from 'motion';

// Critically damped default (no overshoot)
animate(el, { y: 0 }, { type: 'spring', bounce: 0, duration: 0.4 });

// Momentum interaction, a little bounce, only because a flick preceded it
animate(el, { y: target }, { type: 'spring', bounce: 0.2, duration: 0.4 });
```

## 7. Spatial consistency, symmetric paths, anchored origins

> "If something disappears one way, we expect it to emerge from where it came."

- **Enter and exit along the same path.** A panel that slides in from the right must dismiss to the right. In-from-right / out-the-bottom feels disconnected and confusing.
- **Anchor interactions to their source.** A menu, popover, or sheet should originate from the element that triggered it, set `transform-origin` to the trigger, so the spatial relationship between button and content is obvious. (This is the same origin-awareness point as popovers scaling from their trigger, not their center.)
- **Mirror the easing on reversible transitions** so the outbound path matches the return path (use inverse cubic-bézier control points for the two directions).

## 14. Reduced motion & accessibility

Reduced motion doesn't mean *no* feedback, it means a gentler, non-vestibular equivalent. Respond to three independent signals and bake them into your components:

- **`prefers-reduced-motion: reduce`**, replace slides/springs/parallax with short opacity **cross-fades or static transitions**. Drop elastic/overshoot. Keep opacity/color changes that aid comprehension.
- **`prefers-reduced-transparency: reduce`**, make translucent surfaces frostier/solid: raise background opacity, drop the blur.
- **`prefers-contrast: more`**, near-solid backgrounds with a defined, contrasting border.

Also: avoid full-viewport moving backgrounds, slow looping oscillations (near 0.2 Hz / one cycle per 5s), and abrupt brightness jumps (ease dark↔light theme changes). Make large moving objects semi-transparent while they travel, and fade big surfaces out during a large reposition and back in once settled.

```css
@media (prefers-reduced-motion: reduce) {
  .sheet { transition: opacity 200ms ease; transform: none !important; }
}
@media (prefers-reduced-transparency: reduce) {
  .toolbar { background: white; backdrop-filter: none; }
}
```

## Quick Reference

| Need | Technique | Concrete value |
| --- | --- | --- |
| Default UI spring | Critically damped, no overshoot | `damping 1.0`, `response 0.3 to 0.4` |
| Momentum / flick spring | Under-damped, slight bounce | `damping ~0.8`, `response 0.3 to 0.4` |
| Gesture → spring velocity | Hand off release velocity | `gestureVelocity / (target − current)` if normalized |
| Flick landing point | Project momentum | `current + (v/1000)·d/(1−d)`, `d ≈ 0.998` |
| Interrupt cleanly | Start from presentation (live) value | read the on-screen transform |
| Avoid reversal "brick wall" | Carry velocity through re-target | spring that blends velocity |
| Reversible transition | Mirror the easing curve | inverse cubic-bézier |
| Decide reverse vs. commit | Use velocity **sign**, not position | at release |
| 1:1 drag | Pointer Events + capture | respect the grab offset |
| Feedback | On pointer-down, continuous | never only at the end |
| Boundary | Rubber-band, don't hard-stop | progressive resistance |
| Translucent chrome | `backdrop-filter` layer | content scrolls under |
| Type tracking | Size-specific, never fixed | tighten large text (`-0.02em`), body near `0` |
| Reduced motion | Cross-fade, not slide/spring | `@media (prefers-reduced-motion)` |

## Where the rest is

Read these only when a step above sends you to them.

- `apple-pass/`: 1 files from apple-design. `apple-pass/APPLE-PASS.md` is the selected text, with "Part C: The Apple pass", "The Core Idea", "2. Direct manipulation, 1:1 tracking", "5. Velocity handoff, the seam between drag and animation", "6. Momentum projection, animate to where the gesture is *going*", "8. Hint in the direction of the gesture", "9. Rubber-banding, soft boundaries", "10. Gesture design details (the "feel" checklist)" and 6 more sections.
- `hallmark/`: 153 files from hallmark. `hallmark/HALLMARK.md` is its original SKILL.md, with "Branches".
  - `hallmark/references/` (22): `anatomy.md`, `brand-truth.md`, `craft.md`, `dark-mode.md`, `data-viz.md`, `design-md.md`, `direction.md`, `export-formats.md`, `fonts.md`, `gates.md` and 12 more
  - `hallmark/scripts/` (6): `capture.mjs`, `photos.json`, `picture.mjs`, `sloplint-render.mjs`, `sloplint.mjs`, `theme.mjs`
  - `hallmark/references/genres/` (4): `atmospheric.md`, `editorial.md`, `modern-minimal.md`, `playful.md`
  - `hallmark/references/macrostructures/` (21): `01-bento-grid.md`, `02-long-document.md`, `03-marquee-hero.md`, `04-stat-led.md`, `05-workbench.md`, `06-conversational-faq.md`, `07-manifesto.md`, `08-photographic.md`, `09-quote-led.md`, `10-specimen.md` and 11 more
  - `hallmark/references/themes/` (98): `README.md`, `almanac.jpg`, `almanac.md`, `arcade.jpg`, `arcade.md`, `atelier.jpg`, `atelier.md`, `bloom.jpg`, `bloom.md`, `blueprint.jpg` and 88 more
- `uiux-pro-max/`: 42 files from ui-ux-pro-max. `uiux-pro-max/UIUX-PRO-MAX.md` is its original SKILL.md, with "UI/UX Pro Max - Design Intelligence", "Rule Categories by Priority", "Workflow", "Query Contract", "If a search returns 0 results", "Example Workflow", "Output Formats", "Tips for Better Results" and 1 more sections.
  - `uiux-pro-max/data/` (13): `app-interface.csv`, `charts.csv`, `colors.csv`, `google-fonts.csv`, `icons.csv`, `landing.csv`, `motion.csv`, `products.csv`, `react-performance.csv`, `styles.csv` and 3 more
  - `uiux-pro-max/references/` (2): `pro-rules.md`, `quick-reference.md`
  - `uiux-pro-max/scripts/` (4): `core.py`, `design_system.py`, `reasoning_contract.py`, `search.py`
  - `uiux-pro-max/data/stacks/` (22): `angular.csv`, `astro.csv`, `avalonia.csv`, `flutter.csv`, `html-tailwind.csv`, `javafx.csv`, `jetpack-compose.csv`, `laravel.csv`, `nextjs.csv`, `nuxt-ui.csv` and 12 more

## Sources

- `apple-pass/`: ~/.claude/skills/apple-design/SKILL.md (content 53731f8), the compiler's own text, copied. `apple-pass/README.md` says what was kept and why.
- `hallmark/`: Nutlope/hallmark @ 7ec8682 (2026-10-22), MIT, copied. `hallmark/README.md` says what was kept and why.
- `uiux-pro-max/`: nextlevelbuilder/ui-ux-pro-max-skill @ d14efff (2026-10-23), MIT, copied. `uiux-pro-max/README.md` says what was kept and why.
