"""Run tsc / eslint / vitest / pytest and return parsed failures instead of terminal walls."""

import json
import os
import re
import shlex
import tempfile
import xml.etree.ElementTree as ET
from typing import Any, Dict, List, Optional

from .security import is_safe_path
from .command_execution_tools import run_command_with_timeout, create_safe_env
from .mcp_instance import mcp

MAX_FAILURES = 200
_ANSI = re.compile(r"\x1b\[[0-9;]*m")
SUPPORTED_TOOLS = ["tsc", "eslint", "vitest", "pytest"]
_UNSAFE = re.compile(r"[;&|`\n\r]|\$\(")


# ---------------------------------------------------------------- parsers

_TSC_LINE = re.compile(r"^(?P<file>.+?)\((?P<line>\d+),(?P<col>\d+)\):\s+(?P<sev>error|warning)\s+(?P<code>TS\d+):\s+(?P<msg>.*)$")


def parse_tsc(text: str) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    for raw in text.splitlines():
        m = _TSC_LINE.match(raw.strip())
        if m:
            out.append({"file": m["file"].replace("\\", "/"), "line": int(m["line"]),
                        "column": int(m["col"]), "severity": m["sev"], "code": m["code"],
                        "message": m["msg"]})
        elif out and raw.startswith(("  ", "\t")) and raw.strip():
            out[-1]["message"] += "\n" + raw.strip()  # continuation lines of a multi-line error
    return out


def parse_eslint(text: str) -> List[Dict[str, Any]]:
    start = text.find("[")
    if start < 0:
        return []
    data = json.loads(text[start:])
    out: List[Dict[str, Any]] = []
    for f in data:
        for m in f.get("messages", []):
            out.append({"file": f.get("filePath", "").replace("\\", "/"),
                        "line": m.get("line"), "column": m.get("column"),
                        "severity": "error" if m.get("severity") == 2 else "warning",
                        "code": m.get("ruleId"), "message": m.get("message", "")})
    return out


_LOC = re.compile(r"([\w@./\\:-]+\.(?:[cm]?[jt]sx?|py)):(\d+)(?::(\d+))?")


def parse_vitest(text: str) -> List[Dict[str, Any]]:
    start = text.find("{")
    if start < 0:
        return []
    data = json.loads(text[start:text.rfind("}") + 1])
    out: List[Dict[str, Any]] = []
    for suite in data.get("testResults", []):
        file = suite.get("name", "").replace("\\", "/")
        if suite.get("status") == "failed" and not suite.get("assertionResults"):
            out.append({"file": file, "line": None, "column": None, "severity": "error",
                        "code": "suite-failed", "message": suite.get("message", "Test suite failed to run")})
        for t in suite.get("assertionResults", []):
            if t.get("status") != "failed":
                continue
            msgs = "\n".join(t.get("failureMessages", []))
            line = col = None
            for m in _LOC.finditer(msgs):
                if os.path.basename(m[1].replace("\\", "/")) == os.path.basename(file):
                    line, col = int(m[2]), int(m[3]) if m[3] else None
                    break
            loc = t.get("location") or {}
            out.append({"file": file, "line": loc.get("line", line), "column": loc.get("column", col),
                        "severity": "error", "code": t.get("fullName") or t.get("title"),
                        "message": msgs.strip()[:1500]})
    return out


def parse_pytest_junit(xml_text: str) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    root = ET.fromstring(xml_text)
    for case in root.iter("testcase"):
        for kind in ("failure", "error"):
            node = case.find(kind)
            if node is None:
                continue
            body = (node.get("message") or "") + "\n" + (node.text or "")
            file = case.get("file") or case.get("classname", "").replace(".", "/") + ".py"
            line = int(case.get("line")) if (case.get("line") or "").isdigit() else None
            for m in _LOC.finditer(node.text or ""):
                if m[1].endswith(".py"):
                    file, line = m[1].replace("\\", "/"), int(m[2])
            out.append({"file": file, "line": line, "column": None, "severity": "error",
                        "code": f"{case.get('classname', '')}::{case.get('name', '')}",
                        "message": body.strip()[:1500]})
    return out


# ---------------------------------------------------------------- runner

def _split_args(args: str) -> List[str]:
    return shlex.split(args, posix=False) if args else []


def run_checks_impl(tool: str, cwd: str = ".", args: str = "", timeout: int = 180) -> Dict[str, Any]:
    ok, message = is_safe_path(cwd)
    if not ok:
        return {"success": False, "error": f"Working directory blocked: {message}"}
    if not os.path.isdir(cwd):
        return {"success": False, "error": f"Working directory does not exist: {cwd}"}
    if tool not in SUPPORTED_TOOLS:
        return {"success": False, "error": f"Unsupported tool: {tool}", "supported_tools": SUPPORTED_TOOLS}
    if args and _UNSAFE.search(args):
        return {"success": False, "error": "args contains unsafe characters (chaining operators)"}
    timeout = max(10, min(int(timeout), 900))
    extra = " ".join(_split_args(args))
    junit_path: Optional[str] = None

    if tool == "tsc":
        cmd = f"npx --no-install tsc --noEmit --pretty false {extra}".strip()
    elif tool == "eslint":
        cmd = f"npx --no-install eslint --format json {extra or '.'}".strip()
    elif tool == "vitest":
        cmd = f"npx --no-install vitest run --reporter=json {extra}".strip()
    else:
        fd, junit_path = tempfile.mkstemp(suffix=".xml", prefix="mcp-junit-")
        os.close(fd)
        cmd = f'python -m pytest -q -p no:cacheprovider --junitxml="{junit_path}" {extra}'.strip()

    try:
        result = run_command_with_timeout(cmd, shell=True, cwd=cwd, timeout=timeout, env=create_safe_env())
        stdout, stderr = result["stdout"] or "", result["stderr"] or ""
        if result["timed_out"]:
            return {"success": False, "tool": tool, "command": cmd, "timed_out": True,
                    "error": f"Timed out after {timeout}s"}

        parse_error = None
        try:
            if tool == "tsc":
                failures = parse_tsc(stdout + "\n" + stderr)
            elif tool == "eslint":
                failures = parse_eslint(stdout)
            elif tool == "vitest":
                failures = parse_vitest(stdout or stderr)
            else:
                with open(junit_path, "r", encoding="utf-8") as f:
                    failures = parse_pytest_junit(f.read())
        except Exception as e:  # parser problems must not hide the real output
            failures, parse_error = [], f"Could not parse {tool} output: {e}"

        errors = [f for f in failures if f["severity"] == "error"]
        warnings = [f for f in failures if f["severity"] == "warning"]
        response: Dict[str, Any] = {
            "success": True, "tool": tool, "command": cmd, "exit_code": result["returncode"],
            "passed": result["returncode"] == 0 and not errors,
            "error_count": len(errors), "warning_count": len(warnings),
            "failures": failures[:MAX_FAILURES], "truncated": len(failures) > MAX_FAILURES,
            "timed_out": False,
        }
        # Non-zero exit with nothing parsed means the tool itself broke (missing, bad config...)
        if parse_error or (result["returncode"] != 0 and not failures):
            response["parse_error"] = parse_error
            response["raw_output_tail"] = _ANSI.sub("", stdout + "\n" + stderr).strip()[-3000:]
        return response
    except Exception as e:
        return {"success": False, "error": f"Failed to run {tool}: {e}"}
    finally:
        if junit_path and os.path.exists(junit_path):
            os.remove(junit_path)


@mcp.tool()
def run_checks(tool: str, cwd: str = ".", args: str = "", timeout: int = 180) -> Dict[str, Any]:
    """
    Run a type-checker, linter or test runner and get back a PARSED list of failures
    (file, line, column, code, message) instead of raw terminal output.

    Args:
        tool: One of "tsc", "eslint", "vitest", "pytest"
        cwd: Project directory to run in (default: current directory)
        args: Extra arguments, e.g. "src/main" for eslint or "tests/test_x.py -k name" for pytest
        timeout: Seconds before the run is killed (default: 180, max: 900)

    Returns:
        Dictionary with passed, error_count, warning_count and failures[]. If the tool
        itself fails to run, raw_output_tail is included for diagnosis.
    """
    return run_checks_impl(tool, cwd, args, timeout)
