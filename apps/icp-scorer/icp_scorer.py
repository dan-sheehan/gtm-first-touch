#!/usr/bin/env python3
"""ICP Scorer — Rule-based Ideal Customer Profile scoring engine."""
from __future__ import annotations

import argparse
import json
import os
import signal
import socket
import sqlite3
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

from flask import Flask, g, jsonify, render_template, request

APP_NAME = "icp-scorer"
DEFAULT_PORT = 3012
DATA_DIR = Path.home() / ".icp-scorer"
DB_PATH = DATA_DIR / "icp_scorer.db"
PID_PATH = DATA_DIR / "icp-scorer.pid"
BASE_DIR = Path(__file__).resolve().parent
MODEL_PATH = BASE_DIR / "scoring_model.json"


# ---------------------------------------------------------------------------
# Database helpers
# ---------------------------------------------------------------------------

def ensure_db() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.execute("""
        CREATE TABLE IF NOT EXISTS scores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            company_name TEXT NOT NULL,
            dimensions TEXT NOT NULL,
            score INTEGER NOT NULL,
            grade TEXT NOT NULL,
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


# ---------------------------------------------------------------------------
# Scoring model
# ---------------------------------------------------------------------------

def load_model() -> dict[str, object]:
    return json.loads(MODEL_PATH.read_text())


def compute_score(
    model: dict[str, object], selections: dict[str, str]
) -> tuple[int, str, list[dict[str, object]]]:
    """Compute weighted ICP score from dimension selections.

    selections: dict mapping dimension_id -> selected option value
    Returns: (score, grade, breakdown)
    """
    total_weight = 0
    weighted_sum = 0
    breakdown = []

    for dim in model["dimensions"]:
        dim_id = dim["id"]
        weight = dim["weight"]
        selected = selections.get(dim_id, "")
        dim_score = 0

        for opt in dim["options"]:
            if opt["value"] == selected:
                dim_score = opt["score"]
                break

        weighted_sum += weight * dim_score
        total_weight += weight
        breakdown.append({
            "dimension": dim_id,
            "label": dim["label"],
            "weight": weight,
            "selected": selected,
            "score": dim_score,
            "weighted": round(weight * dim_score / 100, 1),
        })

    score = round(weighted_sum / total_weight) if total_weight > 0 else 0

    thresholds = model.get("thresholds", {"A": 80, "B": 60, "C": 40, "D": 0})
    grade = "D"
    for g_letter in ["A", "B", "C"]:
        if score >= thresholds.get(g_letter, 0):
            grade = g_letter
            break

    return score, grade, breakdown


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

    @app.route(prefix + "/api/model", methods=["GET"])
    def api_model():
        return jsonify(load_model())

    @app.route(prefix + "/api/score", methods=["POST"])
    def api_score():
        data = request.get_json(silent=True) or {}
        company_name = data.get("company_name", "").strip()
        selections = data.get("selections", {})

        if not company_name:
            return jsonify({"error": "Company name is required"}), 400

        model = load_model()
        score, grade, breakdown = compute_score(model, selections)

        db = get_db()
        now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")
        cur = db.execute(
            "INSERT INTO scores (company_name, dimensions, score, grade, created_at) VALUES (?, ?, ?, ?, ?)",
            (company_name, json.dumps(selections), score, grade, now),
        )
        db.commit()

        return jsonify({
            "id": cur.lastrowid,
            "company_name": company_name,
            "score": score,
            "grade": grade,
            "breakdown": breakdown,
        })

    @app.route(prefix + "/api/scores", methods=["GET"])
    def api_scores():
        db = get_db()
        rows = db.execute(
            "SELECT id, company_name, score, grade, created_at FROM scores ORDER BY created_at DESC LIMIT 50"
        ).fetchall()
        return jsonify({
            "scores": [dict(r) for r in rows],
        })

    @app.route(prefix + "/api/scores/<int:score_id>", methods=["GET"])
    def api_score_detail(score_id):
        db = get_db()
        row = db.execute("SELECT * FROM scores WHERE id = ?", (score_id,)).fetchone()
        if not row:
            return jsonify({"error": "Not found"}), 404
        result = dict(row)
        result["dimensions"] = json.loads(result["dimensions"])
        return jsonify(result)

    @app.route(prefix + "/api/scores/<int:score_id>", methods=["DELETE"])
    def api_score_delete(score_id):
        db = get_db()
        db.execute("DELETE FROM scores WHERE id = ?", (score_id,))
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
        existing = db.execute("SELECT COUNT(*) FROM scores").fetchone()[0]
        if existing > 0 and not force:
            return jsonify({
                "status": "skipped",
                "count": 0,
                "existing": existing,
                "message": "already seeded",
            })
        if force:
            db.execute("DELETE FROM scores")
        seed_data = json.loads(seed_file.read_text())
        now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")
        for item in seed_data:
            db.execute(
                "INSERT INTO scores (company_name, dimensions, score, grade, created_at) VALUES (?, ?, ?, ?, ?)",
                (item["company_name"], json.dumps(item["dimensions"]), item["score"], item["grade"], now),
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
            print(f"ICP Scorer already running (PID {pid}).")
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
    print(f"ICP Scorer running at http://localhost:{port}")
    return 0


def command_stop(_args: argparse.Namespace) -> int:
    pid = read_pid()
    if not pid or not is_process_running(pid):
        print("ICP Scorer is not running.")
        PID_PATH.unlink(missing_ok=True)
        return 0
    try:
        os.kill(pid, signal.SIGTERM)
    except OSError:
        print("Unable to stop ICP Scorer.")
        return 1
    PID_PATH.unlink(missing_ok=True)
    print("ICP Scorer stopped.")
    return 0


def command_status(_args: argparse.Namespace) -> int:
    pid = read_pid()
    if pid and is_process_running(pid):
        print(f"ICP Scorer running (PID {pid}).")
        return 0
    print("ICP Scorer is not running.")
    return 1


def command_serve(args: argparse.Namespace) -> int:
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
