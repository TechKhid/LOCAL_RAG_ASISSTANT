import argparse
import subprocess
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
BASE_COMMAND = ["docker", "compose"]


def run_command(args: list[str]) -> int:
    completed = subprocess.run(BASE_COMMAND + args, cwd=PROJECT_ROOT)
    return completed.returncode


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Small wrapper around docker compose for the OpenSearch service."
    )
    parser.add_argument(
        "action",
        choices=["up", "down", "restart", "logs", "status"],
        help="Compose action to run against the OpenSearch service.",
    )
    parsed = parser.parse_args()

    if parsed.action == "up":
        return run_command(["up", "-d", "opensearch"])
    if parsed.action == "down":
        return run_command(["stop", "opensearch"])
    if parsed.action == "restart":
        return run_command(["restart", "opensearch"])
    if parsed.action == "logs":
        return run_command(["logs", "-f", "opensearch"])
    return run_command(["ps", "opensearch"])


if __name__ == "__main__":
    sys.exit(main())
