"""Clone the pinned application and control its disposable Docker Compose project."""
import argparse
import http.client
import json
import subprocess
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / ".sut" / "TestProject"
LOCK = json.loads((ROOT / "sut.lock.json").read_text())
COMPOSE = ["docker", "compose", "-p", "pizza-api-tests", "-f", str(ROOT / "compose.yaml")]


def run(*args):
    subprocess.run(args, cwd=ROOT, check=True)


def prepare():
    if not SOURCE.exists():
        SOURCE.parent.mkdir(parents=True, exist_ok=True)
        run("git", "clone", "--no-checkout", LOCK["repository"], str(SOURCE))
        run("git", "-C", str(SOURCE), "checkout", "--detach", LOCK["revision"])
    actual = subprocess.check_output(["git", "-C", str(SOURCE), "rev-parse", "HEAD"], text=True).strip()
    dirty = subprocess.check_output(["git", "-C", str(SOURCE), "status", "--porcelain"], text=True).strip()
    if actual != LOCK["revision"] or dirty:
        raise SystemExit(".sut/TestProject differs from sut.lock.json or contains local changes")


def wait_ready():
    deadline = time.monotonic() + 120
    while time.monotonic() < deadline:
        try:
            with urllib.request.urlopen("http://localhost:8080/orders", timeout=3) as response:
                if response.status == 200:
                    print("API ready: http://localhost:8080; UI: http://localhost:5173", flush=True)
                    return
        except (OSError, http.client.HTTPException):
            pass
        time.sleep(1)
    raise SystemExit("API did not become ready. Check: docker compose -p pizza-api-tests logs app")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["prepare", "start", "stop", "reset", "logs"])
    action = parser.parse_args().action
    if action in {"prepare", "start"}:
        prepare()
    if action == "start":
        run(*COMPOSE, "up", "-d", "--build", "--wait")
        wait_ready()
    elif action == "stop":
        run(*COMPOSE, "stop")
    elif action == "reset":
        # Only the dedicated test project is removed, including its database volume.
        run(*COMPOSE, "down", "--volumes", "--remove-orphans")
    elif action == "logs":
        run(*COMPOSE, "logs", "--tail", "100")


if __name__ == "__main__":
    main()
