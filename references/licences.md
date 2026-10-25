# Licences

The licence check runs in the fetch step, before anything is chosen, and its result is written to each source's README and the lockfile. It reads the licence files in the skill's folder and then each parent up to the repo root, and the SKILL.md `license` field. The nearest folder with a recognised licence decides; when it holds several (code under MIT, documents under CC BY), every one of them is met. When the frontmatter and the file disagree, the stricter one wins and the mismatch is noted.

| Licence | Verdict | What the compiled skill carries |
| --- | --- | --- |
| MIT, ISC, BSD-2-Clause, BSD-3-Clause | copy | The source's `LICENSE` in its folder, which holds the copyright and permission notice ("shall be included in all copies or substantial portions"). |
| MIT-0, 0BSD, Unlicense, CC0-1.0 | copy | Nothing is required; the source is credited anyway. |
| Apache-2.0 | copy | `LICENSE` in the folder; the `NOTICE` file's contents in `NOTICE`; every change to copied text stated in the source README, and in SKILL.md for text that changed inline ("cause any modified files to carry prominent notices stating that You changed the files"). |
| CC-BY-4.0 | copy | Credit (the copyright line, or the repo owner, and the URL), a link to the licence, and the changes made, in the source README. |
| none, NOASSERTION, unknown | name only | Nothing is copied. "No one may reproduce, distribute, or create derivative works" without a licence (GitHub's licensing docs). The output names the skill and how to install it. |
| NonCommercial or NoDerivatives (CC BY-NC, CC BY-ND), proprietary, "all rights reserved" | name only | As above. |
| GPL, AGPL, LGPL, MPL, CC-BY-SA | name only by default | Copying would put the whole compiled skill under those terms. Named and installed by the user instead. |
| your own text (`--own <alias>`, local sources only) | copy | Recorded in the lock as `LicenseRef-Own`. You assert you hold the rights. |

## Named, not copied

A referenced source gets a folder with only a README: the source, its commit, why it is not copied, and the install lines (`npx skills add owner/repo`, `gh skill install owner/repo`). The compiled SKILL.md has a "Skills this one runs (not copied)" section that tells the agent when to run each one: invoke it by name in Claude Code, or read its SKILL.md in other agents. This is the thin orchestrator; `--orchestrate` makes every source work this way, for when the originals must stay live.

## What the engine changes in copied files

Nothing, except:

- the source's `SKILL.md` is renamed `<ALIAS>.md` so no loader sees a second skill inside the first;
- a `README.md`, `LICENSE` or `NOTICE` at the source's root is kept as `SOURCE-README.md` (and so on), beside the compiler's own README;
- a promotional section cut with `--strip` is removed from the copy, and the cut is recorded with its line range.

Text copied inline into SKILL.md can change: relative paths are pointed at the source folder, a heading level shifts, a duplicate rule is removed, dashes are replaced under `--plain-dashes`, or the agent rewrites it with an override. Every such change is listed per section in the source README under "Changes made".

## The compiled skill's own licence

The frontmatter `license` line names the licences of the copied sources ("MIT AND CC-BY-4.0. Each source folder holds its own LICENSE"). The text the compiler wrote is yours; the copied parts stay under their own terms.
