# connect-anything.lock.json

Every compiled skill carries one. It is the honest share unit: like `package-lock.json` names npm and the exact packages, this names the tool and the exact source commits, so anyone holding the skill can trace each part, check it, and update it.

The source entries borrow the shape of the `skills` CLI's `skills-lock.json` (vercel-labs/skills, `src/local-lock.ts`): `source`, `sourceUrl`, `sourceType`, `ref`, `skillPath`, `computedHash`, keyed by name and sorted. `computedHash` uses the same recipe (SHA-256 over each file's relative path then its bytes, files in Node `localeCompare` order), so the two tools agree on a folder's hash.

```json
{
  "version": 1,
  "tool": {"name": "connect-anything", "version": "0.1.0", "url": "https://github.com/gaurpulkit/connect-anything"},
  "skill": {"name": "apple-design", "mode": "connect", "computedHash": "<sha256 of the compiled folder, this file excluded>", "job": "..."},
  "skills": {
    "hallmark": {
      "source": "Nutlope/hallmark",
      "sourceUrl": "https://github.com/Nutlope/hallmark",
      "sourceType": "github",
      "ref": "7ec868225c6caa040558c321ee0fefa0e73f83a8",
      "skillPath": "skills/hallmark/SKILL.md",
      "computedHash": "<sha256 of the source skill folder at that commit>",
      "folder": "hallmark",
      "use": "flatten",
      "licence": {"spdx": "MIT", "verdict": "flatten", "file": "LICENSE"},
      "read": {"files": 178, "bytes": 6841340},
      "scan": {"block": 0, "review": 19, "info": 17, "allowed": 0},
      "files": {"SKILL.md": "<sha256>", "references/gates.md": "<sha256>"},
      "kept": ["SKILL.md", "references/gates.md"],
      "sections": [{"id": "hallmark-the-floor", "file": "SKILL.md", "lines": [16, 38], "hash": "<16 hex>", "use": "inline"}]
    }
  },
  "decisions": {"order": ["..."], "conflicts": {"...": {"status": "confirmed", "winner": "hallmark", "why": "..."}}},
  "eval": {"verdict": "pass", "tiers": ["static"], "originals": {"static": {}}, "compiled": {"static": {}}, "eval_set_hash": "...", "tolerance": 0.05}
}
```

## Fields

| Field | Meaning |
| --- | --- |
| `tool` | The tool that compiled the skill. The only credit anywhere in the output. |
| `skill.computedHash` | The compiled folder's hash with the lockfile left out. `connect verify <folder>` recomputes it: a mismatch means a file changed after compiling. |
| `skills.<alias>.ref` | The full commit the source was read at (for a local source, its content hash). |
| `skillPath` | Where the source's SKILL.md sits in its repo, so a monorepo is fetched for one skill only. |
| `use` | `flatten` (copied), `reference` (named, never copied, because of its licence or `--orchestrate`), `excluded` (with `excluded`, the reason). |
| `licence` | The SPDX id found, the verdict, and the file it came from. |
| `read` | How many files and bytes were read in full. |
| `scan` | Findings by severity when the source was compiled. |
| `files` | The hash of every file read. `update` compares these to find what changed. |
| `kept` | The files copied into the compiled skill. |
| `sections` | Each section of the source's SKILL.md that is inline or one read away, with its line range and a hash of its text; `modified` when the copy differs. |
| `decisions` | The agent's decisions, with override texts inlined, so `update` can re-apply them. |
| `eval` | The gate's verdict, the tiers that ran, both arms' scores, and the hash of the eval set. |

## How update uses it

1. For each `github` source with `use: flatten`, resolve the new commit and list files changed under `skillPath`'s folder since `ref`.
2. Re-read and re-scan each changed file in full.
3. Compare the installed copies with the source at `ref` to find local edits, which are never overwritten.
4. Re-apply `decisions` to the new plan; anything that no longer matches is reported.

A hand-made merged skill has no lock. `update plan --adopt` writes one from what its per-source READMEs say (a GitHub URL and a commit), and finds `skillPath` by matching the hash of the copied original SKILL.md against every skill in the repo at that commit.
