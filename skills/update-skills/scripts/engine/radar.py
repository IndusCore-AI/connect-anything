"""Read skill-radar's report so compile can take its candidates. skill-radar does the watching and scoring;
this module only parses what it wrote (~/.skill-radar/reports/<ts>.md, or latest.md).

The report is in Chinese; its headings and labels are spelled here by code point so this file stays ASCII.
"""
import os
import re

from .util import EngineError

REPORT_DIR = os.path.expanduser("~/.skill-radar/reports")


def _u(*cps):
    return "".join(chr(c) for c in cps)


STAR, DOT = _u(0x2605), _u(0x00B7)
PICKS = _u(0x4E3A, 0x4F60, 0x6311, 0x7684)            # "picked for you"
TRENDING = _u(0x65B0, 0x51FA, 0x7684, 0x70ED, 0x95E8)  # "new and trending"
LISTS = _u(0x7CBE, 0x9009, 0x699C, 0x5355)            # "curated lists"
MATCH, STRUCT, NONE = _u(0x5339, 0x914D), _u(0x7ED3, 0x6784), _u(0x65E0)
PATH_LABEL = "SKILL.md " + _u(0x8DEF, 0x5F84, 0xFF1A)
ENTRY = re.compile(r"^- \*\*\[([A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+)\]\((https://github\.com/[^)]+)\)\*\*\s*" + STAR + r"(\d+)(.*)$")


def report_path(spec):
    if spec in (None, "", "latest"):
        p = os.path.join(REPORT_DIR, "latest.md")
    else:
        p = os.path.expanduser(spec)
    if not os.path.exists(p):
        raise EngineError(f"no skill-radar report at {p}. Run: python3 -I ~/.claude/skills/skill-radar/scripts/radar.py")
    return os.path.realpath(p)


def parse_report(path):
    section, out = None, []
    lines = open(path, encoding="utf-8").read().splitlines()
    for i, line in enumerate(lines):
        if line.startswith("## "):
            section = "picks" if PICKS in line else "trending" if TRENDING in line else "lists" if LISTS in line else "other"
            continue
        m = ENTRY.match(line)
        if not m:
            continue
        repo, url, stars, rest = m.group(1), m.group(2), int(m.group(3)), m.group(4)
        lic = rest.split(DOT)[-1].strip() if DOT in rest else ""
        nxt = lines[i + 1] if i + 1 < len(lines) else ""
        desc = nxt.strip() if nxt.startswith("  ") and not nxt.strip().startswith((MATCH, STRUCT)) else ""
        bits = lines[i + 2].strip() if i + 2 < len(lines) else ""
        paths = re.findall(re.escape(PATH_LABEL) + r"([^" + DOT + r"]+)", bits)
        out.append({"repo": repo, "url": url, "stars": stars, "licence": "none" if NONE in lic else lic,
                    "section": section, "description": desc,
                    "paths": [p.strip() for p in (paths[0].split(",") if paths else [])], "spec": repo})
    return out


def candidates_from_report(spec, pick=5, repos=None):
    entries = parse_report(report_path(spec))
    if repos:
        wanted = [r.strip() for r in repos.split(",") if r.strip()]
        by = {e["repo"].lower(): e for e in entries}
        missing = [w for w in wanted if w.lower() not in by]
        if missing:
            raise EngineError(f"not in the report: {', '.join(missing)}")
        return [by[w.lower()] for w in wanted]
    picks = [e for e in entries if e["section"] == "picks"]
    return (picks + [e for e in entries if e["section"] != "picks"])[:pick]
