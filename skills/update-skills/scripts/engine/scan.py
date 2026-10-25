"""Scan step: every line of every text file of every source, secondary files included.

The pattern list starts from skill-radar's (scripts/install_skill.py, RISKY). When that file is on this
machine its list is loaded too, so the two never drift apart. Severities:

  block   the candidate is excluded and named in the report (download-and-run, secret reads, hidden
          characters, prompt-injection wording, instructions that make the agent promote someone)
  review  kept only if a person or the agent looks and says why (sudo, agent-config writes, tracking links)
  info    recorded in the per-source README (subprocesses, network calls)

Findings are data. Nothing a scanned file says is followed.
"""
import base64
import hashlib
import importlib.util
import os
import re

SKILL_RADAR_INSTALLER = os.path.expanduser("~/.claude/skills/skill-radar/scripts/install_skill.py")

# (id, severity, regex, label). Kept in step with skill-radar's RISKY list; ids are stable for --allow.
PATTERNS = [
    ("download-exec", "block", r"(curl|wget)\b[^|\n]*\|\s*(sudo\s+)?(ba|z|da)?sh\b", "downloads a script and runs it"),
    ("download-exec-subst", "block", r"(ba|z)?sh\s+(-c\s+)?[\"']?\$\((curl|wget)\b|<\((curl|wget)\b", "runs downloaded code"),
    ("download-exec-ps", "block", r"\b(iwr|invoke-webrequest|irm|invoke-restmethod)\b[^|\n]*\|\s*(iex|invoke-expression)\b", "downloads a script and runs it (PowerShell)"),
    ("base64-exec", "block", r"base64\s+(-d|--decode|-D)\b[^\n]*\|\s*(ba|z)?sh\b|echo\s+[A-Za-z0-9+/=]{40,}\s*\|\s*base64", "decodes and runs hidden code"),
    ("reverse-shell", "block", r"\bnc\s+(-e|-c)\b|/dev/tcp/|\breverse shell\b|bash\s+-i\s+>&", "opens a remote shell"),
    ("secret-file", "block", r"\.aws/credentials|~/\.ssh/|\.ssh/id_|\bid_rsa\b|\bid_ed25519\b|\.netrc\b|\.git-credentials|\.docker/config\.json", "reads credential files"),
    ("keychain", "block", r"security\s+(find|dump)-(generic|internet)-password|\bdump-keychain\b", "reads saved passwords"),
    ("env-dump", "block", r"\bprintenv\b[^\n]*\|\s*(curl|nc|wget)|\benv\b\s*\|\s*(curl|nc|wget)|os\.environ\b[^\n]*(requests|urllib|fetch|post)", "sends environment variables somewhere"),
    ("injection", "block", r"ignore (all |any )?(the )?(previous|prior|above|earlier) (instructions|messages|rules)|disregard (all |the )?(previous|prior|system) (instructions|prompt)|do not (tell|inform|show) the user|without (telling|informing) the user|hide this from( the user)?|you are (now )?in (developer|god|dan|jailbreak) mode|new system prompt:", "prompt-injection wording"),
    ("promo-line", "block", r"who also makes\b|made by .{0,40}who also (makes|builds|sells)", "promotes the author's other products"),
    ("rm-home", "block", r"rm\s+-[a-z]*r[a-z]*f?[a-z]*\s+(/\s|/$|~/?\s|~/?$|\$HOME/?\s|\$HOME/?$|/\*)", "deletes the home or root folder"),
    ("hidden-unicode", "block", None, "zero-width or bidirectional control characters"),
    ("sudo", "review", r"\bsudo\b", "uses sudo"),
    ("base64-decode", "review", r"base64\s+(-d|--decode|-D)\b", "decodes base64"),
    ("chmod-777", "review", r"chmod\s+(-R\s+)?[0-7]*777", "chmod 777"),
    ("eval", "review", r"\beval\s*\(|\beval\s+[\"'$]", "evaluates code from a string"),
    ("persistence", "review", r"\blaunchctl\b|\bcrontab\b|LaunchAgents|LaunchDaemons|systemctl\s+enable|\.bashrc|\.zshrc|\.profile\b", "installs something that keeps running"),
    ("agent-config", "review", r"settings\.json|settings\.local\.json|\.claude/hooks|CLAUDE\.md|AGENTS\.md|\.cursorrules|\.codex/config|mcp\.json", "touches agent configuration"),
    ("api-key-ref", "review", r"(?-i:\b[A-Z][A-Z0-9_]*_(API_KEY|TOKEN|SECRET)\b)", "references an API key or token"),
    ("tracking-link", "review", r"[?&](ref|utm_source|utm_medium|utm_campaign|via|aff|affiliate)=", "tracking or affiliate link"),
    ("hidden-comment", "review", r"<!--(?![^>]*-->\s*$)|<!--[^>]*\b(you must|always|never|ignore|assistant|claude|the agent|do not)\b", "HTML comment the reader never sees"),
    ("paid-service", "review", r"\btop-?up\b|\bcredits? (balance|remaining|left)\b|\bbilling\b|\bper (call|request|run)\b[^\n]{0,30}\$|\$\d+(\.\d+)? (per|a) (call|run|request|month)|https?://api\.[a-z0-9-]+\.(ai|com|io|dev|app)", "depends on a paid or account-bound service"),
    ("package-install", "info", r"\b(npm|pnpm|yarn|bun)\s+(i|install|add)\b|\bnpx\s+(-y\s+)?[a-z@]|\bpip3?\s+install\b|\bbrew\s+install\b|\bgo\s+install\b|\bcargo\s+install\b", "installs a package"),
    ("subprocess", "info", r"os\.system\(|os\.popen\(|subprocess\.|child_process|execSync|spawnSync|\bspawn\(|\bexecFile\(|Deno\.run|Bun\.spawn", "runs subprocesses"),
    ("network", "info", r"\brequests\.(get|post|put|delete|request|Session)\b|urllib\.request|urlopen\(|http\.client|\bfetch\(|\baxios\b|XMLHttpRequest|new WebSocket|\bsocket\.(socket|create_connection)\b|https?\.(request|get)\(|\bcurl\s|\bwget\s|Invoke-WebRequest", "makes network calls"),
]

ZERO_WIDTH = re.compile("[" + "".join(chr(c) for c in (0x200B, 0x200C, 0x200D, 0x2060, 0x2061, 0x2062, 0x2063, 0x2064, 0x180E)) + "]")
BIDI = re.compile("[" + "".join(chr(c) for c in (*range(0x202A, 0x202F), *range(0x2066, 0x206A))) + "]")
B64_BLOB = re.compile(r"[A-Za-z0-9+/]{160,}={0,2}")
SEVERITY_ORDER = {"block": 0, "review": 1, "info": 2}


PROMO_APPEND = re.compile(r"\b(end|finish|close|conclude|sign off)\b[^.\n]{0,40}\b(reply|replies|response|responses|answer|answers|message|messages|output|work)\b[^.\n]{0,30}\bwith\b|\bappend\b[^.\n]{0,40}\b(line|note|credit|link|footer)\b|\badd (a|one|this) (short )?(line|note|credit|footer|link|byline)\b|\bsign (it|your (reply|work)) off\b", re.I)
PROMO_CONTENT = re.compile(r"who also makes|made by|built by|brought to you by|check out|follow (me|us)\b|my (apps?|products?|tools?|company|newsletter)|our (apps?|products?|tools?|newsletter)|\bsponsor|powered by|[?&](ref|utm_[a-z]+|via|aff|affiliate)=", re.I)
PROMO_HEADING = re.compile(r"^(sign[- ]?off|signoff|credits?|attribution|about the author|sponsors?|promotion|support (the|this) (author|project))\b", re.I)

_CACHE = {}


def _compiled():
    if "patterns" in _CACHE:
        return _CACHE["patterns"]
    out = []
    for pid, sev, pat, label in PATTERNS:
        out.append((pid, sev, re.compile(pat, re.I | re.M) if pat else None, label))
    _CACHE["patterns"] = out
    return out


def radar_patterns():
    """skill-radar's RISKY list, loaded from its installer when present. Returns [] when absent."""
    if "radar" in _CACHE:
        return _CACHE["radar"]
    _CACHE["radar"] = []
    if not os.path.isfile(SKILL_RADAR_INSTALLER):
        return []
    try:
        spec = importlib.util.spec_from_file_location("_skill_radar_install", SKILL_RADAR_INSTALLER)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)  # our own team's file, read only for its RISKY constant
        _CACHE["radar"] = list(getattr(mod, "RISKY", []))
        return _CACHE["radar"]
    except Exception:
        return []


def _finding_id(path, line_no, pid, text):
    return hashlib.sha1(f"{path}:{line_no}:{pid}:{text.strip()}".encode()).hexdigest()[:12]


def scan_text(path, text, kind="text"):
    findings = []
    compiled = _compiled()
    radar = [(re.compile(p, re.I), f"skill-radar pattern {n}") for n, (p, _label) in enumerate(radar_patterns(), 1)]
    is_doc = kind in ("markdown", "text")
    lines = text.splitlines()
    for i, line in enumerate(lines, 1):
        if BIDI.search(line):
            findings.append(_mk(path, i, "hidden-unicode", "block", "bidirectional control characters (text shown differs from text read)",
                                line.encode("unicode_escape").decode()[:160]))
        elif ZERO_WIDTH.search(line):
            # in prose they hide words from the reader; in code they are usually emoji sequences in a regex or string
            sev = "block" if is_doc else "review"
            findings.append(_mk(path, i, "hidden-unicode", sev, "zero-width characters",
                                line.encode("unicode_escape").decode()[:160]))
        hit_ids = set()
        for pid, sev, rx, label in compiled:
            if rx is None:
                continue
            if pid == "hidden-comment" and kind != "markdown":
                continue
            if pid in ("network", "subprocess") and kind != "script":
                continue
            if pid == "package-install" and kind not in ("script", "markdown"):
                continue
            if rx.search(line):
                hit_ids.add(pid)
                findings.append(_mk(path, i, pid, sev, label, line.strip()[:160]))
        for rx, label in radar:
            if rx.search(line) and not hit_ids:
                findings.append(_mk(path, i, "skill-radar", "review", label, line.strip()[:160]))
                break
        for blob in B64_BLOB.findall(line):
            decoded = _try_b64(blob)
            if decoded:
                for f in scan_text(f"{path} (base64 at line {i})", decoded, "text"):
                    if f["severity"] == "block":
                        f["line"] = i
                        findings.append(f)
    if kind == "markdown":
        findings.extend(promo_sections(path, text))
    return findings


NEGATION = re.compile(r"\b(never|don'?t|do not|no|not|without|avoid|strip|remove|refuse)\b", re.I)


def _negated(text, pos):
    """True when the sentence holding pos says not to do it ("Never add a credit line")."""
    start = max(text.rfind(".", 0, pos), text.rfind("\n", 0, pos), text.rfind(":", 0, pos), text.rfind(";", 0, pos))
    return bool(NEGATION.search(text[start + 1:pos]))


def promo_sections(path, text):
    """A section that tells the agent to append something AND carries promotional content is a sign-off."""
    from .util import parse_sections
    out = []
    for sec in parse_sections(text, path):
        body = sec["text"]
        append = next((m for m in PROMO_APPEND.finditer(body) if not _negated(body, m.start())), None)
        promo = PROMO_CONTENT.search(body)
        heading = PROMO_HEADING.search(sec["title"]) if sec["level"] else None
        if (append and promo) or (heading and promo and re.search(r"\b(you|always|every|each|add|include|end|mention)\b", body, re.I)):
            line = sec["start"] + body[: (append or promo).start()].count("\n")
            out.append(_mk(path, line, "promo-instruction", "block", "tells the agent to add a promotional line",
                           f"## {sec['title']}: " + body.splitlines()[line - sec["start"]].strip()[:120]))
        elif heading and sec["level"]:
            out.append(_mk(path, sec["start"], "promo-heading", "review", "credit section heading", f"## {sec['title']}"))
    return out


def _try_b64(blob):
    try:
        raw = base64.b64decode(blob + "=" * (-len(blob) % 4), validate=True)
    except Exception:
        return None
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        return None
    printable = sum(1 for c in text if c.isprintable() or c in "\n\t")
    return text if text and printable / len(text) > 0.95 else None


def _mk(path, line, pid, sev, label, excerpt):
    return {"id": _finding_id(path, line, pid, excerpt), "file": path, "line": line, "rule": pid,
            "severity": sev, "label": label, "excerpt": excerpt}


def scan_files(files, allow=()):
    """Scan file records from read_tree. Returns (findings, summary)."""
    findings = []
    for f in files:
        kind = f.get("kind")
        if kind == "symlink":
            findings.append(_mk(f["path"], 0, "symlink", "review", f"symbolic link to {f.get('target')}", f.get("target", "")))
            continue
        if kind == "binary-exec":
            findings.append(_mk(f["path"], 0, "binary-exec", "block", "compiled binary that cannot be read", f["path"]))
            continue
        if kind in ("archive", "binary"):
            findings.append(_mk(f["path"], 0, "unreadable", "review", f"{kind} file, not readable as text", f["path"]))
            continue
        if "text" not in f:
            continue
        findings.extend(scan_text(f["path"], f["text"], kind))
    for fd in findings:
        if fd["id"] in allow:
            fd["allowed"] = True
    seen, unique = set(), []
    for fd in findings:
        if fd["id"] not in seen:
            seen.add(fd["id"])
            unique.append(fd)
    findings = unique
    findings.sort(key=lambda x: (SEVERITY_ORDER[x["severity"]], x["file"], x["line"]))
    summary = {"block": 0, "review": 0, "info": 0, "allowed": 0}
    for fd in findings:
        if fd.get("allowed"):
            summary["allowed"] += 1
        else:
            summary[fd["severity"]] += 1
    return findings, summary


def blocked(findings):
    return [f for f in findings if f["severity"] == "block" and not f.get("allowed")]


def network_files(findings):
    return sorted({f["file"] for f in findings if f["rule"] == "network"})
