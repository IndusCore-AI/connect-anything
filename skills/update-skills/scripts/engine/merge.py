"""Merge step: turn an agreed plan into one skill folder.

  <name>/SKILL.md                    one trigger, the "what wins, top first" list, the inline sections
  <name>/<alias>/                    one folder per copied source: README.md, LICENSE, NOTICE, kept files
  <name>/<alias>/README.md           also written for a referenced source, with how to install the original
  <name>/MERGE.md                    every conflict, the winner and why; duplicates; what was cut and why
  <name>/connect-anything.lock.json  written by lock.py after the checks
  <name>/evals/evals.json            the eval set the gate used

Copied files are byte-for-byte unless the plan says otherwise; every change is listed in the source README,
and Apache-2.0 or CC BY text that changed carries the notice those licences ask for.
"""
import datetime as dt
import os
import re
import shutil

from .util import (EngineError, content_words, dump_frontmatter, estimate_tokens, has_dashes, parse_sections,
                   plain_dashes, split_frontmatter, write_text, LOCK_NAME)
from .licence import output_licence

NOTICE_LICENCES = {"Apache-2.0", "CC-BY-4.0"}


def renamed_skill_file(alias):
    return f"{alias.upper()}.md"


def vendored_name(alias, rel):
    """Where a source file lands in its folder: SKILL.md is renamed so no loader sees a second skill, and a
    README.md at the source's root is renamed so the compiler's README.md never overwrites it."""
    if rel == "SKILL.md":
        return renamed_skill_file(alias)
    if rel in ("README.md", "LICENSE", "NOTICE"):
        return "SOURCE-" + rel
    return rel


def _section_text(plan, src, sec, mods):
    key = f"{src['alias']}:{sec['id']}"
    text = sec["text"]
    override = plan.get("overrides", {}).get(key)
    if override:
        if isinstance(override, dict):
            text = override["text"]
        else:
            path = override if os.path.isabs(override) else os.path.join(plan["_workdir"], override)
            if not os.path.isfile(path):
                raise EngineError(f"override for {key} not found: {path}")
            text = open(path, encoding="utf-8").read()
        mods.append("rewritten by the compiler (see MERGE.md)")
    # one copy per rule: drop the losing copy of each duplicate that would otherwise sit inline twice
    for d in plan.get("duplicates", []):
        if d.get("status") == "dismissed":
            continue
        if d["dropped"]["source"] == src["alias"] and d["dropped"]["section"] == sec["id"]:
            kept_inline = _is_inline(plan, d["kept"]["source"], d["kept"]["section"])
            if kept_inline:
                pat = re.compile(r"^\s*(?:[-*+]|\d+[.)])\s+" + re.escape(d["dropped"]["text"]) + r"\s*$\n?", re.M)
                text, n = pat.subn("", text, count=1)
                if n:
                    mods.append(f"removed a rule that `{d['kept']['source']}` states too ({d['id']})")
    text, n_rebased = rebase_paths(text, src)
    if n_rebased:
        mods.append(f"{n_rebased} relative path(s) pointed at `{src['alias']}/`")
    # headings: the compiled skill has one H1, so a source's H1 becomes an H2 and its children follow
    lines = text.splitlines()
    outside = _outside_fences(lines)
    levels = [len(mm.group(1)) for i, mm in ((i, re.match(r"^(#{1,6})\s", l)) for i, l in enumerate(lines)) if mm and outside[i]]
    if levels and min(levels) == 1:
        lines = [("#" + l) if outside[i] and re.match(r"^#{1,5}\s", l) else l for i, l in enumerate(lines)]
        mods.append("heading levels shifted down one")
        text = "\n".join(lines) + "\n"
    if plan["options"].get("plain_dashes") and has_dashes(text):
        text = plain_dashes(text)
        mods.append("em and en dashes replaced (house style)")
    return text.rstrip() + "\n"


def rebase_paths(text, src):
    """Links and paths in copied text are relative to the source's own folder; point them at <alias>/."""
    alias = src["alias"]
    kept = {f["path"] for f in src["files"] if f["keep"]}
    dirs = {os.path.dirname(p) for p in kept}
    dirs |= {d.rsplit("/", i)[0] for d in list(dirs) for i in range(1, d.count("/") + 1)}
    known = kept | {d for d in dirs if d}

    def resolves(p):
        p = p.split("#")[0].rstrip("/")
        return p and not p.startswith((alias + "/", "/", "~", "http", "$")) and p in known

    count = [0]

    def link(m):
        target = m.group(2)
        if resolves(target):
            count[0] += 1
            return f"{m.group(1)}({alias}/{target})"
        return m.group(0)

    def tick(m):
        p = m.group(1)
        if resolves(p):
            count[0] += 1
            return f"`{alias}/{p}`"
        return m.group(0)

    def skilldir(m):
        p = m.group(2)
        if resolves(p):
            count[0] += 1
            return f"{m.group(1)}/{alias}/{p}"
        return m.group(0)

    out = re.sub(r"(\[[^\]]*\])\(([^)\s]+)\)", link, text)
    out = re.sub(r"`([A-Za-z0-9_.-]+(?:/[A-Za-z0-9_.-]+)*/?)`", tick, out)
    out = re.sub(r"(<skill-dir>|\$\{CLAUDE_SKILL_DIR\}|\{baseDir\})/([A-Za-z0-9_./-]+)", skilldir, out)
    return out, count[0]


def _outside_fences(lines):
    out, fence = [], None
    for l in lines:
        s = l.strip()
        mm = re.match(r"^(`{3,}|~{3,})", s)
        if mm:
            out.append(False)
            fence = None if fence and s.startswith(fence) else (fence or mm.group(1))
            continue
        out.append(fence is None)
    return out


def _is_inline(plan, alias, sec_id):
    src = next((s for s in plan["sources"] if s["alias"] == alias), None)
    sec = next((x for x in (src or {}).get("sections", []) if x["id"] == sec_id), None)
    return bool(sec and sec["action"] == "inline")


def _ordered_inline(plan):
    items = []
    for src in plan["sources"]:
        if src["mode"] != "flatten":
            continue
        for sec in src["sections"]:
            if sec["action"] == "inline":
                items.append((f"{src['alias']}:{sec['id']}", src, sec))
    for ex in plan.get("extra_sections", []):
        items.append((f"extra:{ex.get('id') or ex['title']}", None, ex))
    order = plan.get("order") or []
    if order:
        pos = {k: i for i, k in enumerate(order)}
        items.sort(key=lambda x: pos.get(x[0], len(order) + 1))
    else:
        extras = [i for i in items if i[1] is None]
        items = [i for i in items if i[1] is not None] + extras
    return items


def _dir_summary(paths, limit=10):
    groups = {}
    for p in paths:
        d = os.path.dirname(p)
        groups.setdefault(d, []).append(os.path.basename(p))
    out = []
    for d in sorted(groups, key=lambda x: (x.count("/"), x)):
        names = sorted(groups[d])
        shown = ", ".join(f"`{n}`" for n in names[:limit])
        more = f" and {len(names) - limit} more" if len(names) > limit else ""
        out.append((d, shown + more, len(names)))
    return out


def compose_skill_md(plan):
    flat = [s for s in plan["sources"] if s["mode"] == "flatten"]
    refd = [s for s in plan["sources"] if s["mode"] == "reference"]
    fm = {"name": plan["name"], "description": plan["description"],
          "license": output_licence([s["licence"] for s in flat], plan["options"].get("own_licence"))}
    out = [dump_frontmatter(fm), f"# {plan['title']}", ""]
    intro = plan.get("intro") or _default_intro(plan, flat, refd)
    out += [intro.strip(), ""]
    out.append("**What wins, top first:**")
    out += [f"{i}. {rule}" for i, rule in enumerate(plan["precedence"], 1)]
    out.append("")
    notices = []
    for key, src, sec in _ordered_inline(plan):
        if src is None:
            text = sec["text"].rstrip() + "\n"
            if not re.match(r"^#{2,3}\s", text):
                text = f"## {sec['title']}\n\n" + text
            out.append(text)
            continue
        mods = []
        text = _section_text(plan, src, sec, mods)
        sec["modified"] = bool(mods)
        sec["modifications"] = mods
        if mods and src["licence"]["spdx"] in NOTICE_LICENCES:
            notices.append(f"`{sec['title']}` from `{src['alias']}` ({src['licence']['spdx']}): " + "; ".join(mods))
        out.append(text)
    if refd:
        out.append("## Skills this one runs (not copied)")
        out.append("")
        out.append("Their licences do not allow copying, so this skill names them and you install the originals. "
                   "Run each at the point the steps above call for it: in Claude Code invoke it by name, in other agents read its SKILL.md.")
        out.append("")
        for s in refd:
            short = (s.get("ref") or "")[:7]
            # its own description is not repeated here: it is untrusted text, and once installed the skill's own
            # listing tells the agent when to run it
            out.append(f"- `{s['alias']}`: {s['source']} @ {short}. "
                       f"Install: `npx skills add {s['source']}` or `gh skill install {s['source']}`. See `{s['alias']}/README.md`.")
        out.append("")
    where = []
    for s in flat:
        kept = [f["path"] for f in s["files"] if f["keep"]]
        ref_secs = [x["title"] for x in s["sections"] if x["action"] == "reference" and x["level"] in (1, 2)]
        renamed = renamed_skill_file(s["alias"])
        line = f"- `{s['alias']}/`: {len(kept)} files from {s['source']}."
        what = "the selected text" if s.get("section_selector") else "its original SKILL.md"
        if ref_secs:
            line += f" `{s['alias']}/{renamed}` is {what}, with " + ", ".join(f"\"{_q(t)}\"" for t in ref_secs[:8])
            line += (f" and {len(ref_secs) - 8} more sections" if len(ref_secs) > 8 else "") + "."
        where.append(line)
        for d, shown, n in _dir_summary([p for p in kept if p != "SKILL.md"])[:6]:
            if d:
                where.append(f"  - `{s['alias']}/{d}/` ({n}): {shown}")
    if where:
        out += ["## Where the rest is", "", "Read these only when a step above sends you to them.", ""] + where + [""]
    out.append("## Sources")
    out.append("")
    for s in plan["sources"]:
        if s["mode"] == "excluded":
            continue
        short = (s.get("ref") or "")[:7]
        at = f"@ {short}" if s["sourceType"] != "local" else f"(content {short})"
        use = "copied" if s["mode"] == "flatten" else "named, not copied"
        lic = s["licence"]["spdx"] if s["licence"]["verdict"] != "own" else "the compiler's own text"
        out.append(f"- `{s['alias']}/`: {s['source']} {at}{' (' + s['date'] + ')' if s.get('date') and s['sourceType'] != 'local' else ''}, {lic}, {use}. "
                   f"`{s['alias']}/README.md` says what was kept and why.")
    if notices:
        out += ["", "Changed from the original, as the source licence asks: " + " ".join(notices)]
    out.append("")
    text = "\n".join(out)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text


def _one_line(text, n=180):
    t = re.sub(r"\s+", " ", text or "").strip()
    return (t[: n - 1].rsplit(" ", 1)[0] + "...") if len(t) > n else (t + ("" if t.endswith(".") or not t else "."))


def _default_intro(plan, flat, refd):
    names = [f"`{s['alias']}/`" for s in flat] + [f"`{s['alias']}` (named only)" for s in refd]
    job = plan.get("job") or "one job"
    return (f"One skill for {job[0].lower() + job[1:] if job else 'one job'}"
            f"{'' if job.endswith('.') else '.'} It combines {', '.join(names)}. "
            "When two of them disagree, the list below settles it; `MERGE.md` names every conflict and the winner.")


# ------------------------------------------------------------------ per-source README
def source_readme(plan, src):
    lic = src["licence"]
    short = (src.get("ref") or "")[:7]
    lines = [f"# {_q(src['name'])} (from {src['source']})", ""]
    when = dt.date.today().isoformat()
    if src["mode"] == "flatten":
        url = src.get("sourceUrl") or src["source"]
        lines.append(f"Source: {url}, commit {short}" + (f" ({src['date']})" if src.get("date") else "") +
                     (f", {lic['spdx']} licence (`LICENSE`)" if lic["verdict"] == "flatten" else ", the compiler's own text") +
                     f". Merged into `{plan['name']}` on {when}, after every file was read in full and scanned.")
    elif src["mode"] == "reference":
        lines.append(f"Source: {src.get('sourceUrl') or src['source']}, commit {short}. **Referenced, not copied.** "
                     f"Licence: {lic['spdx']} ({lic['verdict']}). Nothing from it is in this folder.")
        lines += ["", "Install the original and keep it installed:", "",
                  "```bash", f"npx skills add {src['source']}", f"gh skill install {src['source']}", "```", "",
                  f"Its own description (the author's words, not checked): {_q(_one_line(src.get('description'), 400))}"]
    lines += ["", "## Read and scanned", "",
              f"- {src['files_read']} files, {src['bytes_read']:,} bytes, read in full (every byte, secondary files included).",
              f"- Scanner: {src['scan']['summary']['block']} blocking, {src['scan']['summary']['review']} to review, "
              f"{src['scan']['summary']['info']} informational."]
    if src["scan"].get("network_files"):
        lines.append("- Scripts that make network calls: " + ", ".join(f"`{p}`" for p in src["scan"]["network_files"]) +
                     (". None of them is kept." if not any(f["keep"] for f in src["files"] if f["path"] in src["scan"]["network_files"]) else "."))
    else:
        lines.append("- No script makes network calls.")
    reviewed = [f for f in src["scan"]["findings"] if f["severity"] == "review"]
    if reviewed:
        lines.append(f"- Flagged for review ({len(reviewed)}), with what was done:")
        kept_paths = {f["path"] for f in src["files"] if f["keep"]}
        for f in reviewed[:25]:
            fate = "kept" if f["file"] in kept_paths else "left out"
            lines.append(f"  - `{f['file']}:{f['line']}` {f['label']} ({fate})")
        if len(reviewed) > 25:
            lines.append(f"  - and {len(reviewed) - 25} more in MERGE.md")
    if src["mode"] != "flatten":
        return "\n".join(lines) + "\n"
    kept = [f for f in src["files"] if f["keep"]]
    dropped = [f for f in src["files"] if not f["keep"]]
    lines += ["", "## What is here", ""]
    renamed = renamed_skill_file(src["alias"])
    if any(f["path"] == "SKILL.md" for f in kept):
        lines.append(f"- `{renamed}`: the original SKILL.md, unchanged, renamed so agents never load it as a second skill. "
                     "Its own file references still hold relative to this folder.")
    if any(f["path"] == "README.md" for f in kept):
        lines.append("- `SOURCE-README.md`: the source's own README, unchanged (this file is the compiler's).")
    for d, shown, n in _dir_summary([f["path"] for f in kept if f["path"] != "SKILL.md"], limit=14):
        lines.append(f"- `{d or '.'}/` ({n}): {shown}")
    inline = [s for s in src["sections"] if s["action"] == "inline"]
    if inline:
        lines += ["", "Inline in `../SKILL.md`: " + ", ".join(f"\"{_q(s['title'])}\"" for s in inline) + "."]
    changed = [s for s in inline if s.get("modifications")]
    if changed:
        lines += ["", "## Changes made", ""]
        for s in changed:
            lines.append(f"- \"{_q(s['title'])}\" (lines {s['lines'][0]} to {s['lines'][1]} of the original): " + "; ".join(s["modifications"]) + ".")
        if lic["spdx"] in NOTICE_LICENCES:
            lines.append(f"- These are the changes {lic['spdx']} asks to be stated. The files in this folder are unchanged.")
    lines += ["", "## Left out, and why", ""]
    if not dropped:
        lines.append("- Nothing.")
    reasons = {}
    for f in dropped:
        reasons.setdefault(f["why"], []).append(f["path"])
    for why, paths in sorted(reasons.items(), key=lambda x: -len(x[1])):
        shown = ", ".join(f"`{p}`" for p in paths[:8]) + (f" and {len(paths) - 8} more" if len(paths) > 8 else "")
        lines.append(f"- {shown}: {why}.")
    for s in src["sections"]:
        if s["action"] == "drop":
            lines.append(f"- Section \"{_q(s['title'])}\" of SKILL.md: {s['why']}.")
    lines += ["", "## Licence duties", "", f"- {lic['duties']}"]
    if lic["spdx"] == "CC-BY-4.0" or "CC-BY-4.0" in (lic.get("all") or []):
        owner = src["source"].split("/")[0] if src["sourceType"] == "github" else src["source"]
        lines.append(f"- Credit: {', '.join(lic.get('copyright') or []) or owner}, {src.get('sourceUrl') or src['source']}. "
                     "Licence: https://creativecommons.org/licenses/by/4.0/. Changes: listed under \"Changes made\" above, or none.")
    if lic.get("notice"):
        lines.append("- The source's NOTICE file is carried in `NOTICE`.")
    for p in lic.get("problems") or []:
        lines.append(f"- Note: {p}.")
    lines += ["", "## Updating", "",
              f"Run the `update-skills` skill on `../`: it diffs {src['source']} against commit {short}, re-reads every changed file, "
              "re-runs the eval and asks before replacing anything."]
    return "\n".join(lines) + "\n"


# ------------------------------------------------------------------ MERGE.md
def merge_md(plan, compare=None, checks=None, scoreboard=None):
    L = [f"# MERGE.md: how `{plan['name']}` was made", ""]
    L.append(f"Mode: `{plan['mode']}`. Job: {plan.get('job') or '(none given)'}" + (f" Gap: {plan['gap']}." if plan.get("gap") else ""))
    L += ["", "## Sources", "", "| Source | Commit | Licence | Use | Read | Scan (block / review / info) |", "| --- | --- | --- | --- | --- | --- |"]
    for s in plan["sources"]:
        sm = s["scan"]["summary"]
        use = {"flatten": "copied", "reference": "named only", "excluded": "**excluded**"}[s["mode"]]
        L.append(f"| `{s['alias']}` {s['source']} | {(s.get('ref') or '')[:7]} | {s['licence']['spdx']} ({s['licence']['verdict']}) | {use} | "
                 f"{s['files_read']} files, {s['bytes_read']:,} B | {sm['block']} / {sm['review']} / {sm['info']} |")
    excluded = [s for s in plan["sources"] if s["mode"] == "excluded"]
    refd = [s for s in plan["sources"] if s["mode"] == "reference"]
    if excluded:
        L += ["", "## Excluded", ""]
        for s in excluded:
            L.append(f"- `{s['alias']}` ({s['source']} @ {(s.get('ref') or '')[:7]}): {s['excluded_reason']}.")
            for f in [x for x in s["scan"]["findings"] if x["severity"] == "block"][:6]:
                # the offending text itself is never repeated into an emitted file
                L.append(f"  - `{f['file']}:{f['line']}` {f['label']} (finding `{f['id']}`; the line is in the staged copy, not here)")
            if any(f["rule"].startswith("promo") for f in s["scan"]["findings"] if f["severity"] == "block"):
                L.append("  - To use the rest of it, re-run with `--strip <finding>`: the section or file is cut and the cut is recorded here.")
    if refd:
        L += ["", "## Named, not copied", ""]
        for s in refd:
            L.append(f"- `{s['alias']}` ({s['source']}): {s['excluded_reason'] or 'orchestrated by reference'}. The compiled SKILL.md names it; its README says how to install it.")
    L += ["", "## What wins, top first", ""] + [f"{i}. {r}" for i, r in enumerate(plan["precedence"], 1)]
    conf = plan.get("conflicts", [])
    live = [c for c in conf if c.get("status") != "dismissed"]
    dismissed = [c for c in conf if c.get("status") == "dismissed"]
    L += ["", f"## Conflicts ({len(live)} settled, {len(dismissed)} dismissed as not a conflict)", ""]
    if not conf:
        L.append("None found. The scan for conflicts compares every pair of rules across sources for opposite advice or different numbers on the same topic.")
    else:
        L += ["| # | Topic | Says | Says | Winner | Why |", "| --- | --- | --- | --- | --- | --- |"]
        for c in live:
            a, b = c["sides"]
            L.append(f"| {c['id']} | {c['topic']} | `{a['source']}`: {_cell(a['text'])} | `{b['source']}`: {_cell(b['text'])} | "
                     f"`{c['winner']}` | {_cell(c['why'])}{' (agent confirmed)' if c.get('status') == 'confirmed' else ''} |")
        if dismissed:
            L += ["", "Dismissed:", ""]
            for c in dismissed:
                L.append(f"- {c['id']} ({c['topic']}): {_cell(c.get('why') or 'not a conflict')}")
    dups = [d for d in plan.get("duplicates", []) if d.get("status") != "dismissed"]
    L += ["", f"## Duplicates folded: one copy per rule ({len(dups)})", ""]
    if not dups:
        L.append("None found.")
    for d in dups:
        L.append(f"- {d['id']}: kept `{d['kept']['source']}` \"{_cell(d['kept']['text'], 90)}\"; dropped `{d['dropped']['source']}`'s copy. {d['why']}.")
    L += ["", "## Sections", "", "| Source | Section | Lines | Tokens | Score | Use | Why |", "| --- | --- | --- | --- | --- | --- | --- |"]
    for s in plan["sources"]:
        for x in s["sections"]:
            L.append(f"| `{s['alias']}` | {_cell(x['title'], 50)} | {x['lines'][0]} to {x['lines'][1]} | {x['tokens']} | {x.get('score', '')} | "
                     f"{x['action']} | {_cell(x.get('why', ''), 90)} |")
    for ex in plan.get("extra_sections", []):
        L.append(f"| compiler | {_cell(ex['title'], 50)} | | {estimate_tokens(ex['text'])} | | inline | {_cell(ex.get('why', 'written for this merge'), 90)} |")
    L += ["", "## Files left out", ""]
    any_left = False
    for s in plan["sources"]:
        if s["mode"] != "flatten":
            continue
        left = [f for f in s["files"] if not f["keep"]]
        if left:
            any_left = True
            L.append(f"- `{s['alias']}`: " + "; ".join(f"`{f['path']}` ({f['why']})" for f in left[:30]) +
                     (f"; and {len(left) - 30} more, listed in `{s['alias']}/README.md`" if len(left) > 30 else ""))
    if not any_left:
        L.append("- None.")
    review = [(s["alias"], f) for s in plan["sources"] for f in s["scan"]["findings"] if f["severity"] == "review"]
    if review:
        L += ["", f"## Flagged for review ({len(review)})", ""]
        for alias, f in review[:60]:
            L.append(f"- `{alias}/{f['file']}:{f['line']}` {f['label']}")
    if plan.get("notes"):
        L += ["", "## Notes from the compiler", ""] + [f"- {n}" for n in plan["notes"]]
    if compare:
        L += ["", f"## Against `{compare['path']}`", ""] + compare["lines"]
    if checks:
        L += ["", "## Checks", ""] + [f"- {'PASS' if c['ok'] else 'FAIL'} {c['name']}: {c['detail']}" for c in checks]
    if scoreboard:
        L += ["", "## Eval", ""] + scoreboard
    L.append("")
    return "\n".join(L)


QUOTE_MASK = re.compile(r"\?ref=\S*|utm_[a-z]+=\S*|sign-?off|made by .{0,40}who also makes|who also makes|end (the|your|every) reply with|once per conversation", re.I)


def quote_safe(text):
    """Quoted source text in MERGE.md never carries a promotional phrase into the compiled skill."""
    return QUOTE_MASK.sub("[promotional text, see source]", text)


_STYLE = {"plain_dashes": False}


def _q(text):
    """Source text quoted in a file the compiler writes: house style applies to it when asked."""
    return plain_dashes(text) if _STYLE["plain_dashes"] else text


def _cell(text, n=140):
    t = _q(quote_safe(re.sub(r"\s+", " ", str(text or "")).replace("|", "/").strip()))
    return t if len(t) <= n else t[: n - 3].rsplit(" ", 1)[0] + "..."


# ------------------------------------------------------------------ comparison with a hand-made skill
def compare_with(plan, out_dir, ref_dir):
    ref_dir = os.path.expanduser(ref_dir)
    lines = []
    ref_md = os.path.join(ref_dir, "SKILL.md")
    if not os.path.isfile(ref_md):
        return {"path": ref_dir, "lines": ["No SKILL.md there to compare."]}
    from .util import iter_files
    from .util import sha256_file
    ref_files = {rel for rel, _ in iter_files(ref_dir)}
    out_files = {rel for rel, _ in iter_files(out_dir)}
    only_ref = sorted(ref_files - out_files)
    only_out = sorted(out_files - ref_files - {"MERGE.md", LOCK_NAME} - {p for p in out_files if p.startswith("evals/")})
    ref_hash = {sha256_file(os.path.join(ref_dir, p)): p for p in only_ref}
    renamed_pairs = []
    for p in list(only_out):
        h = sha256_file(os.path.join(out_dir, p))
        if h in ref_hash:
            renamed_pairs.append((ref_hash[h], p))
            only_out.remove(p)
            only_ref.remove(ref_hash[h])
    lines.append(f"Files: {len(ref_files & out_files)} in both, {len(only_ref)} only in the hand-made skill, {len(only_out)} only here.")
    notes = plan.get("compare_notes", {})
    for a, b in renamed_pairs:
        lines.append(f"- Same file, another name: `{a}` there is `{b}` here.")
    if only_ref:
        lines += ["", "Only in the hand-made skill:", ""]
        for d, shown, n in _dir_summary(only_ref, limit=12):
            why = notes.get(d) or _why_only_ref(d, plan)
            lines.append(f"- `{d or '.'}/` ({n}): {shown}. {why}")
    if only_out:
        lines += ["", "Only here:", ""]
        for d, shown, n in _dir_summary(only_out, limit=12):
            why = notes.get(d) or _why_only_out(d, plan)
            lines.append(f"- `{d or '.'}/` ({n}): {shown}. {why}")
    # SKILL.md sections
    _, ref_body = split_frontmatter(open(ref_md, encoding="utf-8").read())
    _, out_body = split_frontmatter(open(os.path.join(out_dir, "SKILL.md"), encoding="utf-8").read())
    ref_secs = [s for s in parse_sections(ref_body) if s["level"] in (1, 2)]
    out_secs = [s for s in parse_sections(out_body) if s["level"] in (1, 2, 3)]
    src_secs = [x for s in plan["sources"] for x in s["sections"]]
    lines += ["", "SKILL.md, section by section (hand-made heading, closest heading here, word overlap):", ""]
    lines += ["| Hand-made | Here | Overlap | Reading |", "| --- | --- | --- | --- |"]
    for rs in ref_secs:
        rw = set(content_words(rs["text"]))
        best, score = None, 0.0
        for os_ in out_secs:
            ow = set(content_words(os_["text"]))
            j = len(rw & ow) / max(1, len(rw | ow))
            if j > score:
                best, score = os_, j
        src_best = max((len(rw & set(content_words(x["text"]))) / max(1, len(rw | set(content_words(x["text"])))) for x in src_secs), default=0)
        if score >= 0.6:
            reading = "same text"
        elif score >= 0.3:
            reading = "same topic, worded differently"
        elif src_best >= 0.3:
            reading = "in a source but not inline here: it is in the source folder"
        else:
            reading = "written by hand for the merge; no source has it. Add it as an extra section if it should be here"
        note = notes.get(rs["title"])
        lines.append(f"| {_cell(rs['title'], 50)} | {_cell(best['title'] if best else '', 50)} | {score:.2f} | {note or reading} |")
    ref_lines = ref_body.count("\n")
    lines += ["", f"Size: the hand-made SKILL.md body is {ref_lines} lines and about {estimate_tokens(ref_body)} tokens; "
              f"this one is {out_body.count(chr(10))} lines and about {estimate_tokens(out_body)} tokens."]
    return {"path": ref_dir.replace(os.path.expanduser("~"), "~", 1), "lines": lines}


def _why_only_ref(d, plan):
    if d.startswith("scripts"):
        return "Hand-written glue for the hand-made merge (not in any source)."
    for s in plan["sources"]:
        if d == s["alias"] or d.startswith(s["alias"] + "/"):
            return "Left out here by the file rules or the plan; see that source's README."
    return "Not in any source."


def _why_only_out(d, plan):
    for s in plan["sources"]:
        if s.get("section_selector") and d == s["alias"]:
            return ("The hand-made skill keeps this text inline in its SKILL.md; here the selected section gets its own "
                    "folder so its origin is recorded, and the parts that do not fit the budget are read from there.")
        if d == s["alias"] or d.startswith(s["alias"] + "/"):
            return "Kept here by the default file rules; the hand-made merge cut it by judgement. Set `keep: false` in the plan to match."
    return "Written by the compiler."


# ------------------------------------------------------------------ write the folder
def write_folder(plan, out_dir):
    _STYLE["plain_dashes"] = bool(plan["options"].get("plain_dashes"))
    if os.path.exists(out_dir):
        shutil.rmtree(out_dir)
    os.makedirs(out_dir)
    for src in plan["sources"]:
        if src["mode"] == "excluded":
            continue
        dest = os.path.join(out_dir, src["alias"])
        os.makedirs(dest, exist_ok=True)
        if src["mode"] == "flatten":
            for f in src["files"]:
                if not f["keep"]:
                    continue
                rel = f["path"]
                main = os.path.basename(src.get("skillPath") or "SKILL.md")
                if src.get("section_selector") and rel == main:
                    # a section source: carry exactly the selected text, nothing else from that file
                    write_text(os.path.join(dest, renamed_skill_file(src["alias"])),
                               "".join(x["text"] for x in src["sections"]))
                    continue
                target_rel = vendored_name(src["alias"], rel)
                target = os.path.join(dest, target_rel)
                os.makedirs(os.path.dirname(target), exist_ok=True)
                shutil.copyfile(os.path.join(src["staging"], rel), target)
            lic = src["licence"]
            lic_files = lic.get("files") or ([lic["file"]] if lic.get("file") else [])
            for i, lf in enumerate(lic_files):
                name = "LICENSE" if i == 0 else os.path.basename(lf)
                shutil.copyfile(os.path.join(src["repo_root"], lf), os.path.join(dest, name))
            if lic.get("notice"):
                write_text(os.path.join(dest, "NOTICE"), lic["notice"].rstrip() + "\n")
    skill_md = compose_skill_md(plan)
    write_text(os.path.join(out_dir, "SKILL.md"), skill_md)
    for src in plan["sources"]:
        if src["mode"] != "excluded":
            write_text(os.path.join(out_dir, src["alias"], "README.md"), source_readme(plan, src))
    return skill_md
