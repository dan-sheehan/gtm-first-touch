#!/usr/bin/env python3
"""Plain-English setup checks for GTM First Touch."""
from __future__ import annotations

import importlib.metadata
import os
from pathlib import Path
import re
import shlex
import shutil
import socket
import sys


ROOT = Path(__file__).resolve().parents[1]
MIN_PYTHON = (3, 10)

APP_FILES = [
    ("ICP Scorer", ROOT / "apps" / "icp-scorer" / "icp_scorer.py"),
    ("Enrichment", ROOT / "apps" / "enrichment" / "enrichment.py"),
    ("Outbound Email", ROOT / "apps" / "outbound-email" / "outbound_email.py"),
    ("Discovery Call Prep", ROOT / "apps" / "discovery" / "discovery.py"),
]

PORTS = [
    (8000, "hub gateway"),
    (3005, "Discovery Call Prep"),
    (3008, "Outbound Email"),
    (3011, "Enrichment"),
    (3012, "ICP Scorer"),
]

PROVIDERS = {
    "claude": "claude_cli",
    "claude_cli": "claude_cli",
    "openai": "openai",
    "openai_compatible": "openai",
    "anthropic": "anthropic",
    "command": "command",
}


class Reporter:
    def __init__(self) -> None:
        self.failures = 0
        self.warnings = 0

    def ok(self, message: str) -> None:
        print(f"PASS  {message}")

    def warn(self, message: str) -> None:
        self.warnings += 1
        print(f"WARN  {message}")

    def fail(self, message: str) -> None:
        self.failures += 1
        print(f"FAIL  {message}")


def requirement_name(line: str) -> str | None:
    cleaned = line.split("#", 1)[0].strip()
    if not cleaned or cleaned.startswith("-"):
        return None
    return re.split(r"[<>=!~;\[]", cleaned, maxsplit=1)[0].strip()


def check_python(reporter: Reporter) -> None:
    version = sys.version_info
    version_text = f"{version.major}.{version.minor}.{version.micro}"
    if (version.major, version.minor) >= MIN_PYTHON:
        reporter.ok(f"Python {version_text} is usable.")
    else:
        reporter.fail(
            f"Python {version_text} is too old. Use Python {MIN_PYTHON[0]}.{MIN_PYTHON[1]} or newer."
        )


def check_packages(reporter: Reporter) -> None:
    requirements = ROOT / "requirements.txt"
    if not requirements.exists():
        reporter.fail("requirements.txt is missing. Re-download this folder before running the apps.")
        return

    names = []
    for line in requirements.read_text().splitlines():
        name = requirement_name(line)
        if name:
            names.append(name)

    if not names:
        reporter.warn("requirements.txt has no package entries.")
        return

    for name in names:
        try:
            installed = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            reporter.fail(f"Python package {name} is missing. Run `make install`.")
            continue
        reporter.ok(f"Python package {name} is installed ({installed}).")


def check_app_files(reporter: Reporter) -> None:
    for label, path in APP_FILES:
        if path.exists():
            reporter.ok(f"{label} app file exists.")
        else:
            reporter.fail(f"{label} app file is missing at {path.relative_to(ROOT)}.")


def port_is_open(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(0.2)
        return sock.connect_ex(("127.0.0.1", port)) == 0


def check_ports(reporter: Reporter) -> None:
    for port, label in PORTS:
        if port_is_open(port):
            reporter.warn(
                f"Port {port} for {label} is already in use. If the hub is running, this is expected; "
                "otherwise run `./hub stop` or close the process before `make start`."
            )
        else:
            reporter.ok(f"Port {port} for {label} is available.")


def first_present(names: tuple[str, ...]) -> str | None:
    for name in names:
        if os.environ.get(name):
            return name
    return None


def check_required_env(reporter: Reporter, names: tuple[str, ...], label: str) -> bool:
    present = first_present(names)
    if present:
        reporter.ok(f"{label} is set via {present}.")
        return True
    reporter.fail(f"{label} is missing. Set one of: {', '.join(names)}.")
    return False


def check_command_provider(reporter: Reporter) -> None:
    command = os.environ.get("GTM_AI_COMMAND", "").strip()
    if not command:
        reporter.fail("GTM_AI_COMMAND is missing for the command provider.")
        return

    try:
        parts = shlex.split(command)
    except ValueError as exc:
        reporter.fail(f"GTM_AI_COMMAND could not be parsed: {exc}.")
        return

    if not parts:
        reporter.fail("GTM_AI_COMMAND is empty after parsing.")
        return

    executable = shutil.which(parts[0])
    if executable:
        reporter.ok(f"GTM_AI_COMMAND is set and starts with {executable}.")
    else:
        reporter.fail(
            f"GTM_AI_COMMAND starts with `{parts[0]}`, but that executable was not found on PATH."
        )


def check_provider(reporter: Reporter) -> None:
    raw_provider = os.environ.get("GTM_AI_PROVIDER", "claude_cli").strip().lower() or "claude_cli"
    provider = PROVIDERS.get(raw_provider)
    if not provider:
        reporter.fail(
            f"GTM_AI_PROVIDER is `{raw_provider}`. Use claude_cli, openai, anthropic, or command."
        )
        return

    if raw_provider == provider:
        reporter.ok(f"GTM_AI_PROVIDER is {provider}.")
    else:
        reporter.ok(f"GTM_AI_PROVIDER is {raw_provider}, which maps to {provider}.")

    if provider == "claude_cli":
        claude_path = shutil.which("claude")
        if claude_path:
            reporter.ok(f"Claude CLI is available at {claude_path}.")
        else:
            reporter.fail(
                "Claude CLI was not found on PATH. Install/authenticate Claude CLI, "
                "or set GTM_AI_PROVIDER to openai, anthropic, or command."
            )
    elif provider == "openai":
        check_required_env(reporter, ("OPENAI_API_KEY", "GTM_AI_API_KEY"), "OpenAI API key")
        check_required_env(reporter, ("GTM_AI_MODEL", "OPENAI_MODEL"), "OpenAI model")
    elif provider == "anthropic":
        check_required_env(reporter, ("ANTHROPIC_API_KEY", "GTM_AI_API_KEY"), "Anthropic API key")
        check_required_env(reporter, ("GTM_AI_MODEL", "ANTHROPIC_MODEL"), "Anthropic model")
    elif provider == "command":
        check_command_provider(reporter)


def run() -> int:
    reporter = Reporter()
    print("GTM First Touch doctor")
    print("")

    check_python(reporter)
    check_packages(reporter)
    check_app_files(reporter)
    check_ports(reporter)
    check_provider(reporter)

    print("")
    if reporter.failures:
        print("Doctor found setup blockers. Fix the FAIL items above, then rerun `make doctor`.")
        return 1
    if reporter.warnings:
        print("Doctor passed with warnings. Review the WARN items before starting a fresh hub.")
        return 0
    print("All checks passed. Next: run `make start`, then `make reseed` in a second terminal.")
    return 0


def main() -> int:
    try:
        return run()
    except Exception as exc:
        print("FAIL  Doctor hit an unexpected setup check problem.")
        print(f"      {exc}")
        print("      Try `make install`, then rerun `make doctor`.")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
