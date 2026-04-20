import os
import argparse
from datetime import datetime


def log(msg):
    print(f"[{datetime.now()}] JBot Messaging: {msg}")


def send_message(to_dir, agent_name, body, subject="No Subject"):
    msgs_dir = os.path.join(to_dir, ".jbot", "messages")
    if not os.path.exists(msgs_dir):
        log(
            f"Error: Messages directory {msgs_dir} not found. Ensure the project is initialized."
        )
        return False

    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filename = f"{timestamp}_{agent_name}.txt"
    file_path = os.path.join(msgs_dir, filename)

    message_content = f"To: all\nFrom: {agent_name}\nSubject: {subject}\n\n{body}\n"

    with open(file_path, "w") as f:
        f.write(message_content)

    log(f"Message sent to {msgs_dir}/{filename}")
    return True


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="JBot Agent Messaging Tool")
    parser.add_argument(
        "-d",
        "--dir",
        default=".",
        help="Project directory to send the message to (default: current directory)",
    )
    parser.add_argument(
        "-f",
        "--from-agent",
        required=True,
        help="Name of the agent sending the message",
    )
    parser.add_argument("-s", "--subject", default="No Subject", help="Message subject")
    parser.add_argument("-m", "--message", required=True, help="Message body")

    args = parser.parse_args()

    send_message(
        to_dir=args.dir,
        agent_name=args.from_agent,
        body=args.message,
        subject=args.subject,
    )
