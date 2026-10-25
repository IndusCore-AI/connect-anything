"""Shared helpers: paths, safe subprocess calls, hashing, frontmatter and markdown parsing.

Standard library only. Nothing read from a fetched source is ever executed or imported.
"""
import hashlib
import json
import math
import os
import re
import subprocess
import sys

TOOL_NAME = "connect-anything"
TOOL_VERSION = "0.1.0"
TOOL_URL = "https://github.com/gaurpulkit/connect-anything"
LOCK_NAME = "connect-anything.lock.json"
LOCK_VERSION = 1

HOME = os.path.expanduser("~")
STATE_DIR = os.environ.get("CONNECT_ANYTHING_HOME") or os.path.join(HOME, ".connect-anything")
STAGING_DIR = os.path.join(STATE_DIR, "staging")

SKIP_DIRS = {".git", "node_modules", "__pycache__", ".venv", "venv"}
EM_DASH = chr(0x2014)
EN_DASH = chr(0x2013)


class EngineError(Exception):
    """A problem the user can act on. The message is printed without a traceback."""


def log(msg):
    print(msg, file=sys.stderr, flush=True)


def run(cmd, cwd=None, timeout=300, env=None, check=True):
    """Run a command without a shell. Returns stdout (str). Raises EngineError on failure when check."""
    full_env = dict(os.environ)
    full_env.update({"GIT_TERMINAL_PROMPT": "0", "GIT_LFS_SKIP_SMUDGE": "1"})
    if env:
        full_env.update(env)
    try:
        p = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=timeout, env=full_env)
    except FileNotFoundError:
        raise EngineError(f"{cmd[0]} is not installed or not on PATH")
    except subprocess.TimeoutExpired:
        raise EngineError(f"{cmd[0]} timed out after {timeout}s")
    if check and p.returncode != 0:
        raise EngineError(f"{' '.join(cmd[:4])} failed: {(p.stderr or p.stdout).strip()[:400]}")
    return p.stdout


# ------------------------------------------------------------------ hashing
def sha256_bytes(data):
    return hashlib.sha256(data).hexdigest()


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


# Node's String.prototype.localeCompare (ICU root collation) orders ASCII punctuation
# before digits before letters, compares case only when everything else is equal, and
# puts lowercase first. vercel-labs/skills sorts files that way before hashing a folder,
# so this key reproduces its computedHash for ASCII paths.
_ICU_PUNCT = " _-,;:!?.'\"()[]{}@*/\\&#%`^+<=>|~$"
_PUNCT_WEIGHT = {c: i for i, c in enumerate(_ICU_PUNCT)}


def _icu_key(s):
    primary, tertiary = [], []
    for ch in s:
        if ch in _PUNCT_WEIGHT:
            primary.append(_PUNCT_WEIGHT[ch])
            tertiary.append(0)
        elif ch.isdigit() and ch.isascii():
            primary.append(100 + int(ch))
            tertiary.append(0)
        elif ch.isascii() and ch.isalpha():
            primary.append(200 + ord(ch.lower()) - 97)
            tertiary.append(1 if ch.isupper() else 0)
        else:
            primary.append(1000 + ord(ch.lower()))
            tertiary.append(1 if ch != ch.lower() else 0)
    return (primary, tertiary)


def iter_files(root):
    """Yield (relative posix path, absolute path) for every regular file under root, skipping SKIP_DIRS."""
    for dirpath, dirnames, filenames in os.walk(root, followlinks=False):
        dirnames[:] = sorted(d for d in dirnames if d not in SKIP_DIRS)
        for fn in sorted(filenames):  # files are never skipped by name; only the folders above are
            ap = os.path.join(dirpath, fn)
            rel = os.path.relpath(ap, root).replace(os.sep, "/")
            yield rel, ap


def folder_hash(root, exclude=()):
    """SHA-256 over every file: path then bytes, files in localeCompare order (vercel-labs/skills recipe)."""
    files = []
    for rel, ap in iter_files(root):
        if rel in exclude or os.path.islink(ap):
            continue
        files.append((rel, ap))
    files.sort(key=lambda x: _icu_key(x[0]))
    h = hashlib.sha256()
    for rel, ap in files:
        h.update(rel.encode("utf-8"))
        with open(ap, "rb") as f:
            h.update(f.read())
    return h.hexdigest()


# ------------------------------------------------------------------ json and text
def write_json(path, data):
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2, sort_keys=False)
        f.write("\n")
    os.replace(tmp, path)


def read_json(path, default=None):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        if default is not None:
            return default
        raise EngineError(f"not found: {path}")
    except ValueError as e:
        raise EngineError(f"{path} is not valid JSON: {e}")


def write_text(path, text):
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)


def estimate_tokens(text):
    """Rough token count for budgets. Leans high on purpose (3.6 characters per token)."""
    return int(math.ceil(len(text) / 3.6))


def slugify(text):
    """GitHub-style heading anchor: lowercase words joined by hyphens; punctuation and dashes dropped."""
    s = re.sub(r"[^\w\s-]", "", text.strip().lower()).replace("_", "")
    s = re.sub(r"\s+", "-", s)
    s = re.sub(r"-{2,}", "-", s).strip("-")
    return s or "section"


def skill_name_ok(name):
    return bool(re.fullmatch(r"[a-z0-9]+(-[a-z0-9]+)*", name or "")) and len(name) <= 64


def to_skill_name(text):
    s = re.sub(r"[^a-z0-9]+", "-", (text or "").lower()).strip("-")
    s = re.sub(r"-{2,}", "-", s)
    return s[:64].strip("-") or "skill"


def plain_dashes(text):
    """House style: replace em and en dashes. Spaced dashes become a comma, ranges become 'to'."""
    text = re.sub(r"(\d)\s*" + EN_DASH + r"\s*(\d)", r"\1 to \2", text)
    text = re.sub(r"\s+[" + EM_DASH + EN_DASH + r"]\s+", ", ", text)
    text = re.sub(r"[" + EM_DASH + EN_DASH + r"]", ", ", text)
    return text


def has_dashes(text):
    return EM_DASH in text or EN_DASH in text


# ------------------------------------------------------------------ frontmatter
_FM_RE = re.compile(r"^---[ \t]*\r?\n(.*?)\r?\n---[ \t]*(\r?\n|$)", re.S)


def split_frontmatter(text):
    """Return (frontmatter block or None, body)."""
    m = _FM_RE.match(text)
    if not m:
        return None, text
    return m.group(1), text[m.end():]


def _unquote(v):
    v = v.strip()
    if len(v) >= 2 and v[0] == v[-1] == '"':
        try:
            return json.loads(v)
        except ValueError:
            return v[1:-1]
    if len(v) >= 2 and v[0] == v[-1] == "'":
        return v[1:-1].replace("''", "'")
    return v


def parse_frontmatter(block):
    """Parse the YAML subset skills use: scalars, quoted strings, block scalars, one level of maps and lists.

    Returns (dict, list of problems). Problems are things a strict YAML loader would reject.
    """
    data, problems = {}, []
    if block is None:
        return data, ["no frontmatter"]
    lines = block.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i]
        if not line.strip() or line.lstrip().startswith("#"):
            i += 1
            continue
        m = re.match(r"^([A-Za-z0-9_][A-Za-z0-9_.-]*):(?:\s+(.*)|\s*)$", line)
        if not m or line[0] in " \t":
            problems.append(f"line {i + 1}: cannot parse {line.strip()[:60]!r}")
            i += 1
            continue
        key, raw = m.group(1), (m.group(2) or "").rstrip()
        i += 1
        if raw[:1] in ("|", ">"):
            style = raw[0]
            chomp = "-" if "-" in raw else ("+" if "+" in raw else "")
            body = []
            while i < len(lines) and (not lines[i].strip() or lines[i][:1] in " \t"):
                body.append(lines[i])
                i += 1
            indent = min((len(b) - len(b.lstrip()) for b in body if b.strip()), default=0)
            body = [b[indent:] if b.strip() else "" for b in body]
            if style == "|":
                val = "\n".join(body)
            else:
                paras, cur = [], []
                for b in body:
                    if b == "":
                        paras.append(" ".join(cur))
                        cur = []
                    else:
                        cur.append(b.strip())
                paras.append(" ".join(cur))
                val = "\n".join(paras)
            val = val.rstrip("\n") if chomp == "-" else val.rstrip("\n") + ("\n" if chomp != "+" else "")
            if chomp == "":
                val = val.rstrip("\n")
            data[key] = val
        elif raw == "":
            nested, items = {}, []
            while i < len(lines) and (not lines[i].strip() or lines[i][:1] in " \t"):
                sub = lines[i].strip()
                i += 1
                if not sub:
                    continue
                if sub.startswith("- "):
                    items.append(_unquote(sub[2:]))
                    continue
                sm = re.match(r"^([^:]+):\s*(.*)$", sub)
                if sm:
                    nested[sm.group(1).strip()] = _unquote(sm.group(2))
                else:
                    problems.append(f"{key}: cannot parse {sub[:60]!r}")
            data[key] = items if items and not nested else nested
        else:
            if raw[0] in "{[" :
                problems.append(f"{key}: flow style ({raw[0]}) is not allowed by strict loaders")
            if raw[0] not in "\"'" and (": " in raw or " #" in raw):
                problems.append(f"{key}: plain value contains ': ' or ' #'; quote it")
            val = raw
            # plain scalars may continue on more-indented lines
            while i < len(lines) and lines[i][:1] in " \t" and lines[i].strip() and raw[0] not in "\"'":
                val += " " + lines[i].strip()
                i += 1
            data[key] = _unquote(val)
    return data, problems


def _yaml_scalar(v):
    v = str(v)
    safe = re.fullmatch(r"[A-Za-z0-9][^\n]*", v) and ": " not in v and " #" not in v and not v.endswith(":")
    safe = safe and v.strip() == v and v.lower() not in ("yes", "no", "true", "false", "on", "off", "null", "~")
    safe = safe and not re.search(r"[\"'`{}\[\]]", v[:1])
    return v if safe else json.dumps(v, ensure_ascii=False)


def dump_frontmatter(data):
    """Emit frontmatter that strictyaml (skills-ref) and Claude Code both accept. Key order is kept."""
    out = ["---"]
    for k, v in data.items():
        if v is None or v == "" or v == {} or v == []:
            continue
        if isinstance(v, dict):
            out.append(f"{k}:")
            for sk, sv in v.items():
                out.append(f"  {sk}: {json.dumps(str(sv), ensure_ascii=False)}")
        else:
            out.append(f"{k}: {_yaml_scalar(v)}")
    out.append("---")
    return "\n".join(out) + "\n"


# ------------------------------------------------------------------ markdown sections
_HEADING_RE = re.compile(r"^(#{1,6})[ \t]+(.+?)[ \t]*#*[ \t]*$")


def parse_sections(text, file_label="SKILL.md"):
    """Split markdown into heading sections, ignoring headings inside fenced code.

    Each section: {id, file, title, level, path (list of titles), start, end (1-based, inclusive), text}.
    The text before the first heading is a section titled '(preamble)' at level 0.
    """
    lines = text.splitlines()
    heads = []
    fence = None
    for idx, line in enumerate(lines):
        s = line.strip()
        fm = re.match(r"^(`{3,}|~{3,})", s)
        if fm:
            mark = fm.group(1)
            if fence is None:
                fence = mark[0] * len(mark)
            elif s.startswith(fence) and s.strip(fence[0]) == "":
                fence = None
            continue
        if fence:
            continue
        m = _HEADING_RE.match(line)
        if m:
            heads.append((idx, len(m.group(1)), m.group(2).strip()))
    sections = []
    first = heads[0][0] if heads else len(lines)
    if any(l.strip() for l in lines[:first]):
        sections.append({"title": "(preamble)", "level": 0, "start": 1, "end": first, "path": []})
    stack = []
    for n, (idx, level, title) in enumerate(heads):
        end = heads[n + 1][0] if n + 1 < len(heads) else len(lines)
        while stack and stack[-1][0] >= level:
            stack.pop()
        path = [t for _, t in stack] + [title]
        stack.append((level, title))
        sections.append({"title": title, "level": level, "start": idx + 1, "end": end, "path": path})
    seen = {}
    for sec in sections:
        sec["file"] = file_label
        sec["text"] = "\n".join(lines[sec["start"] - 1:sec["end"]])
        base = slugify(" ".join(sec["path"][-2:])) if sec["path"] else "preamble"
        seen[base] = seen.get(base, 0) + 1
        sec["id"] = base if seen[base] == 1 else f"{base}-{seen[base]}"
    return sections


def block_sections(sections, max_lines=90):
    """Group heading sections into merge units: each H2 (or H1 when there is no H2) with its children.

    A unit longer than max_lines is split at its H3 children so the chooser can keep parts of it.
    """
    if not sections:
        return []
    levels = sorted({s["level"] for s in sections if s["level"] > 0})
    unit_level = 2 if 2 in levels else (levels[0] if levels else 0)
    units, cur = [], None
    for s in sections:
        if s["level"] == 0 or (0 < s["level"] <= unit_level):
            cur = {"head": s, "members": [s]}
            units.append(cur)
        elif cur is None:
            cur = {"head": s, "members": [s]}
            units.append(cur)
        else:
            cur["members"].append(s)
    out = []
    for u in units:
        total = sum(m["end"] - m["start"] + 1 for m in u["members"])
        subs = [m for m in u["members"][1:] if m["level"] == unit_level + 1]
        if total > max_lines and subs:
            head_only = {**u["head"]}
            first_sub = subs[0]["start"]
            head_only["end"] = first_sub - 1
            groups = [[head_only]] if head_only["end"] >= head_only["start"] else []
            for m in u["members"][1:]:
                if m["level"] == unit_level + 1 or not groups:
                    groups.append([m])
                else:
                    groups[-1].append(m)
            for g in groups:
                out.append(_merge_unit(g))
        else:
            out.append(_merge_unit(u["members"]))
    return out


def _merge_unit(members):
    head = members[0]
    text = "\n".join(m["text"] if m is not head else head["text"] for m in members)
    return {
        "id": head["id"], "file": head["file"], "title": head["title"], "level": head["level"],
        "path": head["path"], "start": head["start"], "end": max(m["end"] for m in members),
        "text": text.rstrip() + "\n",
    }


def words(text):
    return re.findall(r"[a-z0-9][a-z0-9'+#.-]*[a-z0-9+#]|[a-z0-9]", text.lower())


STOP = set("""a an and are as at be but by can do does for from has have how if in into is it its of on or
so that the their then there these this to use used uses using was what when where which while who will
with you your not no never always only one each any all more most should must may also than them they
via per i we our us it's don't""".split())


def content_words(text):
    return [w for w in words(text) if w not in STOP and len(w) > 2]
