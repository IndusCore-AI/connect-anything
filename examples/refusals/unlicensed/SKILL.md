---
name: mobile-screens
description: Design mobile app screens. Combines mobile-app-design, pixel-perfect, podo into one skill with one trigger.
license: MIT. Each source folder holds its own LICENSE
---

# Mobile Screens

One skill for design mobile app screens. It combines `podo/`, `mobile-app-design` (named only), `pixel-perfect` (named only). When two of them disagree, the list below settles it; `MERGE.md` names every conflict and the winner.

**What wins, top first:**
1. The user's own words in the conversation
2. The project's locked system: its tokens, copy rules, i18n and checks (CLAUDE.md, design.md, config files)
3. Safety, licence and honesty rules from any source; a merge never weakens one
4. The sources in this order: `podo`
5. A rule a mechanical check enforces beats one it does not
6. The more specific rule beats the general one
7. Taste

## Invoke after install

- Skill name: `mobile-app-ui-design`
- Triggers: "mobile UI", "mobile-app-ui-design", "alive interfaces", "smooth mobile"

## What it does

Craft-focused mobile UI design skill modeled on the visual and interaction patterns of top-tier apps. Guides creating interfaces that feel intentional (purposeful hierarchy and spacing), smooth (natural motion and transitions), personal (adapted to context and user), and alive (responsive micro-interactions). Use when quality of craft is the primary concern.

## Skills this one runs (not copied)

Their licences do not allow copying, so this skill names them and you install the originals. Run each at the point the steps above call for it: in Claude Code invoke it by name, in other agents read its SKILL.md.

- `mobile-app-design`: awesome-skills/mobile-app-design @ 83e4721. Install: `npx skills add awesome-skills/mobile-app-design` or `gh skill install awesome-skills/mobile-app-design`. See `mobile-app-design/README.md`.
- `pixel-perfect`: UMDhodi/pixel-perfect-mobile @ ee3ceee. Install: `npx skills add UMDhodi/pixel-perfect-mobile` or `gh skill install UMDhodi/pixel-perfect-mobile`. See `pixel-perfect/README.md`.

## Where the rest is

Read these only when a step above sends you to them.

- `podo/`: 2 files from podo/design-agent-skills. `podo/PODO.md` is its original SKILL.md, with "mobile-app-ui-design", "Decision tree", "When NOT to use".

## Sources

- `mobile-app-design/`: awesome-skills/mobile-app-design @ 83e4721 (2026-02-05), NOASSERTION, named, not copied. `mobile-app-design/README.md` says what was kept and why.
- `pixel-perfect/`: UMDhodi/pixel-perfect-mobile @ ee3ceee (2026-05-04), NOASSERTION, named, not copied. `pixel-perfect/README.md` says what was kept and why.
- `podo/`: podo/design-agent-skills @ 8eeb2a7 (2026-10-21), MIT, copied. `podo/README.md` says what was kept and why.
