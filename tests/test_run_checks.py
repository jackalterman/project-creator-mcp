import os
import shutil

import pytest

from src.mcp_tools.check_tools import run_checks_impl


def _write(path, text):
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)


def test_run_checks_pytest_end_to_end(temp_dir):
    _write(os.path.join(temp_dir, "test_sample.py"),
           "def test_ok():\n    assert True\n\n\ndef test_bad():\n    assert 1 == 2\n")
    r = run_checks_impl("pytest", cwd=temp_dir, timeout=120)
    assert r["success"], r
    assert r["passed"] is False and r["error_count"] == 1
    failure = r["failures"][0]
    assert failure["file"].endswith("test_sample.py")
    assert failure["line"] == 6
    assert "test_bad" in failure["code"]


def test_run_checks_pytest_passing(temp_dir):
    _write(os.path.join(temp_dir, "test_sample.py"), "def test_ok():\n    assert True\n")
    r = run_checks_impl("pytest", cwd=temp_dir, timeout=120)
    assert r["success"] and r["passed"] and r["error_count"] == 0 and r["failures"] == []


@pytest.mark.skipif(shutil.which("npx") is None, reason="npx not installed")
def test_run_checks_never_installs_missing_tools(temp_dir):
    # Empty project: typescript is not installed. Must fail fast instead of
    # letting npx download some unrelated package named 'tsc'.
    r = run_checks_impl("tsc", cwd=temp_dir, timeout=60)
    assert r["success"] and r["passed"] is False
    assert "--no-install" in r["command"]
    assert "will be installed" not in r.get("raw_output_tail", "")
    assert "\x1b[" not in r.get("raw_output_tail", "")  # ANSI colors stripped


def test_run_checks_rejects_bad_input(temp_dir):
    assert not run_checks_impl("make", cwd=temp_dir)["success"]
    assert not run_checks_impl("pytest", cwd=temp_dir, args="-x && del file")["success"]
    assert not run_checks_impl("pytest", cwd=os.path.join(temp_dir, "missing"))["success"]
