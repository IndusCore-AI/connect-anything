"""Read step: every file of every source is read in full, hashed, classified and split into sections.

Reading is mechanical and complete: a file counts as read only when the bytes read equal its size.
The agent still reads the text files it keeps or the scanner flags; this step guarantees that nothing
is skipped by the scanner, including secondary files a SKILL.md never mentions.
"""
import os

from .util import (EngineError, block_sections, iter_files, parse_frontmatter, parse_sections, sha256_bytes,
                   split_frontmatter, estimate_tokens)

TEXT_EXT = {".md", ".markdown", ".txt", ".rst", ".json", ".jsonl", ".yaml", ".yml", ".toml", ".csv", ".tsv",
            ".py", ".js", ".mjs", ".cjs", ".ts", ".tsx", ".jsx", ".sh", ".bash", ".zsh", ".fish", ".ps1", ".bat",
            ".rb", ".go", ".rs", ".java", ".kt", ".swift", ".c", ".h", ".cpp", ".css", ".scss", ".html", ".htm",
            ".xml", ".svg", ".ini", ".cfg", ".conf", ".env", ".sql", ".lua", ".pl", ".php", ".r", ".tex", ".mdx",
            ".vue", ".svelte", ".astro", ".lock", ".gitignore", ""}
SCRIPT_EXT = {".py", ".js", ".mjs", ".cjs", ".ts", ".sh", ".bash", ".zsh", ".fish", ".ps1", ".bat", ".rb", ".pl",
              ".php", ".lua", ".go", ".rs"}
IMAGE_EXT = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".ico", ".avif", ".bmp"}
EXEC_BINARY_EXT = {".so", ".dylib", ".dll", ".exe", ".bin", ".whl", ".jar", ".class", ".wasm", ".node", ".o", ".a"}
ARCHIVE_EXT = {".zip", ".gz", ".tgz", ".tar", ".7z", ".rar", ".xz", ".bz2"}
LICENSE_NAMES = ("LICENSE", "LICENSE.md", "LICENSE.txt", "LICENCE", "LICENCE.md", "LICENCE.txt", "COPYING",
                 "COPYING.md", "LICENSE-MIT", "LICENSE-APACHE", "UNLICENSE")
NOTICE_NAMES = ("NOTICE", "NOTICE.md", "NOTICE.txt")
MAX_TEXT_BYTES = 5_000_000


def classify(rel, data):
    ext = os.path.splitext(rel)[1].lower()
    base = os.path.basename(rel)
    if ext in IMAGE_EXT:
        return "image"
    if ext in EXEC_BINARY_EXT:
        return "binary-exec"
    if ext in ARCHIVE_EXT:
        return "archive"
    if b"\x00" in data[:8192]:
        return "binary"
    if ext in (".md", ".markdown", ".mdx"):
        return "markdown"
    if ext in SCRIPT_EXT or data.startswith(b"#!"):
        return "script"
    if ext in (".json", ".jsonl", ".csv", ".tsv", ".yaml", ".yml", ".toml"):
        return "data"
    if ext in TEXT_EXT or base in LICENSE_NAMES or base in NOTICE_NAMES:
        return "text"
    try:
        data.decode("utf-8")
        return "text"
    except UnicodeDecodeError:
        return "binary"


def read_tree(root):
    """Read every file under root. Returns a list of file records; text is kept for text kinds."""
    records = []
    for rel, ap in iter_files(root):
        if os.path.basename(rel) == ".connect-anything-fetch.json":
            continue
        rec = {"path": rel}
        if os.path.islink(ap):
            rec.update({"kind": "symlink", "size": 0, "sha256": None, "read": False,
                        "target": os.readlink(ap)})
            records.append(rec)
            continue
        size = os.path.getsize(ap)
        with open(ap, "rb") as f:
            data = f.read()
        if len(data) != size:
            raise EngineError(f"short read on {rel}: {len(data)} of {size} bytes")
        kind = classify(rel, data)
        rec.update({"kind": kind, "size": size, "sha256": sha256_bytes(data), "read": True})
        if kind in ("markdown", "script", "data", "text"):
            if size > MAX_TEXT_BYTES:
                rec["oversize"] = True
            text = data.decode("utf-8", errors="replace")
            rec["decode_errors"] = text.count(chr(0xFFFD)) - data.decode("utf-8", errors="ignore").count(chr(0xFFFD))
            rec["text"] = text
            rec["lines"] = text.count("\n") + (0 if text.endswith("\n") or not text else 1)
            rec["executable"] = bool(os.stat(ap).st_mode & 0o111)
        records.append(rec)
    return records


def read_source(src):
    """Read one fetched source. Adds files, frontmatter, sections and licence-file text to the record."""
    root = src["root"]
    out = []
    for skill_path in src["skill_paths"] or ["."]:
        skill_root = os.path.normpath(os.path.join(root, skill_path))
        files = read_tree(skill_root)
        rec = dict(src)
        rec["skill_path"] = skill_path
        rec["skill_root"] = skill_root
        rec["files"] = files
        # licence and notice files from the skill folder, then each parent up to the repo root
        rec["licence_files"], rec["notice_files"] = _licence_files(root, skill_root)
        main = None
        if src.get("file"):
            main = next((f for f in files if f["path"] == src["file"]), None)
        else:
            main = next((f for f in files if f["path"] == "SKILL.md"), None)
        if main is None:
            rec.update({"frontmatter": {}, "frontmatter_problems": ["no SKILL.md"], "sections": [], "body": ""})
        else:
            block, body = split_frontmatter(main["text"])
            fm, problems = parse_frontmatter(block) if block is not None else ({}, ["no frontmatter"])
            offset = main["text"][: len(main["text"]) - len(body)].count("\n")
            sections = parse_sections(body, main["path"])
            for s in sections:
                s["start"] += offset
                s["end"] += offset
            if src.get("section"):
                sections = _select_section(sections, src["section"], main["path"])
            units = block_sections(sections)
            rec.update({"frontmatter": fm, "frontmatter_problems": problems, "main_file": main["path"],
                        "body": "".join(u["text"] for u in units) if src.get("section") else body,
                        "sections": units})
        rec["body_tokens"] = estimate_tokens(rec["body"])
        rec["bytes_read"] = sum(f["size"] for f in files)
        rec["files_read"] = sum(1 for f in files if f.get("read"))
        if src["skill_paths"] and len(src["skill_paths"]) > 1:
            rec["alias"] = f"{src['alias']}-{os.path.basename(skill_path)}" if skill_path != "." else src["alias"]
        out.append(rec)
    return out


def reference_sections(rec, rel):
    """Sections of a markdown reference file inside a source (for update gap search and evals)."""
    f = next((x for x in rec["files"] if x["path"] == rel and x["kind"] == "markdown"), None)
    if not f:
        return []
    block, body = split_frontmatter(f["text"])
    return block_sections(parse_sections(body, rel))


def _select_section(sections, slug, label):
    """Keep one heading (by slug of its title) and everything under it."""
    from .util import slugify
    target = None
    for s in sections:
        if slugify(s["title"]) == slug or s["id"] == slug:
            target = s
            break
    if target is None:
        names = ", ".join(slugify(s["title"]) for s in sections if s["level"] and s["level"] <= 2)
        raise EngineError(f"{label}: no heading matches #{slug}. Headings: {names}")
    picked = []
    inside = False
    for s in sections:
        if s is target:
            inside = True
            picked.append(s)
            continue
        if inside:
            if s["level"] <= target["level"]:
                break
            picked.append(s)
    return picked


def _licence_files(repo_root, skill_root):
    found, notices = [], []
    d = skill_root
    repo_root = os.path.normpath(repo_root)
    while True:
        for name in os.listdir(d):
            ap = os.path.join(d, name)
            if not os.path.isfile(ap):
                continue
            rel = os.path.relpath(ap, repo_root).replace(os.sep, "/")
            if name in LICENSE_NAMES or name.upper().startswith(("LICENSE", "LICENCE")):
                found.append({"path": rel, "text": open(ap, encoding="utf-8", errors="replace").read(),
                              "level": "skill" if d == skill_root else "repo" if d == repo_root else "parent"})
            elif name in NOTICE_NAMES:
                notices.append({"path": rel, "text": open(ap, encoding="utf-8", errors="replace").read()})
        if os.path.normpath(d) == repo_root or len(d) <= len(repo_root):
            break
        d = os.path.dirname(d)
    return found, notices
