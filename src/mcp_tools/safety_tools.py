"""Recoverable deletes (trash) and git-backed checkpoints."""

import json
import os
import re
import shutil
import subprocess
import tempfile
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from .security import is_safe_path
from .mcp_instance import mcp

CHECKPOINT_REF_PREFIX = "refs/mcp-checkpoints/"


# ---------------------------------------------------------------- trash

def trash_root() -> str:
    """Trash lives outside any project so it never pollutes git status."""
    root = os.environ.get("PROJECT_CREATOR_TRASH") or os.path.join(
        os.path.expanduser("~"), ".project-creator-mcp", "trash")
    os.makedirs(root, exist_ok=True)
    return root


def move_to_trash(path: str) -> Dict[str, Any]:
    """Move a file/dir into the trash with a manifest. Returns trash metadata."""
    abs_path = os.path.abspath(path)
    trash_id = datetime.now().strftime("%Y%m%d-%H%M%S-") + uuid.uuid4().hex[:6]
    entry_dir = os.path.join(trash_root(), trash_id)
    os.makedirs(entry_dir)
    meta = {
        "id": trash_id,
        "original_path": abs_path,
        "is_dir": os.path.isdir(abs_path),
        "deleted_at": datetime.now().isoformat(timespec="seconds"),
    }
    shutil.move(abs_path, os.path.join(entry_dir, "data"))
    with open(os.path.join(entry_dir, "meta.json"), "w", encoding="utf-8") as f:
        json.dump(meta, f)
    return meta


def list_trash_impl(limit: int = 50) -> Dict[str, Any]:
    items: List[Dict[str, Any]] = []
    root = trash_root()
    for name in sorted(os.listdir(root), reverse=True):
        meta_path = os.path.join(root, name, "meta.json")
        if os.path.isfile(meta_path):
            try:
                with open(meta_path, "r", encoding="utf-8") as f:
                    items.append(json.load(f))
            except (OSError, ValueError):
                continue
        if len(items) >= limit:
            break
    return {"success": True, "trash_dir": root, "items": items, "count": len(items)}


def restore_from_trash_impl(trash_id: str, overwrite: bool = False, dry_run: bool = False):
    if not re.fullmatch(r"[0-9]{8}-[0-9]{6}-[0-9a-f]{6}", trash_id or ""):
        return {"success": False, "error": "Invalid trash id (see list_trash)"}
    entry_dir = os.path.join(trash_root(), trash_id)
    meta_path = os.path.join(entry_dir, "meta.json")
    if not os.path.isfile(meta_path):
        return {"success": False, "error": "Trash entry not found"}
    with open(meta_path, "r", encoding="utf-8") as f:
        meta = json.load(f)
    dest = meta["original_path"]
    ok, message = is_safe_path(dest)
    if not ok:
        return {"success": False, "error": f"Path blocked for security: {message}"}
    if os.path.exists(dest) and not overwrite:
        return {"success": False, "error": f"Original path already exists: {dest} (use overwrite=True)"}
    if dry_run:
        return {"success": True, "dry_run": True, "would_restore_to": dest}
    try:
        if os.path.exists(dest):
            shutil.rmtree(dest) if os.path.isdir(dest) else os.remove(dest)
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        shutil.move(os.path.join(entry_dir, "data"), dest)
        shutil.rmtree(entry_dir, ignore_errors=True)
        return {"success": True, "dry_run": False, "restored_to": dest}
    except Exception as e:
        return {"success": False, "error": f"Failed to restore: {e}"}


@mcp.tool()
def list_trash(limit: int = 50) -> Dict[str, Any]:
    """
    List files recently deleted with delete_file (newest first).

    Args:
        limit: Maximum entries to return (default: 50)

    Returns:
        Dictionary with trash entries (id, original_path, deleted_at)
    """
    return list_trash_impl(limit)


@mcp.tool()
def restore_from_trash(trash_id: str, overwrite: bool = False, dry_run: bool = False) -> Dict[str, Any]:
    """
    Restore a file deleted with delete_file back to its original location.

    Args:
        trash_id: Id from list_trash
        overwrite: Replace whatever now exists at the original path (default: False)
        dry_run: Report the destination without restoring (default: False)

    Returns:
        Dictionary with the restored path
    """
    return restore_from_trash_impl(trash_id, overwrite, dry_run)


# ---------------------------------------------------------------- checkpoints

_IDENTITY_ENV = {
    "GIT_AUTHOR_NAME": "project-creator-mcp", "GIT_AUTHOR_EMAIL": "mcp@localhost",
    "GIT_COMMITTER_NAME": "project-creator-mcp", "GIT_COMMITTER_EMAIL": "mcp@localhost",
}


def _git(args: List[str], cwd: str, env: Optional[Dict[str, str]] = None, check: bool = True):
    full_env = os.environ.copy()
    full_env.update(_IDENTITY_ENV)
    if env:
        full_env.update(env)
    r = subprocess.run(["git"] + args, cwd=cwd, env=full_env, capture_output=True,
                       text=True, encoding="utf-8", errors="replace", timeout=120)
    if check and r.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)} failed: {r.stderr.strip()}")
    return r


def _repo_root(path: str) -> str:
    return _git(["rev-parse", "--show-toplevel"], cwd=path).stdout.strip()


def _snapshot_tree(root: str) -> str:
    """Write a tree of the full working directory (incl. untracked, minus ignored)
    using a throwaway index, leaving the real index and working tree untouched."""
    tmp = tempfile.mkdtemp(prefix="mcp-ckpt-")
    try:
        env = {"GIT_INDEX_FILE": os.path.join(tmp, "index")}
        _git(["add", "-A"], cwd=root, env=env)
        return _git(["write-tree"], cwd=root, env=env).stdout.strip()
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def _slug(label: str) -> str:
    return re.sub(r"[^A-Za-z0-9._-]+", "-", label).strip("-")[:40] or "checkpoint"


def create_checkpoint_impl(path: str = ".", label: str = "") -> Dict[str, Any]:
    ok, message = is_safe_path(path)
    if not ok:
        return {"success": False, "error": f"Path blocked for security: {message}"}
    try:
        root = _repo_root(path)
        tree = _snapshot_tree(root)
        head = _git(["rev-parse", "--verify", "-q", "HEAD"], cwd=root, check=False)
        commit_args = ["commit-tree", tree, "-m", f"mcp-checkpoint: {label or 'unlabeled'}"]
        if head.returncode == 0:
            commit_args[2:2] = ["-p", head.stdout.strip()]
        sha = _git(commit_args, cwd=root).stdout.strip()
        checkpoint_id = datetime.now().strftime("%Y%m%d-%H%M%S-") + _slug(label)
        _git(["update-ref", CHECKPOINT_REF_PREFIX + checkpoint_id, sha], cwd=root)
        return {
            "success": True, "checkpoint_id": checkpoint_id, "commit": sha, "repo": root,
            "message": "Checkpoint created (working tree untouched). Ignored files are not captured.",
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


def list_checkpoints_impl(path: str = ".") -> Dict[str, Any]:
    try:
        root = _repo_root(path)
        out = _git(["for-each-ref", "--sort=-creatordate", CHECKPOINT_REF_PREFIX,
                    "--format=%(refname)|%(objectname)|%(creatordate:iso)|%(contents:subject)"],
                   cwd=root).stdout
        items = []
        for line in out.splitlines():
            ref, sha, date, subject = (line.split("|", 3) + ["", "", "", ""])[:4]
            items.append({"checkpoint_id": ref[len(CHECKPOINT_REF_PREFIX):], "commit": sha,
                          "created": date, "label": subject.replace("mcp-checkpoint: ", "", 1)})
        return {"success": True, "repo": root, "checkpoints": items, "count": len(items)}
    except Exception as e:
        return {"success": False, "error": str(e)}


def restore_checkpoint_impl(checkpoint_id: str, path: str = ".", dry_run: bool = False):
    ok, message = is_safe_path(path)
    if not ok:
        return {"success": False, "error": f"Path blocked for security: {message}"}
    if not re.fullmatch(r"[A-Za-z0-9._-]+", checkpoint_id or ""):
        return {"success": False, "error": "Invalid checkpoint id (see list_checkpoints)"}
    try:
        root = _repo_root(path)
        ref = CHECKPOINT_REF_PREFIX + checkpoint_id
        sha = _git(["rev-parse", "--verify", "-q", ref], cwd=root, check=False)
        if sha.returncode != 0:
            return {"success": False, "error": "Checkpoint not found"}
        target_tree = _git(["rev-parse", sha.stdout.strip() + "^{tree}"], cwd=root).stdout.strip()
        current_tree = _snapshot_tree(root)
        # Direction current -> checkpoint: A = recreated, M = reverted, D = exists now only (left alone)
        diff = _git(["diff-tree", "-r", "--name-status", current_tree, target_tree], cwd=root).stdout
        changes = []
        for line in diff.splitlines():
            status, _, name = line.partition("\t")
            if status == "D":
                continue
            changes.append({"action": "recreate" if status == "A" else "revert", "path": name})
        if dry_run:
            return {"success": True, "dry_run": True, "files_affected": changes, "count": len(changes)}
        safety = create_checkpoint_impl(root, f"pre-restore-{checkpoint_id}")
        if changes:
            _git(["restore", f"--source={sha.stdout.strip()}", "--worktree", "--", "."], cwd=root)
        return {"success": True, "dry_run": False, "files_restored": changes, "count": len(changes),
                "undo_checkpoint": safety.get("checkpoint_id"),
                "note": "Files created after the checkpoint are left in place. "
                        "A checkpoint of the pre-restore state was saved (undo_checkpoint)."}
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
def create_checkpoint(path: str = ".", label: str = "") -> Dict[str, Any]:
    """
    Snapshot the entire working tree of a git repo (tracked, modified AND untracked
    files; gitignored files excluded) so risky work can be undone. Does not touch
    your working files, index, branches or stash list. Stored under refs/mcp-checkpoints/.

    Args:
        path: Any path inside the repo (default: current directory)
        label: Short description, e.g. "before refactor"

    Returns:
        Dictionary with checkpoint_id for restore_checkpoint
    """
    return create_checkpoint_impl(path, label)


@mcp.tool()
def list_checkpoints(path: str = ".") -> Dict[str, Any]:
    """
    List checkpoints created by create_checkpoint (newest first).

    Args:
        path: Any path inside the repo (default: current directory)

    Returns:
        Dictionary with checkpoint ids, commits, dates and labels
    """
    return list_checkpoints_impl(path)


@mcp.tool()
def restore_checkpoint(checkpoint_id: str, path: str = ".", dry_run: bool = False) -> Dict[str, Any]:
    """
    Restore files to the state captured by a checkpoint. Reverts modified files and
    recreates deleted ones; files created after the checkpoint are left alone.
    A safety checkpoint of the current state is saved first, so the restore is undoable.

    Args:
        checkpoint_id: Id from list_checkpoints
        path: Any path inside the repo (default: current directory)
        dry_run: List the files that would change without touching anything

    Returns:
        Dictionary with the files restored and the undo_checkpoint id
    """
    return restore_checkpoint_impl(checkpoint_id, path, dry_run)
