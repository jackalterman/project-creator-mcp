"""Filesystem search that is not tied to git (sees untracked and gitignored files)."""

import fnmatch
import os
import re
from typing import Any, Dict, List, Optional

from .security import is_safe_path
from .mcp_instance import mcp

DEFAULT_EXCLUDE_DIRS = [".git", "node_modules", "__pycache__", ".pytest_cache"]
MAX_FILE_BYTES = 2 * 1024 * 1024  # skip files larger than 2MB

# Credential files are never searched, whatever the globs or exclude_dirs say: search
# results are returned to the caller, so this must not be a way to read secrets.
# There is deliberately no opt-out parameter.
SECRET_DIRS = {".ssh", ".aws", ".gnupg"}
SECRET_FILE_PATTERNS = [
    ".env", ".env.*", "*.pem", "*.key", "*.p12", "*.pfx", "*.jks", "*.keystore",
    "id_rsa*", "id_dsa*", "id_ecdsa*", "id_ed25519*",
    ".npmrc", ".pypirc", ".netrc", "credentials", "credentials.json",
    "*.secret", "*.secrets", "secrets.json", "secrets.yaml", "secrets.yml", "secrets.toml",
]
# Templates meant to be committed and shared; safe and commonly searched.
SECRET_FILE_ALLOW = {".env.example", ".env.sample", ".env.template", ".env.dist", ".env.defaults"}


def _is_secret_file(name: str) -> bool:
    n = name.lower()
    if n in SECRET_FILE_ALLOW:
        return False
    return any(fnmatch.fnmatchcase(n, p) for p in SECRET_FILE_PATTERNS)


def _glob_to_regex(pattern: str) -> "re.Pattern":
    """Convert a glob (supporting **, *, ?) into a compiled regex."""
    pattern = pattern.replace("\\", "/")
    i, n, out = 0, len(pattern), []
    while i < n:
        c = pattern[i]
        if c == "*":
            if pattern[i:i + 2] == "**":
                i += 2
                if i < n and pattern[i] == "/":
                    i += 1
                    out.append("(?:.*/)?")
                else:
                    out.append(".*")
                continue
            out.append("[^/]*")
        elif c == "?":
            out.append("[^/]")
        else:
            out.append(re.escape(c))
        i += 1
    return re.compile("^" + "".join(out) + "$")


def _matches_glob(rel_path: str, patterns: List["re.Pattern"], raw: List[str]) -> bool:
    """Patterns without a slash match the basename; others match the relative path."""
    base = rel_path.rsplit("/", 1)[-1]
    for rx, src in zip(patterns, raw):
        target = rel_path if "/" in src.replace("\\", "/") else base
        if rx.match(target):
            return True
    return False


def search_files_impl(
    pattern: str,
    path: str = ".",
    glob: Optional[List[str]] = None,
    exclude_glob: Optional[List[str]] = None,
    use_regex: bool = False,
    ignore_case: bool = False,
    context_lines: int = 0,
    max_results: int = 200,
    files_only: bool = False,
    exclude_dirs: Optional[List[str]] = None,
) -> Dict[str, Any]:
    is_safe, message = is_safe_path(path)
    if not is_safe:
        return {"success": False, "error": f"Path blocked for security: {message}"}
    if not os.path.isdir(path):
        return {"success": False, "error": f"Directory not found: {path}"}
    if any(part.lower() in SECRET_DIRS for part in os.path.abspath(path).replace("\\", "/").split("/")):
        return {"success": False, "error": "Searching credential directories (.ssh, .aws, .gnupg) is not allowed"}
    if not pattern:
        return {"success": False, "error": "pattern must not be empty"}

    flags = re.IGNORECASE if ignore_case else 0
    try:
        rx = re.compile(pattern if use_regex else re.escape(pattern), flags)
    except re.error as e:
        return {"success": False, "error": f"Invalid regex pattern: {e}"}

    include_raw = glob or []
    exclude_raw = exclude_glob or []
    include_rx = [_glob_to_regex(g) for g in include_raw]
    exclude_rx = [_glob_to_regex(g) for g in exclude_raw]
    skip_dirs = set(DEFAULT_EXCLUDE_DIRS if exclude_dirs is None else exclude_dirs)
    context_lines = max(0, min(context_lines, 20))
    max_results = max(1, min(max_results, 2000))

    matches: List[Dict[str, Any]] = []
    matched_files: List[str] = []
    files_searched = 0
    files_skipped = 0
    secrets_skipped = 0
    truncated = False
    root = os.path.abspath(path)

    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = sorted(d for d in dirnames if d not in skip_dirs and d.lower() not in SECRET_DIRS)
        for name in sorted(filenames):
            if _is_secret_file(name):
                secrets_skipped += 1
                continue
            full = os.path.join(dirpath, name)
            rel = os.path.relpath(full, root).replace("\\", "/")
            if include_rx and not _matches_glob(rel, include_rx, include_raw):
                continue
            if exclude_rx and _matches_glob(rel, exclude_rx, exclude_raw):
                continue
            try:
                if os.path.getsize(full) > MAX_FILE_BYTES:
                    files_skipped += 1
                    continue
                with open(full, "rb") as fb:
                    raw = fb.read()
                if b"\x00" in raw[:8192]:  # binary
                    files_skipped += 1
                    continue
                lines = raw.decode("utf-8", errors="replace").splitlines()
            except OSError:
                files_skipped += 1
                continue

            files_searched += 1
            file_hit = False
            for idx, line in enumerate(lines):
                if not rx.search(line):
                    continue
                if not file_hit:
                    file_hit = True
                    matched_files.append(rel)
                if files_only:
                    break
                entry: Dict[str, Any] = {"path": rel, "line": idx + 1, "text": line}
                if context_lines:
                    entry["before"] = lines[max(0, idx - context_lines):idx]
                    entry["after"] = lines[idx + 1:idx + 1 + context_lines]
                matches.append(entry)
                if len(matches) >= max_results:
                    truncated = True
                    break
            if truncated:
                break
            if files_only and len(matched_files) >= max_results:
                truncated = True
                break
        if truncated:
            break

    result: Dict[str, Any] = {
        "success": True,
        "pattern": pattern,
        "root": root,
        "files_searched": files_searched,
        "files_skipped": files_skipped,
        "secret_files_skipped": secrets_skipped,
        "files_matched": len(matched_files),
        "truncated": truncated,
    }
    if files_only:
        result["files"] = matched_files
    else:
        result["matches"] = matches
        result["match_count"] = len(matches)
    return result


@mcp.tool()
def search_files(
    pattern: str,
    path: str = ".",
    glob: Optional[List[str]] = None,
    exclude_glob: Optional[List[str]] = None,
    use_regex: bool = False,
    ignore_case: bool = False,
    context_lines: int = 0,
    max_results: int = 200,
    files_only: bool = False,
    exclude_dirs: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    Search file contents under a directory WITHOUT relying on git, so untracked
    and gitignored files are included (unlike `git grep`).

    Args:
        pattern: Text (or regex when use_regex=True) to search for
        path: Directory to search (default: current directory)
        glob: Only search files matching any of these globs, e.g. ["**/*.ts", "src/**/*.tsx"].
              Patterns without a slash match the file name only.
        exclude_glob: Skip files matching any of these globs
        use_regex: Treat pattern as a regular expression (default: False)
        ignore_case: Case-insensitive match (default: False)
        context_lines: Lines of context before/after each match (0-20)
        max_results: Maximum matches (or files, if files_only) to return (default: 200)
        files_only: Return only the matching file paths
        exclude_dirs: Directory names to skip. Default: .git, node_modules,
                      __pycache__, .pytest_cache. Pass [] to search everything.

    Credential files (.env, *.pem, *.key, id_rsa*, .npmrc, .ssh/, .aws/, ...) are
    ALWAYS skipped and counted in secret_files_skipped; this cannot be turned off.
    Template files such as .env.example are searched normally.

    Returns:
        Dictionary with matches (path relative to `path`, 1-based line, text)
    """
    return search_files_impl(
        pattern, path, glob, exclude_glob, use_regex, ignore_case,
        context_lines, max_results, files_only, exclude_dirs,
    )
