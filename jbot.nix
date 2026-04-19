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
    geminiPackage = lib.mkOption {
      type = lib.types.package;
      default = pkgs.gemini-cli;
      description = "The Gemini CLI package to use.";
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
            cfg.geminiPackage
            pkgs.python3
            pkgs.jq
            pkgs.nixfmt-rfc-style
            pkgs.statix
          ]
        }";
        # Sandboxing
        ProtectSystem = "strict";
        ProtectHome = "read-only";
        PrivateTmp = true;
        NoNewPrivileges = true;
        CapabilityBoundingSet = "";
        # Bind project directory as writable
        BindPaths = [ cfg.projectDir ];
        # Bind essential paths as read-only
        BindReadOnlyPaths = [
          "/nix/store"
          "/etc/ssl/certs"
          "/etc/static/charsets"
          "/etc/resolv.conf"
          "/etc/hosts"
        ];
        ExecStart = "${pkgs.writeShellScript "jbot-loop" ''
          set -euo pipefail

          PROJECT_DIR="${cfg.projectDir}"
          cd "$PROJECT_DIR"

          # Inject context into the prompt
          # We'll use a temporary file for the prepared prompt
          PREPARED_PROMPT=$(mktemp)
          trap "rm -f $PREPARED_PROMPT" EXIT

          echo "[$(date)] JBot: Starting execution loop..."

          # Get directory tree (excluding .git and other noise)
          DIRECTORY_TREE=$(find . -maxdepth 2 -not -path '*/.*' | sed 's/^\.//' | sort)

          # Process memory queue if it exists
          if [ -f .memory_queue.json ]; then
              echo "[$(date)] JBot: Consuming memory queue..."
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

          # Run gemini in YOLO mode directly; it will use its tools to modify the project.
          echo "[$(date)] JBot: Invoking Gemini CLI..."
          ${pkgs.gemini-cli}/bin/gemini -y -p "$(cat "$PREPARED_PROMPT")"

          echo "[$(date)] JBot: Execution loop finished."
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
