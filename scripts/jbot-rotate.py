import os
from datetime import datetime
import argparse


def log(msg):
    print(f"[{datetime.now()}] JBot Memory Rotate: {msg}")


def rotate_memory(
    memory_log=".jbot/memory.log", archive_log=".jbot/memory.log.archive", limit=100
):
    if not os.path.exists(memory_log):
        log(f"Memory log {memory_log} not found. Skipping rotation.")
        return

    try:
        with open(memory_log, "r") as f:
            lines = f.readlines()

        if len(lines) <= limit:
            log(
                f"Memory log has {len(lines)} entries (Limit: {limit}). No rotation needed."
            )
            return

        # Split lines
        to_keep = lines[-limit:]
        to_archive = lines[:-limit]

        log(
            f"Rotating memory: Keeping {len(to_keep)} entries, Archiving {len(to_archive)} entries."
        )

        # Append to archive
        with open(archive_log, "a") as f:
            f.writelines(to_archive)

        # Rewrite memory log
        with open(memory_log, "w") as f:
            f.writelines(to_keep)

        log(f"Successfully rotated memory log. Archive: {archive_log}")

    except Exception as e:
        log(f"Error rotating memory log: {e}")


def main():
    parser = argparse.ArgumentParser(description="JBot Memory Rotation Tool")
    parser.add_argument(
        "-m", "--memory", default=".jbot/memory.log", help="Memory log file"
    )
    parser.add_argument(
        "-a", "--archive", default=".jbot/memory.log.archive", help="Archive log file"
    )
    parser.add_argument(
        "-l", "--limit", type=int, default=100, help="Max entries to keep in memory.log"
    )
    args = parser.parse_args()

    rotate_memory(memory_log=args.memory, archive_log=args.archive, limit=args.limit)


if __name__ == "__main__":
    main()
