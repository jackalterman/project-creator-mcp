"""Safer edit tools: unique-match replace, atomic multi-hunk patches, move/rename."""

import difflib
import os
import shutil
import subprocess
import tempfile
from typing import Any, Dict, List, Optional

from .security import is_safe_path, get_file_extension
from src.config import SecurityConfig
from .mcp_instance import mcp

MAX_DIFF_CHARS = 4000


# ---------------------------------------------------------------- helpers

def read_text_exact(path: str) -> str:
    """Read text without newline translation (preserves CRLF/LF exactly)."""
    with open(path, "r", encoding="utf-8", newline="") as f:
        return f.read()


def write_text_atomic(path: str, content: str) -> None:
    """Write via temp file + os.replace, without newline translation."""
    directory = os.path.dirname(os.path.abspath(path))
    fd, tmp = tempfile.mkstemp(dir=directory, prefix=".mcp-edit-", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="") as f:
            f.write(content)
        try:
            shutil.copymode(path, tmp)
        except OSError:
            pass
        os.replace(tmp, path)
    except Exception:
        if os.path.exists(tmp):
            os.remove(tmp)
        raise


def _file_eol(content: str) -> str:
    """Return '\\r\\n' if the file consistently uses CRLF, else '\\n'."""
    crlf = content.count("\r\n")
    lf = content.count("\n") - crlf
    return "\r\n" if crlf and not lf else "\n"


def _normalize_eol(text: str, eol: str) -> str:
    return text.replace("\r\n", "\n").replace("\n", eol)


def _diff(path: str, before: str, after: str) -> str:
    diff = "".join(difflib.unified_diff(
        before.splitlines(keepends=True), after.splitlines(keepends=True),
        fromfile=f"a/{os.path.basename(path)}", tofile=f"b/{os.path.basename(path)}", n=2,
    ))
    if len(diff) > MAX_DIFF_CHARS:
        diff = diff[:MAX_DIFF_CHARS] + "\n... (diff truncated)"
    return diff


def _validate_edit_path(path: str) -> Optional[str]:
    ok, message = is_safe_path(path)
    if not ok:
        return f"Path blocked for security: {message}"
    ext = get_file_extension(path)
    if ext and ext not in SecurityConfig.ALLOWED_EXTENSIONS:
        return f"File extension not allowed: {ext}"
    if not os.path.isfile(path):
        return "File not found"
    return None


def _apply_one(content: str, old_str: str, new_str: str, replace_all: bool):
    """Return (new_content, error). Fails on zero matches or non-unique match."""
    if old_str == "":
        return None, "old_str must not be empty"
    eol = _file_eol(content)
    old = _normalize_eol(old_str, eol)
    new = _normalize_eol(new_str, eol)
    count = content.count(old)
    if count == 0:
        return None, "old_str not found"
    if count > 1 and not replace_all:
        return None, (f"old_str matches {count} times; add surrounding context "
                      f"to make it unique or set replace_all=True")
    return content.replace(old, new), None


# ---------------------------------------------------------------- str_replace

def str_replace_in_file_impl(path, old_str, new_str, replace_all=False, dry_run=False):
    err = _validate_edit_path(path)
    if err:
        return {"success": False, "error": err}
    try:
        before = read_text_exact(path)
    except UnicodeDecodeError:
        return {"success": False, "error": "File contains non-UTF-8 content"}
    after, err = _apply_one(before, old_str, new_str, replace_all)
    if err:
        return {"success": False, "error": err, "path": path}
    replacements = before.count(_normalize_eol(old_str, _file_eol(before)))
    if not dry_run:
        try:
            write_text_atomic(path, after)
        except OSError as e:
            return {"success": False, "error": f"Failed to write file: {e}"}
    return {
        "success": True,
        "dry_run": dry_run,
        "path": path,
        "replacements": replacements,
        "message": ("Would replace" if dry_run else "Replaced") + f" {replacements} occurrence(s)",
        "diff": _diff(path, before, after),
    }


@mcp.tool()
def str_replace_in_file(
    path: str,
    old_str: str,
    new_str: str,
    replace_all: bool = False,
    dry_run: bool = False,
) -> Dict[str, Any]:
    """
    Replace text in a file, failing unless old_str matches EXACTLY ONCE
    (or replace_all=True). Preserves the file's line endings (CRLF/LF).

    Args:
        path: File to edit
        old_str: Exact text to find (include surrounding context to make it unique)
        new_str: Replacement text (empty string deletes old_str)
        replace_all: Allow replacing multiple matches (default: False)
        dry_run: Return the diff without writing anything (default: False)

    Returns:
        Dictionary with success, replacements count and a unified diff
    """
    return str_replace_in_file_impl(path, old_str, new_str, replace_all, dry_run)


# ---------------------------------------------------------------- apply_edits

def apply_edits_impl(edits: List[Dict[str, Any]], dry_run: bool = False) -> Dict[str, Any]:
    if not edits:
        return {"success": False, "error": "edits must be a non-empty list"}

    contents: Dict[str, str] = {}   # abspath -> working content
    originals: Dict[str, str] = {}  # abspath -> original content
    display: Dict[str, str] = {}    # abspath -> path as given

    for i, edit in enumerate(edits):
        if not isinstance(edit, dict) or not all(k in edit for k in ("path", "old_str", "new_str")):
            return {"success": False, "failed_edit": i,
                    "error": "each edit needs 'path', 'old_str' and 'new_str'"}
        path = edit["path"]
        key = os.path.abspath(path)
        if key not in contents:
            err = _validate_edit_path(path)
            if err:
                return {"success": False, "failed_edit": i, "path": path, "error": err,
                        "note": "No files were modified"}
            try:
                originals[key] = contents[key] = read_text_exact(path)
            except UnicodeDecodeError:
                return {"success": False, "failed_edit": i, "path": path,
                        "error": "File contains non-UTF-8 content", "note": "No files were modified"}
            display[key] = path
        new_content, err = _apply_one(contents[key], edit["old_str"], edit["new_str"],
                                      bool(edit.get("replace_all", False)))
        if err:
            return {"success": False, "failed_edit": i, "path": path, "error": err,
                    "note": "No files were modified"}
        contents[key] = new_content

    changed = [k for k in contents if contents[k] != originals[k]]
    diffs = {display[k]: _diff(display[k], originals[k], contents[k]) for k in changed}

    if not dry_run:
        written: List[str] = []
        try:
            for k in changed:
                write_text_atomic(k, contents[k])
                written.append(k)
        except Exception as e:
            rollback_failures = []
            for k in written:
                try:
                    write_text_atomic(k, originals[k])
                except Exception:
                    rollback_failures.append(display[k])
            return {"success": False, "error": f"Write failed, rolled back: {e}",
                    "rollback_failures": rollback_failures}

    return {
        "success": True,
        "dry_run": dry_run,
        "edits_applied": len(edits),
        "files_changed": [display[k] for k in changed],
        "diffs": diffs,
        "message": ("Would apply" if dry_run else "Applied") + f" {len(edits)} edit(s) to {len(changed)} file(s)",
    }


@mcp.tool()
def apply_edits(edits: List[Dict[str, Any]], dry_run: bool = False) -> Dict[str, Any]:
    """
    Apply several exact-match edits (multi-hunk, optionally multi-file) ATOMICALLY:
    every edit is validated in memory first, and if any one fails (not found, or
    not unique) nothing is written. Edits run in order, so a later edit in the same
    file sees the result of earlier ones. Line endings are preserved.

    Args:
        edits: List of {"path": str, "old_str": str, "new_str": str, "replace_all": bool (optional)}
        dry_run: Validate and return diffs without writing (default: False)

    Returns:
        Dictionary with files_changed and per-file unified diffs, or failed_edit index on error
    """
    return apply_edits_impl(edits, dry_run)


# ---------------------------------------------------------------- move / rename

def _git_tracked(path: str) -> bool:
    """True if path is tracked by git (so a rename should go through `git mv`)."""
    directory = os.path.dirname(os.path.abspath(path))
    try:
        r = subprocess.run(["git", "ls-files", "--error-unmatch", "--", os.path.basename(path)],
                           cwd=directory, capture_output=True, text=True, timeout=15)
        return r.returncode == 0
    except (OSError, subprocess.SubprocessError):
        return False


def move_path_impl(source: str, destination: str, overwrite: bool = False, dry_run: bool = False):
    for label, p in (("Source", source), ("Destination", destination)):
        ok, message = is_safe_path(p)
        if not ok:
            return {"success": False, "error": f"{label} path blocked: {message}"}
    if not os.path.exists(source):
        return {"success": False, "error": "Source path does not exist"}
    if os.path.exists(destination) and not overwrite:
        return {"success": False, "error": "Destination exists (use overwrite=True to replace)"}
    if os.path.abspath(source) == os.path.abspath(destination):
        return {"success": False, "error": "Source and destination are the same"}
    if os.path.isfile(source):
        # A rename must not turn a file into a type that write tools would refuse to create.
        # Keeping the file's own extension is always fine.
        src_ext, dest_ext = get_file_extension(source), get_file_extension(destination)
        if dest_ext and dest_ext != src_ext and dest_ext not in SecurityConfig.ALLOWED_EXTENSIONS:
            return {"success": False, "error": f"Destination extension not allowed: {dest_ext}"}

    use_git = os.path.isfile(source) and _git_tracked(source)
    plan = {"source": source, "destination": destination,
            "method": "git mv" if use_git else "filesystem move"}
    if dry_run:
        return {"success": True, "dry_run": True, **plan,
                "message": f"Would move via {plan['method']}"}

    try:
        dest_dir = os.path.dirname(os.path.abspath(destination))
        os.makedirs(dest_dir, exist_ok=True)
        if overwrite and os.path.isfile(destination):
            os.remove(destination)
        if use_git:
            args = ["git", "mv", "-f", "--", os.path.abspath(source), os.path.abspath(destination)]
            r = subprocess.run(args, cwd=os.path.dirname(os.path.abspath(source)),
                               capture_output=True, text=True, timeout=30)
            if r.returncode != 0:
                return {"success": False, "error": f"git mv failed: {r.stderr.strip()}"}
        else:
            shutil.move(source, destination)
        return {"success": True, "dry_run": False, **plan,
                "message": f"Moved via {plan['method']}"}
    except Exception as e:
        return {"success": False, "error": f"Failed to move: {e}"}


@mcp.tool()
def move_path(
    source: str,
    destination: str,
    overwrite: bool = False,
    dry_run: bool = False,
) -> Dict[str, Any]:
    """
    Move or rename a file or directory. Tracked files use `git mv` so git keeps
    rename history; everything else uses a plain filesystem move.

    Args:
        source: Existing file or directory
        destination: New path (parent directories are created)
        overwrite: Replace an existing destination file (default: False)
        dry_run: Report what would happen without moving anything (default: False)

    Returns:
        Dictionary with the method used ("git mv" or "filesystem move")
    """
    return move_path_impl(source, destination, overwrite, dry_run)
