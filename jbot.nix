{
  config,
  lib,
  pkgs,
  ...
}:
let
  cfg = config.programs.jbot;

  agentModule =
    { name, ... }:
    {
      options = {
        enable = lib.mkEnableOption "this JBot agent";
        role = lib.mkOption {
          type = lib.types.str;
          default = "General Developer";
          description = "The role name for this agent (e.g., QA, CEO, Lead Developer).";
        };
        description = lib.mkOption {
          type = lib.types.str;
          default = "An autonomous AI agent managing the codebase.";
          description = "A description of this agent's purpose.";
        };
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
          description = "The Gemini CLI package to use for this agent.";
        };
        promptFile = lib.mkOption {
          type = lib.types.path;
          default = ./jbot_prompt.txt;
          description = "The base prompt file to use.";
        };
        extraPackages = lib.mkOption {
          type = lib.types.listOf lib.types.package;
          default = [ ];
          description = "Additional packages for this agent's sandbox.";
        };
        dependsOn = lib.mkOption {
          type = lib.types.listOf lib.types.str;
          default = [ ];
          description = "Other agents this agent depends on (systemd After/Wants).";
        };
      };
    };
in
{
  options.programs.jbot = {
    enable = lib.mkEnableOption "JBot AI Agent Scheduler";
    agents = lib.mkOption {
      type = lib.types.attrsOf (lib.types.submodule agentModule);
      default = { };
      description = "Map of agents to run.";
    };
  };

  config = lib.mkIf cfg.enable {
    systemd.user.services = lib.mapAttrs' (
      name: agent:
      lib.nameValuePair "jbot-agent-${name}" (
        lib.mkIf agent.enable {
          Unit = {
            Description = "Scheduled JBot AI Developer: ${agent.role}";
            After = map (n: "jbot-agent-${n}.service") agent.dependsOn;
            Wants = map (n: "jbot-agent-${n}.service") agent.dependsOn;
          };
          Service = {
            Environment = [
              "PATH=${
                lib.makeBinPath (
                  [
                    pkgs.coreutils
                    pkgs.bash
                    pkgs.procps
                    pkgs.nix
                    pkgs.bubblewrap
                    pkgs.git
                    pkgs.gh
                    pkgs.curl
                    pkgs.findutils
                    pkgs.gnused
                    pkgs.gawk
                    pkgs.jq
                    pkgs.nixfmt-rfc-style
                    pkgs.statix
                    agent.geminiPackage
                    pkgs.python3
                  ]
                  ++ agent.extraPackages
                )
              }"
              "SKIP_VM_TESTS=1"
            ];
            # Systemd sandboxing for extra security
            ProtectSystem = "strict";
            ProtectHome = "read-only";
            BindPaths = [
              agent.projectDir
              "${config.home.homeDirectory}/.gemini"
              "${config.home.homeDirectory}/.config/gh"
            ];

            ExecStart = "${pkgs.writeShellScript "jbot-loop-${name}" ''
              set -euo pipefail

              PROJECT_DIR="${agent.projectDir}"
              cd "$PROJECT_DIR"

              mkdir -p .jbot/queues .jbot/memory

              PREPARED_PROMPT=$(mktemp)
              trap "rm -f $PREPARED_PROMPT" EXIT

              echo "[$(date)] JBot (${name}): Starting execution loop as ${agent.role}..."

              # Process ALL memory queues into shared memory
              # We use a simple lock via mkdir to prevent race conditions during consolidation
              LOCK_DIR=".jbot/lock"
              if mkdir "$LOCK_DIR" 2>/dev/null; then
                  trap 'rm -rf "$LOCK_DIR"; rm -f "$PREPARED_PROMPT"' EXIT
                  for q in .jbot/queues/*.json; do
                      if [ -f "$q" ]; then
                          AGENT_ID=$(basename "$q" .json)
                          echo "[$(date)] JBot (${name}): Consolidating memory from $AGENT_ID..."
                          # Wrap entry with agent identity
                          echo "{\"agent\": \"$AGENT_ID\", \"content\": $(cat "$q")}" >> .jbot/memory.log
                          rm "$q"
                      fi
                  done
                  rm -rf "$LOCK_DIR"
                  trap "rm -f $PREPARED_PROMPT" EXIT
              fi

              # Get directory tree (excluding .git and other noise)
              DIRECTORY_TREE=$(find . -maxdepth 2 -not -path '*/.*' | sed 's/^\.//' | sort)

              # Load project goal
              PROJECT_GOAL=$(cat .project_goal 2>/dev/null || echo "Maintain and improve the JBot project infrastructure.")

              # Load shared memory (last 20 entries)
              if [ -f .jbot/memory.log ]; then
                  RAG_RESULTS=$(tail -n 20 .jbot/memory.log)
              else
                  RAG_RESULTS="No previous memory found."
              fi

              # Load Task Board
              if [ -f TASKS.md ]; then
                  TASK_BOARD=$(cat TASKS.md)
              else
                  TASK_BOARD="No Task Board found. Please initialize TASKS.md if needed."
              fi

              # Use Python for robust multiline replacement
              export AGENT_NAME_VAR="${name}"
              export AGENT_ROLE_VAR="${agent.role}"
              export AGENT_DESCRIPTION_VAR="${agent.description}"
              export PROJECT_GOAL_VAR="$PROJECT_GOAL"
              export DIRECTORY_TREE_VAR="$DIRECTORY_TREE"
              export RAG_RESULTS_VAR="$RAG_RESULTS"
              export TASK_BOARD_VAR="$TASK_BOARD"

              ${pkgs.python3}/bin/python3 -c '
              import sys
              import os
              import json

              prompt_path = sys.argv[1]
              name = os.environ.get("AGENT_NAME_VAR", "")
              role = os.environ.get("AGENT_ROLE_VAR", "")
              desc = os.environ.get("AGENT_DESCRIPTION_VAR", "")
              goal = os.environ.get("PROJECT_GOAL_VAR", "")
              tree = os.environ.get("DIRECTORY_TREE_VAR", "")
              rag_raw = os.environ.get("RAG_RESULTS_VAR", "")
              task_board = os.environ.get("TASK_BOARD_VAR", "")

              # Format RAG results nicely
              rag_lines = []
              for line in rag_raw.splitlines():
                  if line.strip():
                      try:
                          data = json.loads(line)
                          agent_id = data.get("agent", "unknown")
                          content = data.get("content", {})
                          summary = content.get("summary", "No summary")
                          rag_lines.append(f"[{agent_id}] {summary}")
                      except:
                          rag_lines.append(line)
              rag_formatted = "\n".join(rag_lines[-10:]) # Keep last 10 for prompt

              with open(prompt_path, "r") as f:
                  content = f.read()

              content = content.replace("{AGENT_NAME}", name)
              content = content.replace("{AGENT_ROLE}", role)
              content = content.replace("{AGENT_DESCRIPTION}", desc)
              content = content.replace("{PROJECT_GOAL}", goal)
              content = content.replace("{DIRECTORY_TREE}", tree)
              content = content.replace("{RAG_DATABASE_RESULTS}", rag_formatted)
              content = content.replace("{TASK_BOARD}", task_board)

              sys.stdout.write(content)
              ' "${agent.promptFile}" > "$PREPARED_PROMPT"

              echo "[$(date)] JBot (${name}): Invoking Gemini CLI in bubblewrap sandbox..."

              # Calculate home manager profile path for Nix commands inside sandbox
              HM_PROFILE="${config.home.homeDirectory}/.nix-profile"
              USER_ID=$(id -u)

              # Target for agent output
              export MEMORY_OUTPUT=".jbot/queues/${name}.json"

              timeout 30m bwrap \
                --ro-bind /nix/store /nix/store \
                --ro-bind /etc/resolv.conf /etc/resolv.conf \
                --ro-bind /etc/hosts /etc/hosts \
                --ro-bind /etc/ssl/certs /etc/ssl/certs \
                --ro-bind-try /etc/static/charsets /etc/static/charsets \
                --dev /dev \
                --proc /proc \
                --tmpfs /tmp \
                --tmpfs /home \
                --bind "$PROJECT_DIR" "$PROJECT_DIR" \
                --bind "${config.home.homeDirectory}/.gemini" "${config.home.homeDirectory}/.gemini" \
                --bind-try "${config.home.homeDirectory}/.config/gh" "${config.home.homeDirectory}/.config/gh" \
                --ro-bind-try "${config.home.homeDirectory}/.gitconfig" "${config.home.homeDirectory}/.gitconfig" \
                --ro-bind-try "$HM_PROFILE" "$HM_PROFILE" \
                --ro-bind "/run/user/$USER_ID/bus" "/run/user/$USER_ID/bus" \
                --setenv HOME "${config.home.homeDirectory}" \
                --setenv PATH "$PATH" \
                --setenv DBUS_SESSION_BUS_ADDRESS "unix:path=/run/user/$USER_ID/bus" \
                --chdir "$PROJECT_DIR" \
                --unshare-all \
                --share-net \
                --die-with-parent \
                ${agent.geminiPackage}/bin/gemini -y -d -p "$(cat "$PREPARED_PROMPT")"

              echo "[$(date)] JBot (${name}): Execution loop finished."
            ''}";

            WorkingDirectory = agent.projectDir;
          };
        }
      )
    ) cfg.agents;

    systemd.user.timers = lib.mapAttrs' (
      name: agent:
      lib.nameValuePair "jbot-agent-${name}" (
        lib.mkIf agent.enable {
          Timer.OnCalendar = agent.interval;
          Install.WantedBy = [ "timers.target" ];
        }
      )
    ) cfg.agents;
  };
}
