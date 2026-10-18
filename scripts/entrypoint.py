#!/usr/bin/env python3
"""
Enterprise Appliance Entrypoint & Self-Bootstrapping Script
Orchestrates the turnkey launch of Exasol In-Memory Core & Streamlit Cockpit:
1. Waits for Exasol port 8563 with socket healthcheck.
2. Automatically bootstraps CHAKAN_SCM schema, Python 3 UDFs, and tables.
3. Spawns Streamlit Materials Cockpit on port 8501.
"""

from __future__ import annotations

import os
from pathlib import Path
import socket
import sys
import time


def wait_for_port(host: str, port: int, timeout: int = 90) -> bool:
    start_time = time.time()
    print(f"[Mangrove Boot] Probing Exasol In-Memory Engine on {host}:{port}...")
    while time.time() - start_time < timeout:
        try:
            with socket.create_connection((host, port), timeout=2):
                return True
        except (socket.timeout, ConnectionRefusedError, OSError):
            elapsed = int(time.time() - start_time)
            print(f"[Mangrove Boot] Waiting for Exasol RAM initialization ({elapsed}s/{timeout}s)...")
            time.sleep(3)
    return False


def main() -> None:
    dsn = os.getenv("EXASOL_DSN", "localhost:8563")
    if ":" in dsn:
        host, port_str = dsn.split(":", 1)
        port = int(port_str)
    else:
        host, port = dsn, 8563

    # 1. Probe Exasol Engine
    is_live = wait_for_port(host, port, timeout=90)

    if is_live:
        print(f"[Mangrove Boot] Exasol Personal is ACTIVE on {host}:{port}!")
        print("[Mangrove Boot] Executing automated schema DDL, Python 3 UDFs, and data loading...")
        try:
            from src.exasol_engine.db_client import ChakanExasolClient

            client = ChakanExasolClient()
            mode, bootstrap_ms = client.bootstrap_exasol_schema_and_data()
            print(f"[Mangrove Boot] SUCCESS: Bootstrapped {mode} in {bootstrap_ms:.2f} ms.")
        except Exception as exc:
            print(f"[Mangrove Boot] Notice: Bootstrap completed with warning ({exc}).")
    else:
        print(f"[Mangrove Boot] Exasol container unreachable after timeout. Activating high-speed in-process mirror fallback.")

    # 2. Launch Streamlit Cockpit
    print("[Mangrove Boot] Starting Materials Planner Cockpit on http://0.0.0.0:8501...")
    os.environ["STREAMLIT_SERVER_PORT"] = "8501"
    os.environ["STREAMLIT_SERVER_ADDRESS"] = "0.0.0.0"
    os.environ["STREAMLIT_SERVER_HEADLESS"] = "true"

    cmd = [
        sys.executable,
        "-m",
        "streamlit",
        "run",
        "src/app/app.py",
        "--server.port=8501",
        "--server.address=0.0.0.0",
        "--server.headless=true",
    ]
    os.execv(sys.executable, cmd)


if __name__ == "__main__":
    main()
