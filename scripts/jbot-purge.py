import os
import re
import shutil
import argparse
from datetime import datetime


def log(msg):
    print(f"[{datetime.now()}] JBot Purge: {msg}")


def purge_directives(
    dir_path=".jbot/directives", archive_path=".jbot/directives/archive"
):
    if not os.path.exists(dir_path):
        log(f"Error: Directive directory {dir_path} not found.")
        return

    os.makedirs(archive_path, exist_ok=True)

    today = datetime.now().strftime("%Y-%m-%d")
    purged_count = 0

    dir_files = [
        f
        for f in os.listdir(dir_path)
        if f.endswith((".txt", ".md")) and f != "README.md"
    ]

    for df in dir_files:
        is_expired = False
        df_path = os.path.join(dir_path, df)

        # Skip if it's a directory
        if os.path.isdir(df_path):
            continue

        # Try to find a date (YYYY-MM-DD) in the filename
        date_match = re.search(r"(\d{4}-\d{2}-\d{2})", df)
        exp_date_from_filename = date_match.group(1) if date_match else None

        try:
            with open(df_path, "r") as f:
                directive_content = f.read()

                # Check for explicit expiration in content: "Expiration: YYYY-MM-DD"
                content_exp_match = re.search(
                    r"Expiration:\s*(\d{4}-\d{2}-\d{2})",
                    directive_content,
                    re.IGNORECASE,
                )
                if content_exp_match:
                    exp_date = content_exp_match.group(1)
                    if today > exp_date:
                        is_expired = True
                        log(f"Directive {df} has expired (from content: {exp_date}).")
                elif exp_date_from_filename:
                    # If only date in filename, we treat it as an expiration date by default
                    # as per current jbot-agent.py logic.
                    if today > exp_date_from_filename:
                        is_expired = True
                        log(
                            f"Directive {df} has expired (from filename: {exp_date_from_filename})."
                        )

                if is_expired:
                    dest_path = os.path.join(archive_path, df)
                    # Handle filename collision in archive
                    if os.path.exists(dest_path):
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        name, ext = os.path.splitext(df)
                        dest_path = os.path.join(
                            archive_path, f"{name}_{timestamp}{ext}"
                        )

                    shutil.move(df_path, dest_path)
                    log(
                        f"Archived expired directive: {df} -> {os.path.basename(dest_path)}"
                    )
                    purged_count += 1

        except Exception as e:
            log(f"Error processing directive {df}: {e}")

    if purged_count > 0:
        log(f"Successfully purged {purged_count} expired directives.")
    else:
        log("No expired directives found.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="JBot Directive Purging Tool")
    parser.add_argument(
        "-d", "--dir", default=".jbot/directives", help="Directives directory"
    )
    parser.add_argument(
        "-a", "--archive", default=".jbot/directives/archive", help="Archive directory"
    )
    args = parser.parse_args()

    purge_directives(dir_path=args.dir, archive_path=args.archive)
