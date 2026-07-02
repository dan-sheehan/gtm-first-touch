#!/usr/bin/env python3
"""Enrichment Chain — Multi-step company enrichment pipeline."""
from __future__ import annotations

import argparse
import json
import logging
import os
import signal
import socket
import sqlite3
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

from flask import Flask, Response, g, jsonify, render_template, request

logger = logging.getLogger(__name__)

APP_NAME = "enrichment"
DEFAULT_PORT = 3011
DATA_DIR = Path.home() / ".enrichment"
DB_PATH = DATA_DIR / "enrichment.db"
PID_PATH = DATA_DIR / "enrichment.pid"
ICP_DB_PATH = Path.home() / ".icp-scorer" / "icp_scorer.db"
BASE_DIR = Path(__file__).resolve().parent
PROVIDERS_PATH = BASE_DIR / "providers.json"
sys.path.insert(0, str(BASE_DIR.parent))

from ai_client import ai_complete  # noqa: E402


# ---------------------------------------------------------------------------
# Database helpers
# ---------------------------------------------------------------------------

def ensure_db() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.execute("""
        CREATE TABLE IF NOT EXISTS enrichments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            company TEXT NOT NULL,
            result TEXT NOT NULL DEFAULT '{}',
            steps_completed INTEGER NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()


def get_db() -> sqlite3.Connection:
    if "db" not in g:
        g.db = sqlite3.connect(str(DB_PATH))
        g.db.row_factory = sqlite3.Row
    return g.db


def close_db(exc: BaseException | None = None) -> None:
    db = g.pop("db", None)
    if db is not None:
        db.close()


def load_icp_accounts(limit: int = 20) -> list[dict[str, object]]:
    if not ICP_DB_PATH.exists():
        return []

    conn = sqlite3.connect(str(ICP_DB_PATH))
    conn.row_factory = sqlite3.Row
    try:
        rows = conn.execute(
            """
            SELECT id, company_name, dimensions, score, grade, created_at
            FROM scores
            ORDER BY created_at DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
    except sqlite3.Error:
        return []
    finally:
        conn.close()

    accounts = []
    for row in rows:
        try:
            dimensions = json.loads(row["dimensions"]) if row["dimensions"] else {}
        except json.JSONDecodeError:
            dimensions = {}
        accounts.append({
            "id": row["id"],
            "company_name": row["company_name"],
            "score": row["score"],
            "grade": row["grade"],
            "dimensions": dimensions,
            "created_at": row["created_at"],
        })
    return accounts


# ---------------------------------------------------------------------------
# Provider helpers
# ---------------------------------------------------------------------------

def load_providers() -> dict[str, object]:
    return json.loads(PROVIDERS_PATH.read_text())


def run_provider(
    provider: dict[str, object], company: str, context: dict[str, object]
) -> dict[str, object]:
    """Run a single enrichment provider via the configured AI provider.

    Returns parsed JSON result or error dict.
    """
    prompt = provider["prompt_template"].replace("{company}", company)
    if "{context}" in prompt:
        ctx_str = json.dumps(context, indent=2) if context else "{}"
        prompt = prompt.replace("{context}", ctx_str)

    ai_result = ai_complete(prompt, allow_web=True, timeout=120)
    if not ai_result.ok:
        logger.error("AI provider %s failed for provider %s: %s", ai_result.provider, provider.get("id"), ai_result.error)
        return {"error": ai_result.error}

    output = ai_result.text.strip()
    json_start = output.find("{")
    json_end = output.rfind("}") + 1
    if json_start >= 0 and json_end > json_start:
        try:
            return json.loads(output[json_start:json_end])
        except json.JSONDecodeError:
            logger.error("Failed to parse JSON from provider %s for company %s", provider.get("id"), company)
    return {"raw": output}


# ---------------------------------------------------------------------------
# Flask application
# ---------------------------------------------------------------------------

def create_app(prefix: str = "") -> Flask:
    static_path = prefix + "/static" if prefix else "/static"
    app = Flask(
        __name__,
        static_folder=str(BASE_DIR / "static"),
        static_url_path=static_path,
        template_folder=str(BASE_DIR / "templates"),
    )
    app.config["URL_PREFIX"] = prefix
    app.teardown_appcontext(close_db)

    @app.context_processor
    def inject_prefix() -> dict[str, str]:
        return {"prefix": app.config["URL_PREFIX"]}

    @app.route(prefix + "/")
    def index():
        return render_template("index.html")

    @app.route(prefix + "/api/providers", methods=["GET"])
    def api_providers():
        return jsonify(load_providers())

    @app.route(prefix + "/api/icp-accounts", methods=["GET"])
    @app.route("/api/icp-accounts", methods=["GET"])
    def api_icp_accounts():
        return jsonify({"accounts": load_icp_accounts()})

    @app.route(prefix + "/api/enrich", methods=["POST"])
    def api_enrich():
        data = request.get_json(silent=True) or {}
        company = data.get("company", "").strip()
        dry_run = data.get("dry_run", False)

        if not company:
            return jsonify({"error": "Company name is required"}), 400

        providers_config = load_providers()
        providers = providers_config.get("providers", [])

        if dry_run:
            prompts = []
            ctx = {}
            for prov in providers:
                prompt = prov["prompt_template"].replace("{company}", company)
                if "{context}" in prompt:
                    prompt = prompt.replace("{context}", json.dumps(ctx, indent=2))
                prompts.append({
                    "provider": prov["id"],
                    "label": prov["label"],
                    "prompt": prompt,
                })
                ctx[prov["id"]] = {"placeholder": "result would go here"}
            return jsonify({"prompts": prompts})

        def generate():
            context = {}
            steps_done = 0

            logger.info("Starting enrichment for %s (%d providers)", company, len(providers))
            for prov in providers:
                label = prov["label"]
                step_id = prov["id"]
                yield f"data: {json.dumps({'status': f'Running {label}...', 'step': step_id})}\n\n"

                result = run_provider(prov, company, context)
                context[prov["id"]] = result
                steps_done += 1

                yield f"data: {json.dumps({'step_done': prov['id'], 'label': prov['label'], 'result': result})}\n\n"

            # Save to database
            now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")
            db_conn = sqlite3.connect(str(DB_PATH))
            cur = db_conn.execute(
                "INSERT INTO enrichments (company, result, steps_completed, created_at) VALUES (?, ?, ?, ?)",
                (company, json.dumps(context), steps_done, now),
            )
            db_conn.commit()
            enrichment_id = cur.lastrowid
            db_conn.close()

            yield f"data: {json.dumps({'done': True, 'id': enrichment_id, 'result': context})}\n\n"

        return Response(generate(), content_type="text/event-stream")

    @app.route(prefix + "/api/enrichments", methods=["GET"])
    def api_enrichments():
        db = get_db()
        rows = db.execute(
            "SELECT id, company, steps_completed, created_at FROM enrichments ORDER BY created_at DESC LIMIT 50"
        ).fetchall()
        return jsonify({"enrichments": [dict(r) for r in rows]})

    @app.route(prefix + "/api/enrichments/<int:enrich_id>", methods=["GET"])
    def api_enrichment_detail(enrich_id):
        db = get_db()
        row = db.execute("SELECT * FROM enrichments WHERE id = ?", (enrich_id,)).fetchone()
        if not row:
            return jsonify({"error": "Not found"}), 404
        result = dict(row)
        result["result"] = json.loads(result["result"])
        return jsonify(result)

    @app.route(prefix + "/api/enrichments/<int:enrich_id>", methods=["DELETE"])
    def api_enrichment_delete(enrich_id):
        db = get_db()
        db.execute("DELETE FROM enrichments WHERE id = ?", (enrich_id,))
        db.commit()
        return jsonify({"status": "deleted"})

    @app.route(prefix + "/api/seed", methods=["POST"])
    @app.route("/api/seed", methods=["POST"])
    def api_seed():
        seed_file = BASE_DIR / "sample_data.json"
        if not seed_file.exists():
            return jsonify({"error": "Sample data file not found"}), 404
        ensure_db()
        data = request.get_json(silent=True) or {}
        force = bool(data.get("force"))
        db = get_db()
        existing = db.execute("SELECT COUNT(*) FROM enrichments").fetchone()[0]
        if existing > 0 and not force:
            return jsonify({
                "status": "skipped",
                "count": 0,
                "existing": existing,
                "message": "already seeded",
            })
        if force:
            db.execute("DELETE FROM enrichments")
        seed_data = json.loads(seed_file.read_text())
        now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")
        for item in seed_data:
            db.execute(
                "INSERT INTO enrichments (company, result, steps_completed, created_at) VALUES (?, ?, ?, ?)",
                (item["company"], json.dumps(item["result"]), item["steps_completed"], now),
            )
        db.commit()
        return jsonify({"status": "seeded", "count": len(seed_data), "cleared": existing if force else 0})

    return app


# ---------------------------------------------------------------------------
# Server lifecycle CLI
# ---------------------------------------------------------------------------

def is_port_in_use(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(0.2)
        return sock.connect_ex(("127.0.0.1", port)) == 0


def wait_for_port(port: int, timeout: float = 2.0) -> bool:
    start = time.time()
    while time.time() - start < timeout:
        if is_port_in_use(port):
            return True
        time.sleep(0.1)
    return False


def read_pid() -> int | None:
    if not PID_PATH.exists():
        return None
    try:
        return int(PID_PATH.read_text().strip())
    except ValueError:
        return None


def is_process_running(pid: int | None) -> bool:
    if pid is None:
        return False
    try:
        os.kill(pid, 0)
    except OSError:
        return False
    return True


def command_start(args: argparse.Namespace) -> int:
    ensure_db()
    if PID_PATH.exists():
        pid = read_pid()
        if pid and is_process_running(pid):
            print(f"Enrichment already running (PID {pid}).")
            return 0
        PID_PATH.unlink(missing_ok=True)

    port = args.port or DEFAULT_PORT
    if is_port_in_use(port):
        print(f"Port {port} is in use.")
        return 1

    cmd = [sys.executable, str(Path(__file__).resolve()), "serve", "--port", str(port)]
    if args.prefix:
        cmd += ["--prefix", args.prefix]
    process = subprocess.Popen(
        cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True,
    )
    PID_PATH.write_text(str(process.pid))
    wait_for_port(port)
    print(f"Enrichment running at http://localhost:{port}")
    return 0


def command_stop(_args: argparse.Namespace) -> int:
    pid = read_pid()
    if not pid or not is_process_running(pid):
        print("Enrichment is not running.")
        PID_PATH.unlink(missing_ok=True)
        return 0
    try:
        os.kill(pid, signal.SIGTERM)
    except OSError:
        print("Unable to stop Enrichment.")
        return 1
    PID_PATH.unlink(missing_ok=True)
    print("Enrichment stopped.")
    return 0


def command_status(_args: argparse.Namespace) -> int:
    pid = read_pid()
    if pid and is_process_running(pid):
        print(f"Enrichment running (PID {pid}).")
        return 0
    print("Enrichment is not running.")
    return 1


def command_serve(args: argparse.Namespace) -> int:
    logging.basicConfig(format="%(asctime)s %(name)s %(levelname)s %(message)s", level=logging.INFO)
    ensure_db()
    prefix = getattr(args, "prefix", "") or ""
    app = create_app(prefix=prefix)
    port = args.port or DEFAULT_PORT
    app.run(host="127.0.0.1", port=port, debug=False)
    return 0


# ---------------------------------------------------------------------------
# Argument parser
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog=APP_NAME)
    subparsers = parser.add_subparsers(dest="command")

    start_p = subparsers.add_parser("start")
    start_p.add_argument("--port", type=int, default=None)
    start_p.add_argument("--prefix", type=str, default="")

    subparsers.add_parser("stop")
    subparsers.add_parser("status")

    serve_p = subparsers.add_parser("serve")
    serve_p.add_argument("--port", type=int, default=None)
    serve_p.add_argument("--prefix", type=str, default="")

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    commands = {
        "start": command_start,
        "stop": command_stop,
        "status": command_status,
        "serve": command_serve,
    }

    handler = commands.get(args.command)
    if handler:
        return handler(args)

    parser.print_help()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
