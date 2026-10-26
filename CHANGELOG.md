# Changelog

## 0.1.1 (2026-10-26)

The repository moved to the IndusCore-AI organisation, and a second independent review of the engine and its
threat model was fixed in full, each finding with a regression test.

- Every URL, manifest and lockfile now points at `IndusCore-AI/connect-anything`; the plugin and marketplace
  versions are 0.1.1.
- A lockfile is treated as untrusted input. `update` refuses a skill name, folder or file path that is absolute,
  contains `..`, or otherwise escapes the folder, before it joins any of them to a real path. `apply --to` needs
  `--force` to replace an existing folder that is not the installed skill, and refuses a target that contains the
  work folder or the proposal.
- The proposal lockfile now describes the proposal: refreshed refs, dates, licence, file hashes, read counts,
  scan summary, kept files and the eval. `update apply` no longer inherits stale hashes.
- `verify` catches a kept file that changed after compilation, a symbolic link anywhere in the skill, and a
  missing folder for a referenced source; a section source and a deliberately cut file are exempt from the hash
  they could never match.
- The scanner catches a script downloaded to a file and run later, not only a download piped straight into a shell.
- A UTF-8 byte-order mark no longer hides a skill's frontmatter.
- A blank `needs` entry no longer scores 1.00 for free; an eval set made only of blanks is not scored.
- A `--dry-run` no longer requires `--max-cost-usd`; a real live run still does.
- `--allow` survives a section moving into the root SKILL.md, because allowed findings now match by text as well
  as by path, line and rule.
- `--strip` works for a section source's renamed main file, and drops the overlapping inline sections as well as
  the cut copy; a cut with no destination is an error, not a silent skip.
- Licence titles are anchored, so the AGPL text is not read as GPL and the MPL text is not read as AGPL; a
  public-domain or copyleft base licence is returned before the restriction scan, so a mention of commercial use
  no longer turns it into a proprietary licence.
- Non-ASCII folder hashes now use a deterministic NFKD collation that matches Node's `localeCompare` for Latin
  accents. Non-Latin scripts fall back to code-point order, documented in `references/lockfile.md`.
- 11 new offline tests (56 in all) cover each fix.

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
