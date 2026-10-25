"""Choose step: score every section and file against the job and the profile, find duplicates and conflicts,
and write a plan the agent edits. The engine proposes; the agent decides and writes down why.

A profile is skill-radar's profile.json (interests, negatives) plus optional keys:
  job        one sentence: what the compiled skill is for
  must       rules in the user's own words that win every conflict
  sources    source aliases in rank order (who wins a tie)
  budget     {"lines": 450, "tokens": 4500} for the compiled SKILL.md
  gap        what the update run should fill (update mode)
"""
import math
import os
import re
from collections import Counter

from .util import content_words, estimate_tokens, folder_hash, sha256_bytes, read_json

DEFAULT_BUDGET = {"lines": 450, "tokens": 4500}
CHECK_SCRIPT_RE = re.compile(r"(check|lint|validat|verify|audit|sloplint|test)[^/]*\.(m?js|py|sh|ts)$", re.I)
TRIGGER_TITLE_RE = re.compile(r"^\W*(when to (use|apply|trigger|invoke)( this skill)?|triggers?|usage triggers|overview|about|introduction)\b", re.I)
REPO_DOCS = re.compile(r"(^|/)(README|CHANGELOG|CONTRIBUTING|CODE_OF_CONDUCT|SECURITY|HISTORY|AUTHORS|ROADMAP)(\.[a-z]{2})?\.(md|markdown|txt)$", re.I)
DROP_FILE_RULES = [
    (re.compile(r"(^|/)(tests?|__tests__|fixtures|spec)/|(^|/)test_[^/]+\.py$|_test\.[a-z]+$|\.test\.[a-z]+$|\.spec\.[a-z]+$"), "test code, not needed to use the skill"),
    (re.compile(r"(^|/)\.github/"), "repository CI, not part of the skill"),
    (re.compile(r"(^|/)(package-lock\.json|pnpm-lock\.yaml|yarn\.lock|bun\.lockb|uv\.lock|poetry\.lock)$"), "lockfile for the source's own tooling"),
    (re.compile(r"(^|/)(install|setup|uninstall)[^/]*\.(sh|mjs|js|py|ps1)$|(^|/)[^/]*hook[^/]*\.(sh|mjs|js|py)$"), "installer or hook; the compiled skill is installed as a whole and changes no agent settings"),
    (re.compile(r"(^|/)evals?/"), "the source's eval files feed the eval gate instead of being copied"),
]


def load_profile(path):
    if not path:
        return {}
    prof = read_json(path)
    return prof if isinstance(prof, dict) else {}


def _terms(table):
    out = []
    for kw, w in (table or {}).items():
        prefix = kw.endswith("*")
        base = kw[:-1] if prefix else kw
        if re.search(r"[^\x00-\x7f]", base):
            pat = re.compile(re.escape(base.lower()))
        else:
            pat = re.compile(r"(?<![a-z0-9])" + re.escape(base.lower()) + ("" if prefix else r"(?![a-z0-9])"))
        out.append((kw, float(w), pat))
    return out


class Scorer:
    """BM25 over all sections for the job (and gap) text, plus the profile's interest and negative weights."""

    def __init__(self, docs, job="", gap="", profile=None):
        self.docs = docs
        self.tok = [[stem(w) for w in content_words(d)] for d in docs]
        self.N = max(1, len(docs))
        self.avg = sum(len(t) for t in self.tok) / self.N if self.tok else 1
        df = Counter()
        for t in self.tok:
            df.update(set(t))
        self.idf = {w: math.log(1 + (self.N - n + 0.5) / (n + 0.5)) for w, n in df.items()}
        self.job = [stem(w) for w in content_words(job)]
        self.gap = [stem(w) for w in content_words(gap)]
        profile = profile or {}
        self.interests = _terms(profile.get("interests"))
        self.negatives = _terms(profile.get("negatives"))

    def bm25(self, query, i, k1=1.4, b=0.75):
        if not query:
            return 0.0
        tf = Counter(self.tok[i])
        dl = len(self.tok[i]) or 1
        s = 0.0
        for q in set(query):
            if q in tf:
                f = tf[q]
                s += self.idf.get(q, 0) * f * (k1 + 1) / (f + k1 * (1 - b + b * dl / self.avg))
        return s

    def score_all(self):
        job = [self.bm25(self.job, i) for i in range(len(self.docs))]
        gap = [self.bm25(self.gap, i) for i in range(len(self.docs))]
        jmax, gmax = max(job + [1e-9]), max(gap + [1e-9])
        out = []
        for i, d in enumerate(self.docs):
            low = d.lower()
            hits = [(kw, w) for kw, w, p in self.interests if p.search(low)]
            negs = [(kw, w) for kw, w, p in self.negatives if p.search(low)]
            interest = min(10.0, sum(w for _, w in hits)) / 10.0
            negative = min(10.0, sum(abs(w) for _, w in negs)) / 10.0
            s = 0.6 * job[i] / jmax + 0.4 * interest - 0.5 * negative
            if self.gap:
                s = 0.5 * s + 0.5 * gap[i] / gmax
            out.append({"score": round(s, 3), "job": round(job[i] / jmax, 3), "gap": round(gap[i] / gmax, 3) if self.gap else None,
                        "hits": [k.rstrip("*") for k, _ in hits][:8], "negatives": [k.rstrip("*") for k, _ in negs][:4]})
        return out


def file_disposition(f, findings_by_file, verdict):
    """Default keep or drop for one file, with the reason."""
    if verdict != "flatten":
        return False, "source is referenced, not copied"
    path = f["path"]
    if f["kind"] in ("binary-exec", "archive", "symlink"):
        return False, f"{f['kind']} file; nothing unreadable is copied"
    if path == "SKILL.md":
        return True, "the source's own SKILL.md, renamed so loaders never see a second skill"
    for rx, why in DROP_FILE_RULES:
        if rx.search(path):
            return False, why
    rules = {x["rule"] for x in findings_by_file.get(path, [])}
    if "network" in rules and "api-key-ref" in rules:
        return False, "calls an external service that needs an API key"
    if "agent-config" in rules and f["kind"] == "script":
        return False, "script that writes agent settings"
    return True, "kept as published"


def has_check_script(rec):
    return any(CHECK_SCRIPT_RE.search(f["path"]) and f["kind"] == "script" and not re.search(r"(^|/)tests?/", f["path"])
               for f in rec["files"])


# ------------------------------------------------------------------ rules, duplicates, conflicts
RULE_LINE = re.compile(r"^\s*(?:[-*+]|\d+[.)])\s+(.*\S)\s*$")
NEG = re.compile(r"\b(never|don'?t|do not|avoid|no|not|ban(?:ned)?|forbid(?:den)?|without|refuse[sd]?|stop)\b", re.I)
POS = re.compile(r"\b(always|use|prefer|must|should|keep|allowed|add|start|default)\b", re.I)
NUM = re.compile(r"(\d+(?:\.\d+)?)\s?(px|ms|%|s\b|sec|em|rem|lines?|chars?|characters|tokens|words|pt|dp)", re.I)


NEG_CONTEXT = re.compile(r"\b(avoid|cut|never|don'?t|do not|anti-?patterns?|mistakes?|smells?|tells?|red flags?|banned|forbidden|refuse|not allowed|pitfalls?|bad)\b", re.I)


def rules_of(text, with_context=False):
    """Bullets and numbered items as candidate rules. With with_context, each also says whether the list sits
    under a heading or lead-in that forbids its items ("Common mistakes", "Cut these:")."""
    out = []
    in_code = False
    ctx_neg = False
    for i, line in enumerate(text.splitlines()):
        s = line.strip()
        if s.startswith(("```", "~~~")):
            in_code = not in_code
            continue
        if in_code:
            continue
        m = RULE_LINE.match(line)
        if m:
            out.append((i, m.group(1), ctx_neg) if with_context else (i, m.group(1)))
        elif s:
            if s.startswith("#") or s.endswith(":") or len(s) < 120:
                ctx_neg = bool(NEG_CONTEXT.search(s)) and (s.startswith("#") or s.endswith(":"))
            else:
                ctx_neg = False
    return out


def _jaccard(a, b):
    a, b = set(a), set(b)
    return len(a & b) / max(1, len(a | b))


def stem(w):
    for suf in ("ations", "ation", "ings", "ing", "edly", "ed", "ies", "es", "ly", "s"):
        if len(w) > len(suf) + 3 and w.endswith(suf):
            return w[: -len(suf)] + ("y" if suf == "ies" else "")
    return w


def _rule_index(units):
    """Rules from units [(alias, section, text, rank)] with stems, document frequency and idf."""
    rules = []
    for alias, sec_id, text, rank in units:
        for _, r, neg in rules_of(text, with_context=True):
            cw = content_words(r)
            if len(cw) >= 3:
                rules.append({"source": alias, "section": sec_id, "text": r, "stems": {stem(w) for w in cw}, "rank": rank,
                              "n": len(cw), "list_forbids": neg})
    df = Counter()
    for r in rules:
        df.update(r["stems"])
    n = max(1, len(rules))
    idf = {t: math.log(1 + n / c) for t, c in df.items()}
    inv = {}
    for i, r in enumerate(rules):
        for t in r["stems"]:
            inv.setdefault(t, []).append(i)
    return rules, df, idf, inv


def _pairs(rules, df, inv, max_df):
    """Cross-source rule pairs that share at least one specific (rare) term."""
    seen = set()
    for t, idxs in inv.items():
        if df[t] > max_df or len(idxs) < 2:
            continue
        for x in range(len(idxs)):
            for y in range(x + 1, len(idxs)):
                i, j = idxs[x], idxs[y]
                if rules[i]["source"] != rules[j]["source"] and (i, j) not in seen:
                    seen.add((i, j))
                    yield i, j


def _wsim(a, b, idf):
    shared = a["stems"] & b["stems"]
    union = a["stems"] | b["stems"]
    return sum(idf[t] for t in shared) / max(1e-9, sum(idf[t] for t in union)), shared


def find_duplicates(units):
    """Rules that say the same thing in two sources (idf-weighted overlap of their terms)."""
    rules, df, idf, inv = _rule_index(units)
    max_df = max(3, len(rules) // 25)
    dups = []
    for i, j in _pairs(rules, df, inv, max_df):
        a, b = rules[i], rules[j]
        if min(a["n"], b["n"]) < 5:
            continue
        sim, _ = _wsim(a, b, idf)
        if sim >= 0.55:
            dups.append({"a": (a["source"], a["section"], 0, a["text"], a["stems"], a["rank"]),
                         "b": (b["source"], b["section"], 0, b["text"], b["stems"], b["rank"]), "similarity": round(sim, 2)})
    dups.sort(key=lambda d: -d["similarity"])
    seen, unique = set(), []
    for d in dups:
        pk = pair_key(d["a"][3], d["b"][3])
        if pk not in seen:
            seen.add(pk)
            unique.append(d)
    return unique[:60]


GENERIC = {stem(w) for w in """give make take read build show need decide other ask asks move change keep let set put get
look feel thing things way part page pages user users people time first one two three every each same real right full
small large good best better work works start end line lines text content element elements item items value values
case cases point points place step steps state states style styles kind sort level type types just only even much
many less more most own new old high low top bottom left right side""".split()}


PROHIBIT = re.compile(r"\b(never|no|don'?t|do not|avoid|ban(?:ned|s)?|forbid(?:den|s)?|refuse[sd]?|not|cut|drop|remove|strip|delete|skip)\b", re.I)
ASK = re.compile(r"\b(use|uses|prefer|always|keep|add|include|write|start|default|choose|pick|want|wants|should|must|recommend(?:ed)?|ok|allowed)\b", re.I)


def _prohibited(text):
    """Stems a rule forbids: the content words after never / no / don't / avoid, to the end of that clause
    (a comma list such as "never a gradient, a card in a card, an emoji as an icon" forbids all of them)."""
    toks = re.findall(r"[A-Za-z0-9][A-Za-z0-9'_-]*|[.;:()]", text)
    out = set()
    i = 0
    while i < len(toks):
        if PROHIBIT.fullmatch(toks[i]):
            j = i + 1
            while j < len(toks) and toks[j] in (":", "("):  # "Banned: a, b, c"
                j += 1
            while j < len(toks) and j - i <= 25:
                lw = toks[j].lower()
                if lw in (".", ";", ":", "(", ")") or lw in ("but", "unless", "except", "instead", "when", "if"):
                    break
                if lw in ("use", "prefer") and j > i + 1:  # "never X, use Y" stops here; "never use X" forbids X
                    break
                cw = content_words(lw)
                if cw:
                    out.add(stem(cw[0]))
                j += 1
            i = j
        else:
            i += 1
    return out


def _asked(text):
    """Stems a rule asks for: content words within six words after use / prefer / keep / by default..."""
    toks = re.findall(r"[A-Za-z0-9][A-Za-z0-9'_-]*|[.;:()]", text)
    out = set()
    for i, t in enumerate(toks):
        if ASK.fullmatch(t):
            for w in toks[i + 1:i + 7]:
                if w in (".", ";") or PROHIBIT.fullmatch(w):
                    break
                cw = content_words(w.lower())
                if cw:
                    out.add(stem(cw[0]))
    return out


def find_conflicts(units, limit=25):
    """Rules from different sources where one forbids a specific term the other recommends, or where both
    give a number in the same unit for the same thing and the numbers differ."""
    rules, df, idf, inv = _rule_index(units)
    for r in rules:
        r["forbids"] = set(r["stems"]) if r.get("list_forbids") else _prohibited(r["text"])
        r["asks"] = set() if r.get("list_forbids") else (_asked(r["text"]) - r["forbids"])
    max_df = max(4, len(rules) // 40)
    found = []
    for i, j in _pairs(rules, df, inv, max_df):
        a, b = rules[i], rules[j]
        sim, shared = _wsim(a, b, idf)
        if sim >= 0.55:
            continue  # the same rule twice is a duplicate, not a conflict
        kind, terms = None, []
        clash = (a["forbids"] & b["asks"]) | (b["forbids"] & a["asks"])
        clash = {t for t in clash if df[t] <= max_df and len(t) > 3 and t not in GENERIC}
        specific_shared = {t for t in shared if df[t] <= max_df and t not in GENERIC}
        if clash and len(specific_shared) >= 2:
            kind, terms = "polarity", sorted(clash, key=lambda t: -idf[t])
        else:
            nums_a = {(u.lower().rstrip("s"), v) for v, u in NUM.findall(a["text"])}
            nums_b = {(u.lower().rstrip("s"), v) for v, u in NUM.findall(b["text"])}
            specific = [t for t in shared if df[t] <= max(3, max_df // 2) and t not in GENERIC]
            if len(specific) >= 2 and {u for u, _ in nums_a} & {u for u, _ in nums_b} and not (nums_a & nums_b):
                kind, terms = "number", sorted(specific, key=lambda t: -idf[t])
        if kind:
            found.append({"kind": kind, "overlap": round(sim, 2), "shared": terms[:6], "weight": sum(idf[t] for t in terms) + sim,
                          "sides": [{"source": a["source"], "section": a["section"], "text": a["text"]},
                                    {"source": b["source"], "section": b["section"], "text": b["text"]}],
                          "ranks": (a["rank"], b["rank"])})
    found.sort(key=lambda c: (-c["weight"], -c["overlap"]))
    out, topics, seen = [], Counter(), set()
    for c in found:  # at most two conflicts per topic term, so one busy term cannot crowd out the rest
        pk = pair_key(c["sides"][0]["text"], c["sides"][1]["text"])
        if pk in seen:
            continue
        seen.add(pk)
        key = c["shared"][0]
        if topics[key] >= 2:
            continue
        topics[key] += 1
        out.append(c)
        if len(out) >= limit:
            break
    return out


def pair_key(a, b):
    """Stable id for a conflict or duplicate, so decisions survive a re-plan at a new commit."""
    import hashlib
    return hashlib.sha1("\n".join(sorted([a.strip(), b.strip()])).encode()).hexdigest()[:10]


def default_winner(conflict, recs_by_alias, must_rules):
    sides = conflict["sides"]
    for side in sides:
        for rule in must_rules:
            if _jaccard(content_words(rule), content_words(side["text"])) >= 0.3:
                return side["source"], f"matches your rule: {rule!r}"
    ra, rb = conflict["ranks"]
    if ra != rb:
        win = sides[0] if ra < rb else sides[1]
        return win["source"], "ranked higher in the source order you gave"
    checks = [has_check_script(recs_by_alias[s["source"]]) for s in sides]
    if checks[0] != checks[1]:
        win = sides[0] if checks[0] else sides[1]
        return win["source"], "ships a mechanical check for its rules"
    la, lb = len(content_words(sides[0]["text"])), len(content_words(sides[1]["text"]))
    win = sides[0] if la >= lb else sides[1]
    return win["source"], "the more specific rule"


# ------------------------------------------------------------------ plan
def default_precedence(profile, aliases, checkers):
    out = ["The user's own words in the conversation"]
    for rule in profile.get("must") or []:
        out.append(f"Your rule: {rule}")
    out.append("The project's locked system: its tokens, copy rules, i18n and checks (CLAUDE.md, design.md, config files)")
    out.append("Safety, licence and honesty rules from any source; a merge never weakens one")
    if aliases:
        ranked = ", then ".join(f"`{a}`" + (" (ships a check)" if a in checkers else "") for a in aliases)
        out.append(f"The sources in this order: {ranked}")
    out.append("A rule a mechanical check enforces beats one it does not")
    out.append("The more specific rule beats the general one")
    out.append("Taste")
    return out


def find_pairs(sources, recs, profile, rank=None):
    """Duplicates and conflicts across the copied sources: their SKILL.md sections and markdown references."""
    rank = rank or {s["alias"]: i for i, s in enumerate(sources)}
    by_alias = {s["alias"]: s for s in sources}
    flat_units = [(s["alias"], x) for s in sources if s["mode"] == "flatten" for x in s["sections"] if x["action"] != "drop"]
    # duplicates and conflicts over the inline candidates plus the next best
    cand = [(a, s["id"], s["text"], rank.get(a, 99)) for a, s in flat_units]
    for rec in recs:  # rules in the sources' reference files can clash with inline rules too
        if by_alias[rec["alias"]]["mode"] != "flatten":
            continue
        for f in rec["files"]:
            if f["kind"] == "markdown" and f["path"] != rec.get("main_file") and f.get("text") and f["size"] < 200_000 and not REPO_DOCS.search(f["path"]):
                cand.append((rec["alias"], f["path"], f["text"], rank.get(rec["alias"], 99)))
    dups = find_duplicates(cand)
    duplicates = []
    for n, d in enumerate(dups, 1):
        a, b = d["a"], d["b"]
        ca, cb = by_alias[a[0]]["check_script"], by_alias[b[0]]["check_script"]
        if ca != cb:
            keep, drop, why = (a, b, f"`{a[0]}` ships a check script") if ca else (b, a, f"`{b[0]}` ships a check script")
        elif a[5] != b[5]:
            keep, drop, why = (a, b, "higher in the source order") if a[5] < b[5] else (b, a, "higher in the source order")
        else:
            keep, drop, why = (a, b, "the longer, more specific wording") if len(a[4]) >= len(b[4]) else (b, a, "the longer, more specific wording")
        duplicates.append({"id": f"d{n}", "key": pair_key(keep[3], drop[3]), "similarity": d["similarity"], "why": why,
                           "kept": {"source": keep[0], "section": keep[1], "text": keep[3]},
                           "dropped": {"source": drop[0], "section": drop[1], "text": drop[3]}})
    conflicts = []
    must = profile.get("must") or []
    for n, c in enumerate(find_conflicts(cand), 1):
        win, why = default_winner(c, {s["alias"]: _rec_for(recs, s["alias"]) for s in sources}, must)
        conflicts.append({"id": f"c{n}", "key": pair_key(c["sides"][0]["text"], c["sides"][1]["text"]), "kind": c["kind"],
                          "topic": ", ".join(c["shared"][:4]), "sides": c["sides"], "winner": win, "why": why, "status": "proposed"})
    return duplicates, conflicts


def build_plan(mode, name, recs, assessments, scans, profile, job="", gap="", budget=None, extra=None, per_repo=None):
    """recs: read records; assessments: alias -> licence; scans: alias -> (findings, summary)."""
    budget = {**DEFAULT_BUDGET, **(profile.get("budget") or {}), **(budget or {})}
    ranked_aliases = profile.get("sources") or [r["alias"] for r in recs]
    rank = {a: i for i, a in enumerate(ranked_aliases)}
    sources, all_units = [], []
    for rec in recs:
        alias = rec["alias"]
        lic = assessments[alias]
        findings, summary = scans[alias]
        blocked = [f for f in findings if f["severity"] == "block" and not f.get("allowed")]
        excluded_by = None
        if blocked:
            mode_s, why = "excluded", f"scanner: {blocked[0]['label']} at {blocked[0]['file']}:{blocked[0]['line']}"
            excluded_by = "scanner"
        elif lic["verdict"] in ("flatten", "own"):
            mode_s, why = "flatten", None
        else:
            mode_s, why = "reference", f"licence {lic['spdx']}: {lic['verdict']}; never copied"
        by_file = {}
        for f in findings:
            by_file.setdefault(f["file"], []).append(f)
        files = []
        for f in rec["files"]:
            keep, fwhy = file_disposition(f, by_file, "flatten" if mode_s == "flatten" else "reference")
            flags = sorted({f"{x['severity']}:{x['rule']}" for x in by_file.get(f["path"], []) if x["severity"] != "info"})
            files.append({"path": f["path"], "kind": f["kind"], "size": f["size"], "sha256": f["sha256"],
                          "keep": keep and mode_s == "flatten", "why": fwhy, "flags": flags,
                          "network": any(x["rule"] == "network" for x in by_file.get(f["path"], []))})
        sections = []
        for s in rec["sections"]:
            sections.append({"id": s["id"], "file": s["file"], "title": s["title"], "level": s["level"],
                             "lines": [s["start"], s["end"]], "tokens": estimate_tokens(s["text"]),
                             "hash": sha256_bytes(s["text"].encode())[:16], "text": s["text"]})
            all_units.append((alias, s, mode_s))
        meta = rec["meta"]
        sources.append({
            "alias": alias, "spec": rec["spec"], "source": meta["source"], "sourceType": meta["sourceType"],
            "sourceUrl": meta.get("sourceUrl"), "ref": meta.get("sha") or meta.get("contentHash"),
            "date": meta.get("date"), "skillPath": (rec["skill_path"].rstrip("/") + "/" if rec["skill_path"] != "." else "") + (rec.get("main_file") or "SKILL.md"),
            "staging": rec["skill_root"], "repo_root": rec["root"], "section_selector": rec.get("section"),
            "computedHash": folder_hash(rec["skill_root"], exclude={".connect-anything-fetch.json"}),
            "licence": {k: v for k, v in lic.items() if k != "file_text"},
            "mode": mode_s, "excluded_reason": why, "excluded_by": excluded_by,
            "scan": {"summary": summary, "findings": [f for f in findings if f["severity"] != "info"],
                     "info": dict(Counter(f["rule"] for f in findings if f["severity"] == "info")),
                     "network_files": sorted({f["file"] for f in findings if f["rule"] == "network"})},
            "files_read": rec["files_read"], "bytes_read": rec["bytes_read"],
            "description": (rec.get("frontmatter") or {}).get("description", ""),
            "name": (rec.get("frontmatter") or {}).get("name", alias),
            "check_script": has_check_script(rec), "files": files, "sections": sections,
            "body_tokens": rec["body_tokens"],
        })
    # score
    docs = [u[1]["text"] for u in all_units]
    scores = Scorer(docs, job=job, gap=gap, profile=profile).score_all() if docs else []
    by_alias = {s["alias"]: s for s in sources}
    flat_units = []
    for (alias, s, mode_s), sc in zip(all_units, scores):
        sec = next(x for x in by_alias[alias]["sections"] if x["id"] == s["id"])
        sec.update(sc)
        if mode_s != "flatten":
            sec["action"], sec["why"] = ("drop", "source is not copied") if mode_s == "excluded" else ("reference", "named only; the original stays installed")
        elif TRIGGER_TITLE_RE.search(s["title"]) or s["title"] == "(preamble)" and sec["tokens"] < 120:
            sec["action"], sec["why"] = "drop", "trigger or intro text; the compiled description covers it"
        elif sc["negatives"] and sc["score"] < 0:
            sec["action"], sec["why"] = "drop", "matches your negatives: " + ", ".join(sc["negatives"])
        else:
            sec["action"], sec["why"] = "reference", "kept in the source folder"
            flat_units.append((alias, sec))
    # pack inline by score within budget
    overhead_lines, overhead_tokens = 40, 600
    lines_used, tokens_used = overhead_lines, overhead_tokens
    n_src = max(1, len(ranked_aliases))
    bonus = lambda a: 0.15 * (1 - rank.get(a, n_src) / n_src)  # the order you gave the sources counts a little
    repo_of = {s["alias"]: s["source"] for s in sources}
    per_repo_used = Counter()
    for alias, sec in sorted(flat_units, key=lambda x: (-(x[1]["score"] + bonus(x[0])), rank.get(x[0], 99))):
        n_lines = sec["lines"][1] - sec["lines"][0] + 1
        if sec["score"] <= 0.05:
            continue
        if per_repo and per_repo_used[repo_of[alias]] >= per_repo:
            sec["why"] = f"score {sec['score']}: kept in the source folder; {per_repo} sections from this repo are already inline"
            continue
        if lines_used + n_lines <= budget["lines"] and tokens_used + sec["tokens"] <= budget["tokens"]:
            sec["action"], sec["why"] = "inline", f"score {sec['score']}: fits the job" + (f" ({', '.join(sec['hits'][:4])})" if sec["hits"] else "")
            per_repo_used[repo_of[alias]] += 1
            lines_used += n_lines
            tokens_used += sec["tokens"]
        else:
            sec["why"] = f"score {sec['score']}: kept in the source folder; the SKILL.md budget is full"
    duplicates, conflicts = find_pairs(sources, recs, profile, rank)
    flat_aliases = [s["alias"] for s in sources if s["mode"] == "flatten"]
    plan = {
        "version": 1, "mode": mode, "name": name, "title": name.replace("-", " ").title(), "job": job, "gap": gap or None,
        "description": "", "intro": "", "budget": budget,
        "precedence": default_precedence(profile, [a for a in ranked_aliases if a in flat_aliases],
                                         {s["alias"] for s in sources if s["check_script"]}),
        "options": {"plain_dashes": False, "own_licence": None},
        "sources": sources, "duplicates": duplicates, "conflicts": conflicts,
        "overrides": {}, "extra_sections": [], "order": [], "notes": [],
        "profile": {k: profile[k] for k in ("job", "must", "sources", "gap") if k in profile},
    }
    if extra:
        plan.update(extra)
    plan["description"] = plan["description"] or draft_description(plan)
    return plan


def _rec_for(recs, alias):
    return next(r for r in recs if r["alias"] == alias)


def draft_description(plan):
    """A first description: the job, then what it merges. The agent tunes it with trigger phrases."""
    job = plan.get("job") or ""
    names = [s["name"] or s["alias"] for s in plan["sources"] if s["mode"] != "excluded"]
    text = (job.rstrip(".") + ". " if job else "") + "Combines " + ", ".join(names) + " into one skill with one trigger."
    return text[:1000]
