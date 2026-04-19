{
  config,
  lib,
  pkgs,
  ...
}:
let
  cfg = config.programs.jbot;
in
{
  options.programs.jbot = {
    enable = lib.mkEnableOption "JBot AI Agent Scheduler";
    projectDir = lib.mkOption {
      type = lib.types.path;
      description = "The project directory to manage.";
    };
    interval = lib.mkOption {
      type = lib.types.str;
      default = "hourly";
      description = "Systemd calendar interval for the JBot agent.";
    };
  };

  config = lib.mkIf cfg.enable {
    systemd.user.services.jbot-agent = {
      Unit.Description = "Scheduled JBot AI Developer";
      Service = {
        Environment = "PATH=${
          lib.makeBinPath [
            pkgs.coreutils
            pkgs.bash
            pkgs.git
            pkgs.gh
            pkgs.curl
            pkgs.findutils
            pkgs.gnused
            pkgs.gawk
            pkgs.gemini-cli
            pkgs.python3
            pkgs.jq
          ]
        }";
        ExecStart = "${pkgs.writeShellScript "jbot-loop" ''
                    set -euo pipefail

                    PROJECT_DIR="${cfg.projectDir}"
                    cd "$PROJECT_DIR"

                    # Inject context into the prompt
                    # We'll use a temporary file for the prepared prompt
                    PREPARED_PROMPT=$(mktemp)

                    # Get directory tree (excluding .git and other noise)
                    DIRECTORY_TREE=$(find . -maxdepth 2 -not -path '*/.*' | sed 's/^\.//' | sort)

                    # Process memory queue if it exists
                    if [ -f .memory_queue.json ]; then
                        cat .memory_queue.json >> .memory.log
                        rm .memory_queue.json
                    fi

                    # Load project goal
                    PROJECT_GOAL=$(cat .project_goal 2>/dev/null || echo "Maintain and improve the JBot project infrastructure.")

                    # Load memory log
                    if [ -f .memory.log ]; then
                        RAG_RESULTS=$(tail -n 10 .memory.log)
                    else
                        RAG_RESULTS="No previous memory found."
                    fi

                    # Use Python for robust multiline replacement
                    export PROJECT_GOAL_VAR="$PROJECT_GOAL"
                    export DIRECTORY_TREE_VAR="$DIRECTORY_TREE"
                    export RAG_RESULTS_VAR="$RAG_RESULTS"

                    ${pkgs.python3}/bin/python3 -c '
          import sys
          import os

          prompt_path = sys.argv[1]
          goal = os.environ.get("PROJECT_GOAL_VAR", "")
          tree = os.environ.get("DIRECTORY_TREE_VAR", "")
          rag = os.environ.get("RAG_RESULTS_VAR", "")

          with open(prompt_path, "r") as f:
              content = f.read()

          content = content.replace("{PROJECT_GOAL}", goal)
          content = content.replace("{DIRECTORY_TREE}", tree)
          content = content.replace("{RAG_DATABASE_RESULTS}", rag)

          sys.stdout.write(content)
          ' "$PROJECT_DIR/jbot_prompt.txt" > "$PREPARED_PROMPT"

                    # Run gemini-cli in YOLO mode and pipe output to bash
                    ${pkgs.gemini-cli}/bin/gemini -y --raw-output -p "$(cat "$PREPARED_PROMPT")" | bash

                    rm "$PREPARED_PROMPT"
        ''}";
        WorkingDirectory = cfg.projectDir;
      };
    };

    systemd.user.timers.jbot-agent = {
      Timer.OnCalendar = cfg.interval;
      Install.WantedBy = [ "timers.target" ];
    };
  };
}
