#!/usr/bin/env python3
import argparse
import json
import os
import re
import signal
import socket
import subprocess
import sys
import time
from pathlib import Path

import sqlite3
import threading
from flask import Flask, Response, jsonify, render_template, request, g

_researching = threading.Lock()

APP_NAME = "discovery"
DEFAULT_PORT = 3005
DATA_DIR = Path.home() / ".discovery"
DB_PATH = DATA_DIR / "discovery.db"
PID_PATH = DATA_DIR / "discovery.pid"
CONFIG_PATH = DATA_DIR / "config.json"
BASE_DIR = Path(__file__).resolve().parent
REPO_ROOT = BASE_DIR.parent.parent
sys.path.insert(0, str(BASE_DIR.parent))

from ai_client import ai_complete  # noqa: E402


# ---------------------------------------------------------------------------
# Data directory & config
# ---------------------------------------------------------------------------

def ensure_data_dir():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    config = {}
    if CONFIG_PATH.exists():
        try:
            config = json.loads(CONFIG_PATH.read_text())
        except json.JSONDecodeError:
            config = {}
    config.setdefault("port", DEFAULT_PORT)
    config["app_root"] = str(BASE_DIR)
    CONFIG_PATH.write_text(json.dumps(config, indent=2))


# ---------------------------------------------------------------------------
# Database helpers
# ---------------------------------------------------------------------------

def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
    return g.db


def close_db(_exc=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS preps (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    company_url     TEXT NOT NULL,
    company_name    TEXT,
    prospect_name   TEXT NOT NULL,
    selling_as      TEXT,
    company_bullets TEXT,
    prospect_data   TEXT,
    raw_markdown    TEXT,
    created_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);
"""


def init_db(conn):
    conn.executescript(SCHEMA_SQL)
    conn.commit()


def ensure_db():
    ensure_data_dir()
    conn = sqlite3.connect(DB_PATH)
    try:
        init_db(conn)
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Company context loader
# ---------------------------------------------------------------------------

MAX_CONTEXT_CHARS = 10000

def load_company_context(company_key):
    """Load markdown files from projects/<company_key>/ as context."""
    projects_dir = REPO_ROOT / "data" / "contexts" / company_key
    if not projects_dir.is_dir():
        return ""

    chunks = []
    total = 0
    # Prioritize overview/summary files
    priority = ["overview", "summary", "about"]
    md_files = sorted(projects_dir.rglob("*.md"))

    def sort_key(p):
        name = p.stem.lower()
        for i, kw in enumerate(priority):
            if kw in name:
                return (0, i, str(p))
        return (1, 0, str(p))

    md_files.sort(key=sort_key)

    for f in md_files:
        if total >= MAX_CONTEXT_CHARS:
            break
        try:
            text = f.read_text()
        except Exception:
            continue
        if len(text) > 50000:
            continue
        remaining = MAX_CONTEXT_CHARS - total
        chunk = text[:remaining]
        chunks.append(f"## {f.name}\n{chunk}")
        total += len(chunk)

    return "\n\n".join(chunks)


def list_company_contexts():
    """Scan projects/ for directories that could be company contexts."""
    projects_dir = REPO_ROOT / "data" / "contexts"
    if not projects_dir.is_dir():
        return []
    results = []
    for d in sorted(projects_dir.iterdir()):
        if d.is_dir() and not d.name.startswith("."):
            # Only include dirs that have markdown files
            if any(d.rglob("*.md")):
                name = d.name.replace("-", " ").title()
                results.append({"key": d.name, "name": name})
    return results


# ---------------------------------------------------------------------------
# AI prompt
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = (
    "You are a research assistant. You NEVER fabricate information. "
    "If something is not available, say 'Not available'. "
    "Output ONLY valid JSON — no preamble, no markdown fences, no commentary."
)

USER_PROMPT_TEMPLATE = """\
Search the web for {company_url} and {prospect_name} who works there.

Return JSON:
{{"company":{{"name":"...","bullets":["...","...","..."]}},"prospect":{{"name":"{prospect_name}","current_role":"...","linkedin_url":"...","college":"...","hobbies":"...","sports_teams":"...","bullets":["...","...","..."]}}}}

Rules: 3 bullets each, max one short sentence. Use "Not available" for anything you can't find. Do NOT guess."""

CONTEXT_ADDENDUM = """

I am selling on behalf of {company_name}. Here is context about the product, ICP, and value props:

{context}

Use this context to identify relevant talking points or angles for the discovery call, \
but keep the output JSON structure the same."""


def build_prompt(data):
    prompt = USER_PROMPT_TEMPLATE.format(
        company_url=data["company_url"],
        prospect_name=data["prospect_name"],
    )
    selling_as = data.get("selling_as", "").strip()
    if selling_as:
        context = load_company_context(selling_as)
        if context:
            prompt += CONTEXT_ADDENDUM.format(
                company_name=selling_as.replace("-", " ").title(),
                context=context,
            )
    return prompt


def parse_json_response(text):
    """Try to extract JSON from an AI response, handling markdown fences."""
    text = text.strip()
    # Try direct parse
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    # Try extracting from code fences
    match = re.search(r"```(?:json)?\s*\n?(.*?)\n?```", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            pass
    # Try finding first { ... } block
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            pass
    return None


def run_discovery(company_url, prospect_name, selling_as=None):
    """Pure Python — no Flask, SSE, or SQLite. Safe to call from an eval harness."""
    data = {"company_url": company_url, "prospect_name": prospect_name, "selling_as": selling_as or ""}
    prompt = build_prompt(data)

    ai_result = ai_complete(prompt, system_prompt=SYSTEM_PROMPT, allow_web=True, timeout=120)
    if not ai_result.ok:
        return {"ok": False, "error": ai_result.error, "raw": None}

    raw_text = ai_result.text
    if not raw_text.strip():
        return {"ok": False, "error": "No output from AI provider", "raw": None}

    parsed = parse_json_response(raw_text)
    if not parsed:
        return {"ok": False, "error": "Could not parse research results as JSON", "raw": raw_text}

    return {"ok": True, "result": parsed, "raw": raw_text}


def result_to_markdown(data):
    """Convert structured JSON result to markdown."""
    lines = []
    c = data.get("company", {})
    p = data.get("prospect", {})

    lines.append("# Discovery Call Prep")
    lines.append("")

    lines.append(f"## About the Company: {c.get('name', 'Unknown')}")
    for b in c.get("bullets", []):
        lines.append(f"- {b}")
    lines.append("")

    lines.append(f"## About the Prospect: {p.get('name', 'Unknown')}")
    lines.append(f"- **Current Role:** {p.get('current_role', 'Not available')}")
    lines.append(f"- **LinkedIn:** {p.get('linkedin_url', 'Not available')}")
    lines.append(f"- **College:** {p.get('college', 'Not available')}")
    lines.append(f"- **Hobbies:** {p.get('hobbies', 'Not available')}")
    lines.append(f"- **Sports Teams:** {p.get('sports_teams', 'Not available')}")
    lines.append("")
    for b in p.get("bullets", []):
        lines.append(f"- {b}")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Flask application
# ---------------------------------------------------------------------------

def create_app(prefix=""):
    static_path = prefix + "/static" if prefix else "/static"
    app = Flask(
        __name__,
        static_folder=str(BASE_DIR / "static"),
        static_url_path=static_path,
        template_folder=str(BASE_DIR / "templates"),
    )
    app.config["URL_PREFIX"] = prefix

    @app.context_processor
    def inject_prefix():
        return {"prefix": app.config["URL_PREFIX"]}

    @app.teardown_appcontext
    def teardown_db(exception=None):
        close_db(exception)

    # --- Page routes -------------------------------------------------------

    @app.route(prefix + "/")
    @app.route("/")
    def index():
        return render_template("index.html")

    # --- API routes --------------------------------------------------------

    @app.route(prefix + "/api/research", methods=["POST"])
    @app.route("/api/research", methods=["POST"])
    def api_research():
        data = request.get_json(silent=True) or {}

        for field in ("company_url", "prospect_name"):
            if not (data.get(field) or "").strip():
                return jsonify({"error": f"{field} is required"}), 400

        def stream():
            if not _researching.acquire(blocking=False):
                yield f"data: {json.dumps({'error': 'A research request is already running. Please wait.'})}\n\n"
                return

            try:
                yield f"data: {json.dumps({'status': 'Searching the web and researching...'})}\n\n"

                outcome = run_discovery(
                    company_url=data["company_url"].strip(),
                    prospect_name=data["prospect_name"].strip(),
                    selling_as=(data.get("selling_as") or "").strip() or None,
                )

                if not outcome["ok"]:
                    yield f"data: {json.dumps({'error': outcome['error']})}\n\n"
                    return

                parsed = outcome["result"]

                # Save to DB
                markdown = result_to_markdown(parsed)
                company_name = parsed.get("company", {}).get("name", "")
                conn = sqlite3.connect(DB_PATH)
                conn.row_factory = sqlite3.Row
                try:
                    cur = conn.execute(
                        "INSERT INTO preps (company_url, company_name, prospect_name, selling_as, company_bullets, prospect_data, raw_markdown) VALUES (?, ?, ?, ?, ?, ?, ?)",
                        (
                            data["company_url"].strip(),
                            company_name,
                            data["prospect_name"].strip(),
                            (data.get("selling_as") or "").strip() or None,
                            json.dumps(parsed.get("company", {})),
                            json.dumps(parsed.get("prospect", {})),
                            markdown,
                        ),
                    )
                    conn.commit()
                    prep_id = cur.lastrowid
                finally:
                    conn.close()

                yield f"data: {json.dumps({'done': True, 'id': prep_id, 'result': parsed})}\n\n"

            except Exception as e:
                yield f"data: {json.dumps({'error': str(e)})}\n\n"
            finally:
                _researching.release()

        return Response(stream(), mimetype="text/event-stream",
                        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})

    @app.route(prefix + "/api/preps", methods=["GET"])
    @app.route("/api/preps", methods=["GET"])
    def api_preps_list():
        ensure_db()
        conn = get_db()
        rows = conn.execute(
            "SELECT id, company_url, company_name, prospect_name, selling_as, created_at FROM preps ORDER BY created_at DESC"
        ).fetchall()
        return jsonify({
            "preps": [
                {
                    "id": r["id"],
                    "company_url": r["company_url"],
                    "company_name": r["company_name"],
                    "prospect_name": r["prospect_name"],
                    "selling_as": r["selling_as"],
                    "created_at": r["created_at"],
                }
                for r in rows
            ]
        })

    @app.route(prefix + "/api/preps/<int:prep_id>", methods=["GET"])
    @app.route("/api/preps/<int:prep_id>", methods=["GET"])
    def api_prep_get(prep_id):
        ensure_db()
        conn = get_db()
        row = conn.execute("SELECT * FROM preps WHERE id = ?", (prep_id,)).fetchone()
        if not row:
            return jsonify({"error": "Prep not found"}), 404
        return jsonify({
            "id": row["id"],
            "company_url": row["company_url"],
            "company_name": row["company_name"],
            "prospect_name": row["prospect_name"],
            "selling_as": row["selling_as"],
            "company_bullets": json.loads(row["company_bullets"]) if row["company_bullets"] else {},
            "prospect_data": json.loads(row["prospect_data"]) if row["prospect_data"] else {},
            "raw_markdown": row["raw_markdown"],
            "created_at": row["created_at"],
        })

    @app.route(prefix + "/api/preps/<int:prep_id>", methods=["PUT"])
    @app.route("/api/preps/<int:prep_id>", methods=["PUT"])
    def api_prep_update(prep_id):
        ensure_db()
        conn = get_db()
        existing = conn.execute("SELECT id FROM preps WHERE id = ?", (prep_id,)).fetchone()
        if not existing:
            return jsonify({"error": "Prep not found"}), 404

        data = request.get_json(silent=True) or {}
        updates = []
        params = []

        if "company_bullets" in data:
            updates.append("company_bullets = ?")
            params.append(json.dumps(data["company_bullets"]))
        if "prospect_data" in data:
            updates.append("prospect_data = ?")
            params.append(json.dumps(data["prospect_data"]))
        if "company_name" in data:
            updates.append("company_name = ?")
            params.append(data["company_name"])

        if updates:
            # Also regenerate markdown
            row = conn.execute("SELECT * FROM preps WHERE id = ?", (prep_id,)).fetchone()
            company = json.loads(data.get("company_bullets", row["company_bullets"]) if isinstance(data.get("company_bullets"), str) else json.dumps(data.get("company_bullets", json.loads(row["company_bullets"] or "{}"))))
            prospect = json.loads(data.get("prospect_data", row["prospect_data"]) if isinstance(data.get("prospect_data"), str) else json.dumps(data.get("prospect_data", json.loads(row["prospect_data"] or "{}"))))
            markdown = result_to_markdown({"company": company, "prospect": prospect})
            updates.append("raw_markdown = ?")
            params.append(markdown)

            params.append(prep_id)
            conn.execute(f"UPDATE preps SET {', '.join(updates)} WHERE id = ?", params)
            conn.commit()

        return jsonify({"success": True})

    @app.route(prefix + "/api/preps/<int:prep_id>", methods=["DELETE"])
    @app.route("/api/preps/<int:prep_id>", methods=["DELETE"])
    def api_prep_delete(prep_id):
        ensure_db()
        conn = get_db()
        existing = conn.execute("SELECT id FROM preps WHERE id = ?", (prep_id,)).fetchone()
        if not existing:
            return jsonify({"error": "Prep not found"}), 404
        conn.execute("DELETE FROM preps WHERE id = ?", (prep_id,))
        conn.commit()
        return jsonify({"success": True})

    @app.route(prefix + "/api/preps/<int:prep_id>/export", methods=["GET"])
    @app.route("/api/preps/<int:prep_id>/export", methods=["GET"])
    def api_prep_export(prep_id):
        ensure_db()
        conn = get_db()
        row = conn.execute("SELECT * FROM preps WHERE id = ?", (prep_id,)).fetchone()
        if not row:
            return jsonify({"error": "Prep not found"}), 404
        filename = f"discovery-prep-{row['company_name'] or 'unknown'}-{row['prospect_name']}.md"
        filename = re.sub(r"[^\w\s.-]", "", filename).replace(" ", "-").lower()
        return Response(
            row["raw_markdown"],
            mimetype="text/markdown",
            headers={"Content-Disposition": f"attachment; filename={filename}"},
        )

    @app.route(prefix + "/api/companies", methods=["GET"])
    @app.route("/api/companies", methods=["GET"])
    def api_companies():
        return jsonify({"companies": list_company_contexts()})

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
        existing = db.execute("SELECT COUNT(*) FROM preps").fetchone()[0]
        if existing > 0 and not force:
            return jsonify({
                "status": "skipped",
                "count": 0,
                "existing": existing,
                "message": "already seeded",
            })
        if force:
            db.execute("DELETE FROM preps")
        seed_data = json.loads(seed_file.read_text())
        for item in seed_data:
            db.execute(
                "INSERT INTO preps (company_url, company_name, prospect_name, selling_as, company_bullets, prospect_data, raw_markdown) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (item["company_url"], item["company_name"], item["prospect_name"], item.get("selling_as", ""), json.dumps(item["company_bullets"]), json.dumps(item["prospect_data"]), item["raw_markdown"]),
            )
        db.commit()
        return jsonify({"status": "seeded", "count": len(seed_data), "cleared": existing if force else 0})

    return app


# ---------------------------------------------------------------------------
# Server lifecycle CLI
# ---------------------------------------------------------------------------

def is_port_in_use(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(0.2)
        return sock.connect_ex(("127.0.0.1", port)) == 0


def wait_for_port(port, timeout=2.0):
    start = time.time()
    while time.time() - start < timeout:
        if is_port_in_use(port):
            return True
        time.sleep(0.1)
    return False


def read_pid():
    if not PID_PATH.exists():
        return None
    try:
        return int(PID_PATH.read_text().strip())
    except ValueError:
        return None


def is_process_running(pid):
    if pid is None:
        return False
    try:
        os.kill(pid, 0)
    except OSError:
        return False
    return True


def command_start(args):
    ensure_db()

    if PID_PATH.exists():
        pid = read_pid()
        if pid and is_process_running(pid):
            print(f"Discovery call prep already running (PID {pid}).")
            return 0
        PID_PATH.unlink(missing_ok=True)

    port = args.port or DEFAULT_PORT
    if is_port_in_use(port):
        print(f"Port {port} is in use. Stop other process or use '{APP_NAME} start --port XXXX'.")
        return 1

    cmd = [sys.executable, str(Path(__file__).resolve()), "serve", "--port", str(port)]
    process = subprocess.Popen(
        cmd,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
    )
    PID_PATH.write_text(str(process.pid))

    wait_for_port(port, timeout=2.0)
    try:
        import webbrowser
        webbrowser.open(f"http://localhost:{port}")
    except Exception:
        print(f"Open http://localhost:{port} in your browser.")

    print(f"Discovery call prep running at http://localhost:{port} (use '{APP_NAME} stop' to shut down)")
    return 0


def command_stop(_args):
    pid = read_pid()
    if not pid or not is_process_running(pid):
        print("Discovery call prep is not running.")
        PID_PATH.unlink(missing_ok=True)
        return 0
    try:
        os.kill(pid, signal.SIGTERM)
    except OSError:
        print("Unable to stop the discovery call prep process.")
        return 1
    PID_PATH.unlink(missing_ok=True)
    print("Discovery call prep stopped.")
    return 0


def command_status(_args):
    pid = read_pid()
    if pid and is_process_running(pid):
        print(f"Discovery call prep running (PID {pid}).")
        return 0
    print("Discovery call prep is not running.")
    return 1


def command_research(args):
    outcome = run_discovery(
        company_url=args.url,
        prospect_name=args.prospect,
        selling_as=getattr(args, "selling_as", None),
    )
    if outcome["ok"]:
        print(json.dumps(outcome["result"], indent=2))
        return 0
    print(outcome["error"], file=sys.stderr)
    return 1


def command_serve(args):
    ensure_db()
    prefix = getattr(args, "prefix", "") or ""
    app = create_app(prefix=prefix)
    port = args.port or DEFAULT_PORT
    app.run(host="127.0.0.1", port=port, debug=False, threaded=True)
    return 0


# ---------------------------------------------------------------------------
# Argument parser
# ---------------------------------------------------------------------------

def build_parser():
    parser = argparse.ArgumentParser(prog=APP_NAME)
    subparsers = parser.add_subparsers(dest="command")

    start_parser = subparsers.add_parser("start", help="Start the discovery call prep server")
    start_parser.add_argument("--port", type=int, default=None, help="Port to bind")

    subparsers.add_parser("stop", help="Stop the discovery call prep server")
    subparsers.add_parser("status", help="Show server status")

    serve_parser = subparsers.add_parser("serve")
    serve_parser.add_argument("--port", type=int, default=None)
    serve_parser.add_argument("--prefix", type=str, default="", help="URL prefix for gateway mode")

    research_parser = subparsers.add_parser("research", help="Run discovery research from the CLI")
    research_parser.add_argument("--url", required=True, help="Company URL")
    research_parser.add_argument("--prospect", required=True, help="Prospect name")
    research_parser.add_argument("--selling-as", default=None, dest="selling_as", help="Company context key")

    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "start":
        return command_start(args)
    if args.command == "stop":
        return command_stop(args)
    if args.command == "status":
        return command_status(args)
    if args.command == "serve":
        return command_serve(args)
    if args.command == "research":
        return command_research(args)

    parser.print_help()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
