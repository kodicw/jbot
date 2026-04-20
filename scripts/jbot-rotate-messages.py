import os
import shutil
import argparse
from datetime import datetime


def log(msg):
    print(f"[{datetime.now()}] JBot Message Rotate: {msg}")


def rotate_messages(
    msgs_dir=".jbot/messages", archive_dir=".jbot/messages/archive", limit=20
):
    if not os.path.exists(msgs_dir):
        log(f"Messages directory {msgs_dir} not found.")
        return

    os.makedirs(archive_dir, exist_ok=True)

    all_msgs = sorted(
        [f for f in os.listdir(msgs_dir) if f.endswith(".txt") and f != "human.txt"]
    )

    if len(all_msgs) <= limit:
        log(
            f"Messages directory has {len(all_msgs)} entries (Limit: {limit}). No rotation needed."
        )
        return

    # Split files
    to_keep = all_msgs[-limit:]
    to_archive = all_msgs[:-limit]

    log(
        f"Rotating messages: Keeping {len(to_keep)} entries, Archiving {len(to_archive)} entries."
    )

    for mf in to_archive:
        src_path = os.path.join(msgs_dir, mf)
        dest_path = os.path.join(archive_dir, mf)

        # Handle filename collision in archive
        if os.path.exists(dest_path):
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            name, ext = os.path.splitext(mf)
            dest_path = os.path.join(archive_dir, f"{name}_{timestamp}{ext}")

        shutil.move(src_path, dest_path)

    log(f"Successfully archived old messages to {archive_dir}")


def main():
    parser = argparse.ArgumentParser(description="JBot Message Rotation Tool")
    parser.add_argument(
        "-m", "--messages", default=".jbot/messages", help="Messages directory"
    )
    parser.add_argument(
        "-a", "--archive", default=".jbot/messages/archive", help="Archive directory"
    )
    parser.add_argument(
        "-l", "--limit", type=int, default=20, help="Max entries to keep in messages/"
    )
    args = parser.parse_args()

    rotate_messages(msgs_dir=args.messages, archive_dir=args.archive, limit=args.limit)


if __name__ == "__main__":
    main()
