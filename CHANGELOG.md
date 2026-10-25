# Changelog

## 0.1.0 (2026-10-25)

First version, private, for testing.

- Three skills on one engine: `connect-skills` (two or three skills into one), `compile-skills` (5 to 20 candidates into one, against a profile), `update-skills` (upstream diff, gap fill, proposal, approval).
- Engine (Python standard library): fetch at a locked commit, full read, scan (skill-radar's list plus more), licence check, choose, merge, lock, check, eval gate.
- `decisions.json` for the agent's judgement, carried in the lockfile.
- `connect-anything.lock.json` in the shape of the skills CLI's lockfile, with the same folder hash.
- Eval gate: static coverage on every build; live tier through `claude -p` with a budget; skill-creator's eval format.
- Examples: apple-design recreation, a five-candidate research compile, an app-screens update, refusals.
- 45 offline tests and 6 online acceptance tests; CI runs the offline tests on Python 3.9 and 3.12, the sync check and `skills-ref validate`.
- Hardened after an independent review: unreadable and UTF-16 files, update path handling, the gate when nothing was measured, untrusted source evals, local git config, scanner evasion, restrictive licences, allow pass-through, untrusted source names (DECISIONS.md, "Found by an independent review").
- Live eval runs are confined with `--restricted`.
