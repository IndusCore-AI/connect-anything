"""Fetch step: resolve a source spec, lock it to a commit, and stage a copy that is never executed.

Source specs
  owner/repo                       default branch HEAD
  owner/repo@ref                   branch, tag, or (short) commit
  owner/repo@ref:path/to/skill     one skill inside a multi-skill repo
  owner/repo:path/to/skill
  https://github.com/owner/repo/tree/<ref>/<path>
  ./local/skill  ~/path  /abs      an installed skill folder (snapshotted)
  /path/file.md#heading-slug       one section of a local markdown file
  alias=<any of the above>         name the source folder in the output
"""
import datetime as dt
import os
import re
import shutil
import tempfile

from .util import (STAGING_DIR, EngineError, iter_files, log, run, slugify, to_skill_name, write_json,
                   read_json, folder_hash)

GIT_SAFE = ["-c", "core.hooksPath=/dev/null", "-c", "core.symlinks=false", "-c", "protocol.file.allow=never",
            "-c", "submodule.recurse=false", "-c", "core.fsmonitor=false", "-c", "advice.detachedHead=false"]


def parse_spec(spec):
    alias = None
    m = re.match(r"^([a-z0-9][a-z0-9-]*)=(.+)$", spec)
    if m:
        alias, spec = m.group(1), m.group(2)
    spec = spec.strip()
    local = spec.startswith(("/", "./", "../", "~")) or os.path.exists(os.path.expanduser(spec.split("#")[0]))
    if local:
        path, _, section = spec.partition("#")
        return {"alias": alias, "type": "local", "path": os.path.abspath(os.path.expanduser(path)),
                "section": section or None, "spec": spec}
    m = re.match(r"^(?:https?://)?github\.com/([^/\s]+)/([^/\s#?]+?)(?:\.git)?(?:/tree/([^/\s]+)(?:/(.+?))?)?/?$", spec)
    if m:
        return {"alias": alias, "type": "github", "repo": f"{m.group(1)}/{m.group(2)}", "ref": m.group(3),
                "path": (m.group(4) or "").strip("/") or None, "spec": spec}
    m = re.match(r"^git@github\.com:([^/\s]+)/([^/\s]+?)(?:\.git)?$", spec)
    if m:
        return {"alias": alias, "type": "github", "repo": f"{m.group(1)}/{m.group(2)}", "ref": None, "path": None,
                "spec": spec}
    m = re.match(r"^([A-Za-z0-9_.-]+)/([A-Za-z0-9_.-]+)(?:@([^:\s]+))?(?::(.+))?$", spec)
    if m:
        return {"alias": alias, "type": "github", "repo": f"{m.group(1)}/{m.group(2)}", "ref": m.group(3),
                "path": (m.group(4) or "").strip("/") or None, "spec": spec}
    raise EngineError(f"cannot read source spec {spec!r}; use owner/repo[@ref][:path], a GitHub URL, or a local path")


def _gh_available():
    return shutil.which("gh") is not None and not os.environ.get("CONNECT_ANYTHING_GIT_BASE")


def remote_url(repo):
    """https://github.com/<repo>.git, or a local mirror when CONNECT_ANYTHING_GIT_BASE is set (offline tests)."""
    base = os.environ.get("CONNECT_ANYTHING_GIT_BASE")
    return os.path.join(base, repo + ".git") if base else f"https://github.com/{repo}.git"


def resolve_ref(repo, ref):
    """Return (full sha, commit date) for a branch, tag or short sha."""
    if _gh_available():
        out = run(["gh", "api", f"repos/{repo}/commits/{ref or 'HEAD'}", "--jq",
                   '.sha + " " + .commit.committer.date'], timeout=60)
        sha, _, date = out.strip().partition(" ")
        if re.fullmatch(r"[0-9a-f]{40}", sha):
            return sha, date[:10]
    if os.environ.get("CONNECT_ANYTHING_GIT_BASE"):
        url = remote_url(repo)
        sha = run(["git", "-C", url, "rev-parse", f"{ref or 'HEAD'}^{{commit}}"], timeout=30).strip()
        date = run(["git", "-C", url, "show", "-s", "--format=%cs", sha], timeout=30).strip()
        return sha, date
    if ref and re.fullmatch(r"[0-9a-f]{40}", ref):
        return ref, ""
    out = run(["git", "ls-remote", f"https://github.com/{repo}.git", ref or "HEAD"], timeout=60)
    line = out.strip().splitlines()[0] if out.strip() else ""
    if not line:
        raise EngineError(f"cannot resolve {repo}@{ref or 'HEAD'}")
    return line.split()[0], ""


def _git(args, cwd, timeout=300):
    cred = ["-c", "credential.helper=", "-c", "credential.helper=!gh auth git-credential"] if _gh_available() else []
    safe = list(GIT_SAFE)
    if os.environ.get("CONNECT_ANYTHING_GIT_BASE"):
        safe[safe.index("protocol.file.allow=never")] = "protocol.file.allow=always"
    return run(["git", *safe, *cred, *args], cwd=cwd, timeout=timeout)


def fetch_commits(repo, shas, dest):
    """Make dest a shallow repo holding exactly these commits (used by fetch and by update's diff)."""
    os.makedirs(dest, exist_ok=True)
    if not os.path.isdir(os.path.join(dest, ".git")):
        _git(["init", "-q"], dest)
        _git(["remote", "add", "origin", remote_url(repo)], dest)
    _git(["fetch", "-q", "--depth", "1", "--no-tags", "origin", *shas], dest, timeout=600)


def find_skill_dirs(root):
    hits = []
    for rel, _ in iter_files(root):
        if rel.endswith("SKILL.md") and (rel == "SKILL.md" or rel.endswith("/SKILL.md")):
            hits.append(os.path.dirname(rel) or ".")
    return sorted(set(hits), key=lambda p: (p != ".", p.count("/"), p))


def stage_github(src, refresh=False):
    repo = src["repo"]
    sha, date = resolve_ref(repo, src.get("ref"))
    dest = os.path.join(STAGING_DIR, f"{repo.replace('/', '__')}@{sha[:12]}")
    marker = os.path.join(dest, ".connect-anything-fetch.json")
    if os.path.exists(marker) and not refresh:
        meta = read_json(marker)
        if meta.get("sha") == sha:
            return dest, meta
    if os.path.isdir(dest):
        shutil.rmtree(dest)
    log(f"fetch {repo} @ {sha[:7]}")
    fetch_commits(repo, [sha], dest)
    _git(["checkout", "-q", "--detach", sha], dest)
    shutil.rmtree(os.path.join(dest, ".git"), ignore_errors=True)
    meta = {"source": repo, "sourceType": "github", "sourceUrl": f"https://github.com/{repo}", "sha": sha,
            "date": date, "fetchedAt": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
            "requestedRef": src.get("ref") or "HEAD"}
    write_json(marker, meta)
    return dest, meta


def stage_local(src):
    path = src["path"]
    if not os.path.exists(path):
        raise EngineError(f"local source not found: {path}")
    is_file = os.path.isfile(path)
    base = os.path.dirname(path) if is_file else path
    sha, dirty = None, None
    try:
        run(["git", "-C", base, "ls-files", "--error-unmatch", path], timeout=20)  # tracked at all?
        sha = run(["git", "-C", base, "rev-parse", "HEAD"], timeout=20).strip()
        dirty = bool(run(["git", "-C", base, "status", "--porcelain", "--", path], timeout=20).strip())
        if dirty:
            sha = None  # a commit would not describe what was read; the content hash does
    except EngineError:
        pass
    tmp = tempfile.mkdtemp(prefix="local-", dir=_ensure(STAGING_DIR))
    if is_file:
        shutil.copy2(path, os.path.join(tmp, os.path.basename(path)))
    else:
        for rel, ap in iter_files(path):
            if os.path.islink(ap):
                continue  # never follow a link out of the folder
            target = os.path.join(tmp, rel)
            os.makedirs(os.path.dirname(target), exist_ok=True)
            shutil.copy2(ap, target)
    h = folder_hash(tmp)
    dest = os.path.join(STAGING_DIR, f"local__{slugify(os.path.basename(path.rstrip('/')))}@{h[:12]}")
    if os.path.isdir(dest):
        shutil.rmtree(tmp)
    else:
        os.replace(tmp, dest)
    meta = {"source": path.replace(os.path.expanduser("~"), "~", 1), "sourceType": "local", "sha": sha,
            "dirty": dirty, "contentHash": h, "date": dt.date.today().isoformat(),
            "fetchedAt": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"), "file": is_file}
    write_json(os.path.join(dest, ".connect-anything-fetch.json"), meta)
    return dest, meta


def _ensure(d):
    os.makedirs(d, exist_ok=True)
    return d


def fetch(spec, refresh=False):
    """Stage one source. Returns a source record the read step consumes."""
    src = parse_spec(spec)
    if src["type"] == "github":
        root, meta = stage_github(src, refresh=refresh)
        skill_dirs = find_skill_dirs(root)
        rel = src.get("path")
        if rel:
            rel = rel[:-len("SKILL.md")].rstrip("/") or "." if rel.endswith("SKILL.md") else rel
            if not os.path.isfile(os.path.join(root, rel, "SKILL.md")):
                raise EngineError(f"{src['repo']}: no SKILL.md at {rel}. Skills in this repo: {skill_dirs or 'none'}")
            skill_paths = [rel]
        elif not skill_dirs:
            skill_paths = []
        elif skill_dirs[0] == ".":
            skill_paths = ["."]
        else:
            skill_paths = skill_dirs
        default_alias = to_skill_name(src["repo"].split("/")[1] if not rel or rel == "." else os.path.basename(rel))
    else:
        root, meta = stage_local(src)
        if meta["file"]:
            skill_paths = ["."]
        else:
            skill_paths = ["."] if os.path.isfile(os.path.join(root, "SKILL.md")) else find_skill_dirs(root)
        default_alias = to_skill_name(src["section"] or os.path.basename(src["path"].rstrip("/")).replace(".md", ""))
    return {
        "alias": src.get("alias") or default_alias,
        "spec": src["spec"],
        "type": src["type"],
        "root": root,
        "meta": meta,
        "skill_paths": skill_paths,
        "section": src.get("section"),
        "file": os.path.basename(src["path"]) if src["type"] == "local" and meta.get("file") else None,
    }
