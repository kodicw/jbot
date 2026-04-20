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
  agentsJson = pkgs.writeText "agents.json" (
    builtins.toJSON (
      lib.mapAttrs (name: agent: {
        role = agent.role;
        description = agent.description;
        interval = agent.interval;
        projectDir = toString agent.projectDir;
      }) cfg.agents
    )
  );
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
                    pkgs.bc
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

            ExecStart = "${pkgs.writeShellScript "jbot-launcher-${name}" ''
              set -euo pipefail

              PROJECT_DIR="${agent.projectDir}"
              mkdir -p "$PROJECT_DIR/.jbot"

              # Provide the agent registry to the project directory
              cp ${agentsJson} "$PROJECT_DIR/.jbot/agents.json"

              # Calculate home manager profile path for Nix commands inside sandbox
              HM_PROFILE="${config.home.homeDirectory}/.nix-profile"
              USER_ID=$(id -u)

              export AGENT_NAME="${name}"
              export AGENT_ROLE="${agent.role}"
              export AGENT_DESCRIPTION="${agent.description}"
              export PROJECT_DIR="$PROJECT_DIR"
              export PROMPT_FILE="${agent.promptFile}"
              export GEMINI_PACKAGE="${agent.geminiPackage}/bin/gemini"

              echo "[$(date)] JBot (${name}): Launching agent runner in sandbox..."

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
                ${pkgs.python3}/bin/python3 ${./.}/jbot-agent.py
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
