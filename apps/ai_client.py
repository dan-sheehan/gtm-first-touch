"""Small model-provider adapter for AI-powered GTM tools.

The apps stay dependency-light by using stdlib subprocess/HTTP only. Provider is
selected with GTM_AI_PROVIDER:
  - claude_cli (default): local Claude CLI, prompt via `claude -p`
  - openai: OpenAI-compatible chat completions endpoint
  - anthropic: Anthropic messages endpoint
  - command: any local command that reads the full prompt from stdin
"""
from __future__ import annotations

from dataclasses import dataclass
import json
import os
import shlex
import shutil
import subprocess
import urllib.error
import urllib.request


@dataclass
class AIResult:
    ok: bool
    text: str = ""
    error: str = ""
    provider: str = ""


def ai_complete(
    prompt: str,
    *,
    system_prompt: str | None = None,
    allow_web: bool = False,
    timeout: int = 120,
) -> AIResult:
    provider = os.environ.get("GTM_AI_PROVIDER", "claude_cli").strip().lower()

    if provider in ("claude", "claude_cli"):
        return _claude_cli_complete(prompt, system_prompt=system_prompt, allow_web=allow_web, timeout=timeout)
    if provider in ("openai", "openai_compatible"):
        return _openai_compatible_complete(prompt, system_prompt=system_prompt, timeout=timeout)
    if provider == "anthropic":
        return _anthropic_complete(prompt, system_prompt=system_prompt, timeout=timeout)
    if provider == "command":
        return _command_complete(prompt, system_prompt=system_prompt, timeout=timeout)

    return AIResult(
        ok=False,
        provider=provider,
        error=(
            f"Unsupported GTM_AI_PROVIDER '{provider}'. "
            "Use claude_cli, openai, anthropic, or command."
        ),
    )


def _join_prompt(prompt: str, system_prompt: str | None) -> str:
    if system_prompt:
        return system_prompt + "\n\n" + prompt
    return prompt


def _claude_cli_complete(
    prompt: str,
    *,
    system_prompt: str | None,
    allow_web: bool,
    timeout: int,
) -> AIResult:
    claude_bin = shutil.which("claude")
    if not claude_bin:
        return AIResult(
            ok=False,
            provider="claude_cli",
            error=(
                "Claude CLI not found. Install Claude Code, or set "
                "GTM_AI_PROVIDER=openai, anthropic, or command."
            ),
        )

    cmd = [claude_bin, "-p", _join_prompt(prompt, system_prompt), "--output-format", "text"]
    model = os.environ.get("GTM_AI_MODEL") or os.environ.get("CLAUDE_MODEL")
    if model:
        cmd += ["--model", model]
    if allow_web:
        cmd += ["--allowedTools", "WebSearch,WebFetch"]

    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            env={k: v for k, v in os.environ.items() if k != "CLAUDECODE"},
            cwd=os.path.expanduser("~"),
            stdin=subprocess.DEVNULL,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        return AIResult(ok=False, provider="claude_cli", error=f"AI request timed out after {timeout} seconds.")

    if proc.returncode != 0:
        err = proc.stderr.strip() or proc.stdout.strip() or "(no output)"
        return AIResult(ok=False, provider="claude_cli", error=f"Claude CLI error (exit {proc.returncode}): {err}")
    if not proc.stdout.strip():
        return AIResult(ok=False, provider="claude_cli", error="No output from Claude CLI.")
    return AIResult(ok=True, text=proc.stdout, provider="claude_cli")


def _openai_compatible_complete(prompt: str, *, system_prompt: str | None, timeout: int) -> AIResult:
    api_key = os.environ.get("OPENAI_API_KEY") or os.environ.get("GTM_AI_API_KEY")
    if not api_key:
        return AIResult(ok=False, provider="openai", error="OPENAI_API_KEY or GTM_AI_API_KEY is required.")

    model = os.environ.get("GTM_AI_MODEL") or os.environ.get("OPENAI_MODEL")
    if not model:
        return AIResult(ok=False, provider="openai", error="GTM_AI_MODEL or OPENAI_MODEL is required.")

    base_url = os.environ.get("GTM_AI_BASE_URL", "https://api.openai.com/v1").rstrip("/")
    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})

    payload = json.dumps({"model": model, "messages": messages}).encode("utf-8")
    req = urllib.request.Request(
        f"{base_url}/chat/completions",
        data=payload,
        method="POST",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
    )
    ok, response = _json_request(req, timeout=timeout, provider="openai")
    if not ok:
        return response

    try:
        text = response["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError):
        return AIResult(ok=False, provider="openai", error="OpenAI-compatible response did not include content.")
    return AIResult(ok=True, text=text, provider="openai")


def _anthropic_complete(prompt: str, *, system_prompt: str | None, timeout: int) -> AIResult:
    api_key = os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("GTM_AI_API_KEY")
    if not api_key:
        return AIResult(ok=False, provider="anthropic", error="ANTHROPIC_API_KEY or GTM_AI_API_KEY is required.")

    model = os.environ.get("GTM_AI_MODEL") or os.environ.get("ANTHROPIC_MODEL")
    if not model:
        return AIResult(ok=False, provider="anthropic", error="GTM_AI_MODEL or ANTHROPIC_MODEL is required.")

    max_tokens = int(os.environ.get("GTM_AI_MAX_TOKENS", "4096"))
    payload_data = {
        "model": model,
        "max_tokens": max_tokens,
        "messages": [{"role": "user", "content": prompt}],
    }
    if system_prompt:
        payload_data["system"] = system_prompt

    payload = json.dumps(payload_data).encode("utf-8")
    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages",
        data=payload,
        method="POST",
        headers={
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json",
        },
    )
    ok, response = _json_request(req, timeout=timeout, provider="anthropic")
    if not ok:
        return response

    try:
        text = "\n".join(block.get("text", "") for block in response["content"] if block.get("type") == "text")
    except (KeyError, TypeError):
        return AIResult(ok=False, provider="anthropic", error="Anthropic response did not include text content.")
    if not text.strip():
        return AIResult(ok=False, provider="anthropic", error="Anthropic response was empty.")
    return AIResult(ok=True, text=text, provider="anthropic")


def _command_complete(prompt: str, *, system_prompt: str | None, timeout: int) -> AIResult:
    command = os.environ.get("GTM_AI_COMMAND", "").strip()
    if not command:
        return AIResult(ok=False, provider="command", error="GTM_AI_COMMAND is required for command provider.")

    try:
        proc = subprocess.run(
            shlex.split(command),
            input=_join_prompt(prompt, system_prompt),
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except (OSError, ValueError) as exc:
        return AIResult(ok=False, provider="command", error=f"Command provider failed to start: {exc}")
    except subprocess.TimeoutExpired:
        return AIResult(ok=False, provider="command", error=f"AI command timed out after {timeout} seconds.")

    if proc.returncode != 0:
        err = proc.stderr.strip() or proc.stdout.strip() or "(no output)"
        return AIResult(ok=False, provider="command", error=f"AI command exited {proc.returncode}: {err}")
    if not proc.stdout.strip():
        return AIResult(ok=False, provider="command", error="AI command returned no output.")
    return AIResult(ok=True, text=proc.stdout, provider="command")


def _json_request(
    req: urllib.request.Request,
    *,
    timeout: int,
    provider: str,
) -> tuple[bool, dict[str, object] | AIResult]:
    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
            raw = response.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        return False, AIResult(ok=False, provider=provider, error=f"{provider} HTTP {exc.code}: {detail}")
    except urllib.error.URLError as exc:
        return False, AIResult(ok=False, provider=provider, error=f"{provider} request failed: {exc}")

    try:
        return True, json.loads(raw)
    except json.JSONDecodeError:
        return False, AIResult(ok=False, provider=provider, error=f"{provider} returned invalid JSON.")
