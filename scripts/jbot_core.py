import os
import json
import subprocess
from datetime import datetime
from typing import Any, Optional


# --- Logging ---
def log(msg: str, component: str = "JBot") -> None:
    """Standardized logging format for all JBot scripts."""
    print(f"[{datetime.now()}] {component}: {msg}")


# --- Paths & Files ---
def find_file_upwards(filename: str, start_dir: str = ".") -> Optional[str]:
    """Search for a file in the current directory and its parents."""
    current = os.path.abspath(start_dir)
    while True:
        target = os.path.join(current, filename)
        if os.path.exists(target):
            return target
        parent = os.path.dirname(current)
        if parent == current:
            break
        current = parent
    return None


def get_project_root(start_dir: str = ".") -> str:
    """Find the project root by looking for .project_goal."""
    goal_path = find_file_upwards(".project_goal", start_dir)
    if goal_path:
        return os.path.dirname(goal_path)
    return os.path.abspath(start_dir)


def load_json(file_path: str, default: Any = None) -> Any:
    """Safely load a JSON file."""
    if not os.path.exists(file_path):
        return default if default is not None else {}
    try:
        with open(file_path, "r") as f:
            return json.load(f)
    except Exception as e:
        log(f"Error loading JSON from {file_path}: {e}", "Core")
        return default if default is not None else {}


def save_json(file_path: str, data: Any) -> None:
    """Safely save a JSON file, ensuring the directory exists."""
    try:
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, "w") as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        log(f"Error saving JSON to {file_path}: {e}", "Core")


def read_file(file_path: str, default: str = "") -> str:
    """Safely read a file's content."""
    if not os.path.exists(file_path):
        return default
    try:
        with open(file_path, "r") as f:
            return f.read().strip()
    except Exception as e:
        log(f"Error reading file {file_path}: {e}", "Core")
        return default


def write_file(file_path: str, content: str) -> bool:
    """Safely write content to a file, ensuring the directory exists."""
    try:
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, "w") as f:
            f.write(content)
        return True
    except Exception as e:
        log(f"Error writing to file {file_path}: {e}", "Core")
        return False


# --- Git ---
def is_git_clean(project_dir: str = ".") -> bool:
    """Check if the git workspace is clean."""
    try:
        result = subprocess.run(
            ["git", "-C", project_dir, "status", "--porcelain"],
            capture_output=True,
            text=True,
            check=True,
        )
        return len(result.stdout.strip()) == 0
    except Exception as e:
        log(f"Error checking git status: {e}", "Core")
        return False


# --- Versioning ---
def get_version(project_dir: str = ".") -> str:
    """Retrieve the current version from the VERSION file."""
    version_path = os.path.join(project_dir, "VERSION")
    return read_file(version_path, default="0.0.0")


# --- Environment Context ---
def get_git_status(project_dir: str = ".") -> str:
    """Retrieve a short summary of the git status."""
    try:
        result = subprocess.run(
            ["git", "-C", project_dir, "status", "--short"],
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout.strip() if result.stdout.strip() else "Clean"
    except Exception:
        return "Not a git repository or git error."


def get_nix_metadata(project_dir: str = ".") -> str:
    """Retrieve Nix flake metadata."""
    try:
        result = subprocess.run(
            [
                "nix",
                "--extra-experimental-features",
                "nix-command flakes",
                "flake",
                "metadata",
                "--json",
            ],
            capture_output=True,
            text=True,
            cwd=project_dir,
        )
        if result.returncode == 0:
            data = json.loads(result.stdout)
            url = data.get("url", "Unknown")
            rev = data.get("revision", "Dirty/Uncommitted")
            return f"- **Flake URL**: {url}\n- **Revision**: {rev}"
        return "Nix flake metadata unavailable."
    except Exception:
        return "Nix command failed."


def bump_version(project_dir: str = ".", part: str = "patch") -> Optional[str]:
    """Increment the version (major, minor, patch)."""
    current_version = get_version(project_dir)
    try:
        parts = list(map(int, current_version.split(".")))
        if len(parts) != 3:
            log(f"Invalid version format: {current_version}", "Core")
            return None

        if part == "major":
            parts[0] += 1
            parts[1] = 0
            parts[2] = 0
        elif part == "minor":
            parts[1] += 1
            parts[2] = 0
        elif part == "patch":
            parts[2] += 1
        else:
            log(f"Invalid version part: {part}", "Core")
            return None

        new_version = ".".join(map(str, parts))
        if write_file(os.path.join(project_dir, "VERSION"), new_version):
            return new_version
    except Exception as e:
        log(f"Error bumping version: {e}", "Core")
    return None


def update_changelog(project_dir: str, new_version: str) -> bool:
    """
    Updates CHANGELOG.md by moving content from the [Unreleased] section
    to a new versioned section.
    """
    changelog_path = os.path.join(project_dir, "CHANGELOG.md")
    if not os.path.exists(changelog_path):
        log("CHANGELOG.md not found.", "Core")
        return False

    with open(changelog_path, "r") as f:
        lines = f.readlines()

    unreleased_header = "## [Unreleased]"
    unreleased_index = -1
    next_version_index = -1
    today_date = datetime.now().strftime("%Y-%m-%d")

    # Locate the [Unreleased] section and the start of the next version section
    for i, line in enumerate(lines):
        if unreleased_header in line:
            unreleased_index = i
        elif (
            unreleased_index != -1 and line.startswith("## [") and i > unreleased_index
        ):
            next_version_index = i
            break

    if unreleased_index == -1:
        log("Could not find [Unreleased] section in CHANGELOG.md", "Core")
        return False

    # If no next version section exists, unreleased content goes to the end of the file
    if next_version_index == -1:
        next_version_index = len(lines)

    # Extract the unreleased content (lines between unreleased header and next section)
    unreleased_content = lines[unreleased_index + 1 : next_version_index]

    # Check if there is actual meaningful change content beyond headers
    has_changes = any(
        line.strip() and not line.strip().startswith("###")
        for line in unreleased_content
    )
    if not has_changes:
        log("No meaningful changes found in [Unreleased] section.", "Core")

    # Reconstruct the changelog with a new empty [Unreleased] section
    # and the new versioned section containing the extracted content.
    updated_changelog = lines[: unreleased_index + 1]
    updated_changelog.append("\n")  # Empty line after [Unreleased] header
    updated_changelog.append(f"## [{new_version}] - {today_date}\n")
    updated_changelog.extend(unreleased_content)
    updated_changelog.extend(lines[next_version_index:])

    with open(changelog_path, "w") as f:
        f.writelines(updated_changelog)

    log(f"Updated CHANGELOG.md for version {new_version}.", "Core")
    return True
