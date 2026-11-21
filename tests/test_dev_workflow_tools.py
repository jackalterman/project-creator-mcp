import json
import os
import shutil
import subprocess
import sys
import time

import pytest

from src.mcp_tools import file_system_tools, safety_tools
from src.mcp_tools.search_tools import search_files_impl
from src.mcp_tools.edit_tools import (
    str_replace_in_file_impl, apply_edits_impl, move_path_impl,
)
from src.mcp_tools.safety_tools import (
    list_trash_impl, restore_from_trash_impl,
    create_checkpoint_impl, list_checkpoints_impl, restore_checkpoint_impl,
)
from src.mcp_tools.check_tools import (
    parse_tsc, parse_eslint, parse_vitest, parse_pytest_junit,
)


def _fn(tool):
    """@mcp.tool() returns a plain function or a FunctionTool depending on FastMCP version."""
    return getattr(tool, "fn", tool)


def _write(path, text, newline=""):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline=newline) as f:
        f.write(text)


def _read(path):
    with open(path, "r", encoding="utf-8", newline="") as f:
        return f.read()


needs_git = pytest.mark.skipif(shutil.which("git") is None, reason="git not installed")


def _git(cwd, *args):
    return subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@t", *args],
                          cwd=cwd, capture_output=True, text=True, check=True).stdout


@pytest.fixture
def repo(temp_dir):
    _git(temp_dir, "init")
    _write(os.path.join(temp_dir, "a.txt"), "one\ntwo\n")
    _git(temp_dir, "add", "-A")
    _git(temp_dir, "commit", "-m", "init")
    return temp_dir


@pytest.fixture
def trash(temp_dir, monkeypatch):
    t = os.path.join(temp_dir, "_trash")
    monkeypatch.setenv("PROJECT_CREATOR_TRASH", t)
    return t


# ------------------------------------------------------------------ search

def test_search_finds_untracked_and_ignored(repo):
    _write(os.path.join(repo, ".gitignore"), "ignored.txt\n")
    _write(os.path.join(repo, "ignored.txt"), "needle here\n")
    _write(os.path.join(repo, "untracked.txt"), "another needle\n")
    r = search_files_impl("needle", repo)
    paths = {m["path"] for m in r["matches"]}
    assert paths == {"ignored.txt", "untracked.txt"}


def test_search_glob_exclude_and_dirs(temp_dir):
    _write(os.path.join(temp_dir, "src", "a.ts"), "TODO x\n")
    _write(os.path.join(temp_dir, "src", "b.js"), "TODO y\n")
    _write(os.path.join(temp_dir, "node_modules", "pkg", "c.ts"), "TODO z\n")
    r = search_files_impl("TODO", temp_dir, glob=["**/*.ts"])
    assert [m["path"] for m in r["matches"]] == ["src/a.ts"]
    r = search_files_impl("TODO", temp_dir, glob=["*.ts"], exclude_dirs=[])
    assert {m["path"] for m in r["matches"]} == {"src/a.ts", "node_modules/pkg/c.ts"}
    r = search_files_impl("TODO", temp_dir, exclude_glob=["src/*.js"])
    assert {m["path"] for m in r["matches"]} == {"src/a.ts"}


def test_search_regex_case_context_and_limits(temp_dir):
    _write(os.path.join(temp_dir, "f.txt"), "a\nFoo123\nb\n")
    r = search_files_impl(r"foo\d+", temp_dir, use_regex=True, ignore_case=True, context_lines=1)
    m = r["matches"][0]
    assert m["line"] == 2 and m["before"] == ["a"] and m["after"] == ["b"]
    assert search_files_impl("(", temp_dir, use_regex=True)["success"] is False
    r = search_files_impl("a", temp_dir, files_only=True)
    assert r["files"] == ["f.txt"]


def test_search_skips_binary(temp_dir):
    with open(os.path.join(temp_dir, "bin.dat"), "wb") as f:
        f.write(b"needle\x00\x01")
    r = search_files_impl("needle", temp_dir)
    assert r["match_count"] == 0 and r["files_skipped"] == 1


# ------------------------------------------------------------------ ranged read

def test_read_file_range(temp_dir):
    p = os.path.join(temp_dir, "big.txt")
    _write(p, "\n".join(f"line{i}" for i in range(1, 11)))
    r = _fn(file_system_tools.read_file)(p, start_line=3, end_line=5)
    assert r["content"] == "line3\nline4\nline5"
    assert (r["start_line"], r["end_line"], r["total_lines"], r["has_more"]) == (3, 5, 10, True)
    r = _fn(file_system_tools.read_file)(p, start_line=9, line_numbers=True)
    assert r["content"] == "9\tline9\n10\tline10" and r["has_more"] is False
    assert _fn(file_system_tools.read_file)(p, start_line=50)["success"] is False
    assert _fn(file_system_tools.read_file)(p, start_line=5, end_line=2)["success"] is False


def test_read_file_without_range_unchanged(temp_dir):
    p = os.path.join(temp_dir, "x.txt")
    _write(p, "Content")
    r = _fn(file_system_tools.read_file)(p)
    assert r["content"] == "Content" and "start_line" not in r


# ------------------------------------------------------------------ str_replace / apply_edits

def test_str_replace_unique_required(temp_dir):
    p = os.path.join(temp_dir, "f.txt")
    _write(p, "foo\nbar\nfoo\n")
    r = str_replace_in_file_impl(p, "foo", "baz")
    assert not r["success"] and "2 times" in r["error"]
    assert _read(p) == "foo\nbar\nfoo\n"
    assert not str_replace_in_file_impl(p, "nope", "x")["success"]
    assert str_replace_in_file_impl(p, "bar", "BAR")["success"]
    assert str_replace_in_file_impl(p, "foo", "baz", replace_all=True)["replacements"] == 2
    assert _read(p) == "baz\nBAR\nbaz\n"


def test_str_replace_dry_run_writes_nothing(temp_dir):
    p = os.path.join(temp_dir, "f.txt")
    _write(p, "hello\n")
    r = str_replace_in_file_impl(p, "hello", "bye", dry_run=True)
    assert r["success"] and r["dry_run"] and "-hello" in r["diff"] and "+bye" in r["diff"]
    assert _read(p) == "hello\n"


def test_str_replace_preserves_crlf(temp_dir):
    p = os.path.join(temp_dir, "crlf.txt")
    _write(p, "a\r\nb\r\nc\r\n")
    r = str_replace_in_file_impl(p, "a\nb", "x\ny")  # LF in the request, CRLF in the file
    assert r["success"]
    assert _read(p) == "x\r\ny\r\nc\r\n"


def test_str_replace_rejects_bad_targets(temp_dir):
    assert not str_replace_in_file_impl(os.path.join(temp_dir, "missing.txt"), "a", "b")["success"]
    exe = os.path.join(temp_dir, "x.exe")
    _write(exe, "a")
    assert "extension" in str_replace_in_file_impl(exe, "a", "b")["error"]
    p = os.path.join(temp_dir, "e.txt")
    _write(p, "a")
    assert not str_replace_in_file_impl(p, "", "b")["success"]


def test_apply_edits_is_atomic(temp_dir):
    a, b = os.path.join(temp_dir, "a.txt"), os.path.join(temp_dir, "b.txt")
    _write(a, "alpha\n")
    _write(b, "beta\n")
    r = apply_edits_impl([
        {"path": a, "old_str": "alpha", "new_str": "ALPHA"},
        {"path": b, "old_str": "does-not-exist", "new_str": "x"},
    ])
    assert not r["success"] and r["failed_edit"] == 1
    assert _read(a) == "alpha\n" and _read(b) == "beta\n"  # nothing written


def test_apply_edits_multi_hunk_multi_file(temp_dir):
    a, b = os.path.join(temp_dir, "a.txt"), os.path.join(temp_dir, "b.txt")
    _write(a, "one\ntwo\n")
    _write(b, "beta\n")
    edits = [
        {"path": a, "old_str": "one", "new_str": "1"},
        {"path": a, "old_str": "1\ntwo", "new_str": "1\n2"},  # sees result of the first edit
        {"path": b, "old_str": "beta", "new_str": "BETA"},
    ]
    dry = apply_edits_impl(edits, dry_run=True)
    assert dry["success"] and _read(a) == "one\ntwo\n"
    r = apply_edits_impl(edits)
    assert r["success"] and len(r["files_changed"]) == 2
    assert _read(a) == "1\n2\n" and _read(b) == "BETA\n"


def test_apply_edits_validates_input(temp_dir):
    assert not apply_edits_impl([])["success"]
    assert not apply_edits_impl([{"path": "x"}])["success"]


# ------------------------------------------------------------------ move

def test_move_path_plain_and_dry_run(temp_dir):
    src, dst = os.path.join(temp_dir, "s.txt"), os.path.join(temp_dir, "sub", "d.txt")
    _write(src, "data")
    r = move_path_impl(src, dst, dry_run=True)
    assert r["success"] and os.path.exists(src) and not os.path.exists(dst)
    r = move_path_impl(src, dst)
    assert r["success"] and not os.path.exists(src) and _read(dst) == "data"


def test_move_path_refuses_overwrite(temp_dir):
    a, b = os.path.join(temp_dir, "a.txt"), os.path.join(temp_dir, "b.txt")
    _write(a, "A")
    _write(b, "B")
    assert not move_path_impl(a, b)["success"]
    assert move_path_impl(a, b, overwrite=True)["success"] and _read(b) == "A"


@needs_git
def test_move_path_uses_git_mv_for_tracked_files(repo):
    src, dst = os.path.join(repo, "a.txt"), os.path.join(repo, "renamed.txt")
    r = move_path_impl(src, dst)
    assert r["success"] and r["method"] == "git mv"
    status = _git(repo, "status", "--porcelain")
    assert "R" in status and "renamed.txt" in status


# ------------------------------------------------------------------ trash

def test_delete_goes_to_trash_and_restores(temp_dir, trash):
    p = os.path.join(temp_dir, "keep.txt")
    _write(p, "precious")
    r = _fn(file_system_tools.delete_file)(p)
    assert r["success"] and r["recoverable"] and not os.path.exists(p)
    items = list_trash_impl()["items"]
    assert items[0]["id"] == r["trash_id"]
    assert restore_from_trash_impl(r["trash_id"], dry_run=True)["success"]
    assert not os.path.exists(p)
    assert restore_from_trash_impl(r["trash_id"])["success"]
    assert _read(p) == "precious"


def test_delete_dry_run_and_permanent(temp_dir, trash):
    p = os.path.join(temp_dir, "f.txt")
    _write(p, "x")
    r = _fn(file_system_tools.delete_file)(p, dry_run=True)
    assert r["dry_run"] and os.path.exists(p)
    r = _fn(file_system_tools.delete_file)(p, permanent=True)
    assert r["success"] and not os.path.exists(p) and list_trash_impl()["count"] == 0


def test_restore_refuses_clobber_and_bad_ids(temp_dir, trash):
    p = os.path.join(temp_dir, "f.txt")
    _write(p, "old")
    tid = _fn(file_system_tools.delete_file)(p)["trash_id"]
    _write(p, "new")
    assert not restore_from_trash_impl(tid)["success"]
    assert restore_from_trash_impl(tid, overwrite=True)["success"] and _read(p) == "old"
    assert not restore_from_trash_impl("../../etc")["success"]


def test_search_and_replace_dry_run(temp_dir):
    p = os.path.join(temp_dir, "f.txt")
    _write(p, "aaa")
    r = _fn(file_system_tools.search_and_replace_in_file)(p, "a", "b", dry_run=True)
    assert r["dry_run"] and r["matches_found"] == 3 and _read(p) == "aaa"


# ------------------------------------------------------------------ checkpoints

@needs_git
def test_checkpoint_roundtrip_including_untracked(repo):
    _write(os.path.join(repo, "a.txt"), "one\ntwo\nMODIFIED\n")       # tracked, modified
    _write(os.path.join(repo, "new.txt"), "untracked work\n")          # untracked
    status_before = _git(repo, "status", "--porcelain")
    cp = create_checkpoint_impl(repo, "before risky change")
    assert cp["success"]
    assert _git(repo, "status", "--porcelain") == status_before         # working tree/index untouched
    assert _git(repo, "stash", "list") == ""                            # stash list untouched
    assert list_checkpoints_impl(repo)["checkpoints"][0]["label"] == "before risky change"

    _write(os.path.join(repo, "a.txt"), "destroyed\n")
    os.remove(os.path.join(repo, "new.txt"))

    dry = restore_checkpoint_impl(cp["checkpoint_id"], repo, dry_run=True)
    assert dry["success"] and {c["path"] for c in dry["files_affected"]} == {"a.txt", "new.txt"}
    assert _read(os.path.join(repo, "a.txt")) == "destroyed\n"          # dry run changed nothing

    r = restore_checkpoint_impl(cp["checkpoint_id"], repo)
    assert r["success"] and r["undo_checkpoint"]
    # compare newline-insensitively: git may apply core.autocrlf when restoring files
    assert _read(os.path.join(repo, "a.txt")).replace("\r\n", "\n") == "one\ntwo\nMODIFIED\n"
    assert _read(os.path.join(repo, "new.txt")).replace("\r\n", "\n") == "untracked work\n"

    # the pre-restore state is itself recoverable
    undo = restore_checkpoint_impl(r["undo_checkpoint"], repo)
    assert undo["success"] and _read(os.path.join(repo, "a.txt")).replace("\r\n", "\n") == "destroyed\n"


@needs_git
def test_checkpoint_errors(temp_dir, repo):
    assert not restore_checkpoint_impl("does-not-exist", repo)["success"]
    assert not restore_checkpoint_impl("../bad", repo)["success"]
    not_a_repo = os.path.join(temp_dir, "plain")
    os.makedirs(not_a_repo)
    # temp_dir is itself the repo here, so use a genuinely separate directory
    import tempfile
    with tempfile.TemporaryDirectory() as outside:
        assert not create_checkpoint_impl(outside)["success"]


# ------------------------------------------------------------------ parsers

def test_parse_tsc():
    text = (
        "src/main/index.ts(12,5): error TS2322: Type 'string' is not assignable to type 'number'.\n"
        "  Type details continue here\n"
        "src\\renderer\\app.tsx(3,1): warning TS6133: 'x' is declared but never used.\n"
        "Found 2 errors.\n"
    )
    out = parse_tsc(text)
    assert len(out) == 2
    assert out[0]["file"] == "src/main/index.ts" and out[0]["line"] == 12 and out[0]["column"] == 5
    assert out[0]["code"] == "TS2322" and "continue here" in out[0]["message"]
    assert out[1]["file"] == "src/renderer/app.tsx" and out[1]["severity"] == "warning"


def test_parse_eslint():
    payload = json.dumps([{"filePath": "C:\\p\\a.ts", "messages": [
        {"ruleId": "no-unused-vars", "severity": 2, "message": "unused", "line": 4, "column": 7},
        {"ruleId": "semi", "severity": 1, "message": "missing", "line": 5, "column": 1},
    ]}, ])
    out = parse_eslint("npm warn noise\n" + payload)
    assert [(f["severity"], f["code"], f["line"]) for f in out] == [("error", "no-unused-vars", 4), ("warning", "semi", 5)]
    assert out[0]["file"] == "C:/p/a.ts"
    assert parse_eslint("no json here") == []


def test_parse_vitest():
    payload = json.dumps({"testResults": [{
        "name": "C:\\p\\src\\a.test.ts", "status": "failed",
        "assertionResults": [
            {"status": "passed", "fullName": "ok"},
            {"status": "failed", "fullName": "suite adds", "failureMessages": [
                "AssertionError: expected 1 to be 2\n    at C:/p/src/a.test.ts:10:15"]},
        ]}, {"name": "b.test.ts", "status": "failed", "assertionResults": [], "message": "import error"}]})
    out = parse_vitest("stdout noise\n" + payload)
    assert len(out) == 2
    assert out[0]["code"] == "suite adds" and out[0]["line"] == 10 and out[0]["column"] == 15
    assert out[1]["code"] == "suite-failed" and out[1]["message"] == "import error"


def test_parse_pytest_junit():
    xml = """<testsuites><testsuite>
      <testcase classname="tests.test_a" name="test_ok"/>
      <testcase classname="tests.test_a" name="test_bad">
        <failure message="assert 1 == 2">tests/test_a.py:7: AssertionError</failure>
      </testcase></testsuite></testsuites>"""
    out = parse_pytest_junit(xml)
    assert len(out) == 1
    assert out[0]["file"] == "tests/test_a.py" and out[0]["line"] == 7
    assert out[0]["code"] == "tests.test_a::test_bad"


# ------------------------------------------------------------------ hardening

def test_search_never_reads_secret_files(temp_dir):
    for rel in (".env", "server.pem", "id_rsa", ".npmrc", ".ssh/config", ".aws/credentials"):
        _write(os.path.join(temp_dir, *rel.split("/")), "needle")
    _write(os.path.join(temp_dir, ".env.example"), "needle")  # template: allowed
    _write(os.path.join(temp_dir, "app.ts"), "needle")
    # Most permissive options possible: match-everything glob, nothing excluded.
    r = search_files_impl("needle", temp_dir, glob=["**/*", ".env", "*.pem"], exclude_dirs=[])
    assert {m["path"] for m in r["matches"]} == {".env.example", "app.ts"}
    assert r["secret_files_skipped"] == 4  # .env, server.pem, id_rsa, .npmrc (the dirs are pruned)
    assert "files_only" not in r and "needle" not in json.dumps(
        [m for m in r["matches"] if m["path"] in (".env", "server.pem", "id_rsa", ".npmrc")])
    assert search_files_impl("needle", temp_dir, files_only=True)["files"] == [".env.example", "app.ts"]


def test_search_refuses_credential_directories(temp_dir):
    d = os.path.join(temp_dir, ".ssh")
    _write(os.path.join(d, "config"), "needle")
    assert not search_files_impl("needle", d)["success"]
    nested = os.path.join(temp_dir, ".aws", "sub")
    _write(os.path.join(nested, "f.txt"), "needle")
    assert not search_files_impl("needle", nested)["success"]


def test_move_path_blocks_renaming_into_disallowed_type(temp_dir):
    src = os.path.join(temp_dir, "notes.txt")
    _write(src, "data")
    for bad in ("payload.exe", "lib.dll"):
        r = move_path_impl(src, os.path.join(temp_dir, bad))
        assert not r["success"] and "extension" in r["error"]
        assert os.path.exists(src) and not os.path.exists(os.path.join(temp_dir, bad))
    assert not move_path_impl(src, os.path.join(temp_dir, "x.exe"), dry_run=True)["success"]
    assert move_path_impl(src, os.path.join(temp_dir, "notes.md"))["success"]  # allowed type is fine


def test_move_path_allows_same_extension_and_directories(temp_dir):
    odd = os.path.join(temp_dir, "tool.exe")
    _write(odd, "bin")
    # moving a file that already has this extension is fine; only *changing* into one is blocked
    assert move_path_impl(odd, os.path.join(temp_dir, "sub", "tool.exe"))["success"]
    d = os.path.join(temp_dir, "pkg")
    _write(os.path.join(d, "a.txt"), "x")
    assert move_path_impl(d, os.path.join(temp_dir, "pkg2"))["success"]
