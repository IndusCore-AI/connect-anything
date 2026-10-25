---
name: screen-kit
description: Design dashboards and app screens. Combines ios-app-design into one skill with one trigger.
license: MIT. Each source folder holds its own LICENSE
---

# Screen Kit

One skill for design dashboards and app screens. It combines ios-app-design (`ios-app-design/`). When two of them disagree, the list below settles it; `MERGE.md` names every conflict and the winner.

**What wins, top first:**
1. The user's own words in the conversation
2. The project's locked system: its tokens, copy rules, i18n and checks (CLAUDE.md, design.md, config files)
3. Safety, licence and honesty rules from any source; a merge never weakens one
4. The sources in this order: `ios-app-design`
5. A rule a mechanical check enforces beats one it does not
6. The more specific rule beats the general one
7. Taste

## iOS App Design

Choose interface behavior that fits the product, target OS, and existing UI framework. Inspect deployment targets and current components before proposing new APIs or visual-system adoption.

## Design Criteria

- Use familiar system navigation and controls when they support the task. Preserve established product behavior unless a redesign is requested.
- Keep content readable and actions reachable across supported sizes, orientations, text sizes, and appearances.
- Include accessibility semantics, sufficient contrast, and reduced-motion behavior appropriate to the interaction.
- Give immediate feedback for actions. Distinguish motion polish from actual rendering, network, or input latency.
- Treat Liquid Glass adoption as a compatibility and design decision. Do not replace opaque backgrounds or custom controls merely to match a newer OS style; consider readability, accessibility settings, and the requested scope.
- Apply SwiftUI, UIKit, and React Native examples only within the matching implementation environment. Verify version-sensitive APIs against installed tooling and official Apple documentation before use.

## Read by Decision

| Decision | Reference |
|----------|-----------|
| Adopting or tuning Liquid Glass materials | [Liquid Glass](ios-app-design/references/liquid-glass.md) |
| Choosing tabs, navigation stacks, modals, or search | [Navigation](ios-app-design/references/navigation.md) |
| Safe areas, adaptive layout, or iPad presentation | [Layout](ios-app-design/references/layout.md) |
| Text hierarchy and Dynamic Type | [Typography](ios-app-design/references/typography.md) |
| Semantic colors, contrast, or theme behavior | [Color and theme](ios-app-design/references/color-and-theme.md) |
| Symbols, imagery, or app icons | [Icons and imagery](ios-app-design/references/icons-and-imagery.md) |
| Transitions, springs, or gesture continuity | [Motion](ios-app-design/references/motion.md) |
| VoiceOver, contrast, and accessibility settings | [Accessibility](ios-app-design/references/accessibility.md) |
| Haptic and visual feedback | [Haptics and feedback](ios-app-design/references/haptics-and-feedback.md) |

Read only references relevant to the current decision. Their examples and preferred values are starting points, not universal adoption requirements.

## Where the rest is

Read these only when a step above sends you to them.

- `ios-app-design/`: 10 files from ios-app-design. `ios-app-design/IOS-APP-DESIGN.md` is its original SKILL.md, with "Completion".
  - `ios-app-design/references/` (9): `accessibility.md`, `color-and-theme.md`, `haptics-and-feedback.md`, `icons-and-imagery.md`, `layout.md`, `liquid-glass.md`, `motion.md`, `navigation.md`, `typography.md`

## Sources

- `ios-app-design/`: ahonn/dotfiles @ 27f1e58 (2026-10-08), MIT, copied. `ios-app-design/README.md` says what was kept and why.
