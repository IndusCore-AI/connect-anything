"""Decisions: the agent's judgement, kept apart from the generated plan so it survives a re-plan.

plan.json is regenerated whenever a source moves; decisions.json is what the agent decided after reading,
matched to the plan by stable keys (source alias + section id, source alias + file path, conflict key).
The build applies it, and the lockfile carries it, so `update` re-applies the same judgement to new commits.

{
  "title": "...", "description": "...", "intro": "...", "precedence": ["...", ...],
  "order": ["extra:how-to-use", "hallmark:the-floor", ...],
  "sections": {"<alias>:<section id>": {"action": "inline|reference|drop", "why": "..."}},
  "files": {"<alias>:<path>": {"keep": false, "why": "..."}},
  "conflicts": {"<key>": {"status": "confirmed|dismissed", "winner": "<alias>", "why": "..."}},
  "duplicates": {"<key>": {"status": "dismissed", "why": "..."}},
  "extra_sections": [{"id": "how-to-use", "title": "...", "text": "...", "why": "..."}],
  "overrides": {"<alias>:<section id>": "overrides/<file>.md"},
  "compare_notes": {"<heading or folder>": "..."},
  "options": {"plain_dashes": true}, "notes": ["..."]
}
"""
from .util import EngineError

SCALARS = ("title", "description", "intro", "precedence", "order", "extra_sections", "overrides", "compare_notes", "notes")


def apply(plan, dec):
    """Apply decisions to a plan in place. Returns keys that matched nothing (the source moved or the id changed)."""
    if not dec:
        return []
    unmatched = []
    for k in SCALARS:
        if k in dec:
            plan[k] = dec[k]
    plan["options"].update(dec.get("options") or {})
    by_alias = {s["alias"]: s for s in plan["sources"]}
    for key, d in (dec.get("sections") or {}).items():
        alias, _, sid = key.partition(":")
        sec = next((x for x in by_alias.get(alias, {}).get("sections", []) if x["id"] == sid), None)
        if sec is None:
            unmatched.append(f"section {key}")
            continue
        if d.get("action") not in ("inline", "reference", "drop"):
            raise EngineError(f"decisions: section {key} has action {d.get('action')!r}; use inline, reference or drop")
        if by_alias[alias]["mode"] != "flatten" and d["action"] == "inline":
            raise EngineError(f"decisions: {key} cannot be inline; {alias} is {by_alias[alias]['mode']} ({by_alias[alias].get('excluded_reason')})")
        sec["action"], sec["why"] = d["action"], d.get("why") or "the compiler's decision"
        sec["decided"] = True
    for key, d in (dec.get("files") or {}).items():
        alias, _, path = key.partition(":")
        f = next((x for x in by_alias.get(alias, {}).get("files", []) if x["path"] == path), None)
        if f is None:
            unmatched.append(f"file {key}")
            continue
        if d.get("keep") and by_alias[alias]["mode"] != "flatten":
            raise EngineError(f"decisions: cannot keep {key}; {alias} is not copied ({by_alias[alias].get('excluded_reason')})")
        f["keep"], f["why"] = bool(d.get("keep")), d.get("why") or "the compiler's decision"
        f["decided"] = True
    for kind in ("conflicts", "duplicates"):
        items = {x["key"]: x for x in plan.get(kind, [])}
        for key, d in (dec.get(kind) or {}).items():
            item = items.get(key) or next((x for x in plan.get(kind, []) if x["id"] == key), None)
            if item is None:
                unmatched.append(f"{kind[:-1]} {key}")
                continue
            if d.get("winner"):
                sides = {s["source"] for s in item.get("sides", [])} if kind == "conflicts" else set()
                if kind == "conflicts" and d["winner"] not in sides:
                    raise EngineError(f"decisions: conflict {key} winner {d['winner']!r} is not one of {sorted(sides)}")
                item["winner"] = d["winner"]
            item["status"] = d.get("status", "confirmed")
            if d.get("why"):
                item["why"] = d["why"]
    plan["decisions_applied"] = True
    return unmatched
