# How conflicts are settled

Two sources disagree when one forbids what the other asks for, or when both give a number in the same unit for the same thing and the numbers differ. The engine proposes candidates; the agent settles each one in `decisions.json`, and `MERGE.md` prints every one with its winner and the reason, including the ones dismissed as not a conflict.

## What wins, top first

Every compiled SKILL.md opens with this list, and the agent's choices follow it. The default:

1. **The user's own words** in the conversation.
2. **The project's locked system:** its tokens, copy rules, i18n and checks (CLAUDE.md, design.md, config). A merged skill refines a project; it never restyles one that has a system.
3. **Safety, licence and honesty rules** from any source. A merge never weakens one: if one source says "never invent a metric", that holds even where another is silent.
4. **The sources in the order the user gave them**, or `profile.sources`.
5. **A rule a mechanical check enforces** beats one it does not. A source that ships a check script (a linter, a validator) wins ties.
6. **The more specific rule** beats the general one ("labels are untracked" beats "small text is slightly tracked" for labels).
7. **Taste.**

Edit the list in `decisions.json` (`precedence`) when the job needs it. Keep it short: it is read on every activation.

## How the engine finds candidates

- **Polarity.** For each rule (a bullet or a numbered item) it collects the terms the rule forbids (the words after never, no, don't, avoid, cut, remove, until the clause ends; every item of a list under a heading such as "Common mistakes" or "Cut these") and the terms it asks for (the words after use, prefer, keep, always, add, by default). Two rules from different sources clash when one forbids a specific term the other asks for and they share at least two specific terms.
- **Numbers.** Both rules give a number in the same unit (px, ms, %, lines, tokens) and share specific terms, and the numbers differ.
- **Specific** means rare across all the rules being compared, and not a generic word (make, page, user, state).
- At most two candidates per topic term, 25 in all, so one busy word cannot crowd out the rest.

The scan is a helper, not a judge. On real sources about a third of its candidates are real tensions; the rest are rules that agree or talk about different things. It also misses conflicts the sources word differently (one says "glass", the other "translucent"). Read the sources, dismiss what is not a conflict with a reason, and add what it missed to `notes`.

## Duplicates: one copy per rule

Rules from two sources whose specific terms overlap heavily (an idf-weighted score of 0.55 or more) are duplicates. When both copies would sit inline, the loser's line is removed from the compiled text and the removal is recorded as a change. The winner is the source that ships a check script, then the higher-ranked source, then the longer wording. The `one-copy` check fails a build whose SKILL.md still holds two near-identical rules.

## The decisions file

`<name>.connect-anything/decisions.json` (or `--decisions <file>`). The build applies it to the freshly generated plan, so it survives a re-plan at a new commit, and the lockfile carries it so `update` can apply the same judgement again. Keys:

```json
{
  "title": "Apple Design",
  "description": "What it does and when to use it, under 1,024 characters.",
  "intro": "One paragraph under the title.",
  "precedence": ["The user's own words", "..."],
  "order": ["extra:pick-the-mode", "hallmark:hallmark-the-floor", "apple-pass:part-c-the-apple-pass-1-response-kill-latency"],
  "sources": {"philosopher-okf": {"mode": "excluded", "why": "produces a study page, not a brief"}},
  "sections": {"hallmark:flow-3-direction": {"action": "reference", "why": "long; one read away"}},
  "files": {"hallmark:references/comp.md": {"keep": false, "why": "needs a paid API key"}},
  "conflicts": {"844a9b6479": {"status": "confirmed", "winner": "hallmark", "why": "the more specific rule"}},
  "duplicates": {"62735d2331": {"status": "dismissed", "why": "different contexts"}},
  "extra_sections": [{"id": "pick-the-mode", "title": "Pick the mode first", "text": "## Pick the mode first\n...", "why": "written for this merge"}],
  "overrides": {"bug-bounty-triage:phase-5-...-knowledge-assumption-audit": "overrides/reader-test.md"},
  "compare_notes": {"scripts": "why the hand-made skill has a file this one does not"},
  "notes": ["anything a reader of MERGE.md should know"],
  "options": {"plain_dashes": true}
}
```

- `order` is the SKILL.md body. A section the plan had inline but `order` leaves out goes back to its source folder.
- `sources` can only exclude or reference a source. Copying is decided by the licence and the scan, never by a decision.
- `overrides` replace a section's text with the agent's rewrite. The change is recorded in the source README and, for Apache-2.0 or CC BY sources, stated in SKILL.md as those licences ask.
- Keys that no longer match anything (a section renamed upstream) are printed at build time and skipped.
- Conflict and duplicate keys are a hash of the two rule texts, so they stay the same across re-plans while the texts do.
