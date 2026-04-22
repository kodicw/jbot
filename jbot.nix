{
  config,
  lib,
  pkgs,
  ...
}:
let
  cfg = config.programs.jbot;

  agentModule = _: {
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
      cpuQuota = lib.mkOption {
        type = lib.types.str;
        default = "25%";
        description = "Percentage of CPU time cap (systemd CPUQuota).";
      };
      memoryLimit = lib.mkOption {
        type = lib.types.str;
        default = "2G";
        description = "Maximum memory usage (systemd MemoryMax).";
      };
    };
  };
  agentsJson = pkgs.writeText "agents.json" (
    builtins.toJSON (
      lib.mapAttrs (_name: agent: {
        inherit (agent) role description interval;
        projectDir = toString agent.projectDir;
      }) cfg.agents
    )
  );

  jbot-cli = pkgs.writeShellScriptBin "jbot" ''
    ${pkgs.python3}/bin/python3 ${./scripts}/jbot_cli.py "$@"
  '';

  corePackages = [
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
    pkgs.ruff
    pkgs.deadnix
    pkgs.just
    pkgs.nb
    pkgs.tealdeer
    pkgs.bat
    pkgs.ripgrep
    pkgs.gum
    pkgs.pandoc
    pkgs.w3m
    (pkgs.python3.withPackages (ps: [
      ps.jinja2
      ps.pytest
      ps.pytest-mock
      ps.pytest-cov
    ]))
  ];

  # Pick a representative project directory for maintenance if multiple exist
  firstAgent = lib.head (lib.attrValues cfg.agents ++ [ { projectDir = "/dev/null"; } ]);
  maintenanceProjectDir = firstAgent.projectDir;
in
{
  options.programs.jbot = {
    enable = lib.mkEnableOption "JBot AI Agent Scheduler";
    maintenanceInterval = lib.mkOption {
      type = lib.types.str;
      default = "hourly";
      description = "Systemd calendar interval for the JBot maintenance service.";
    };
    agents = lib.mkOption {
      type = lib.types.attrsOf (lib.types.submodule agentModule);
      default = { };
      description = "Map of agents to run.";
    };
  };

  config = lib.mkIf cfg.enable {
    home.packages = [
      jbot-cli
      pkgs.nb
      pkgs.gum
      pkgs.tealdeer
      pkgs.bat
      pkgs.ripgrep
    ];

    home.activation.jbotEnvironmentAudit = config.lib.dag.entryAfter [ "writeBoundary" ] ''
      # Generate Technical Environment Note for nb
      AUDIT_CONTENT=$(cat <<EOF
      # ADR: Technical Environment & Tool Registry (Deep Audit)
      *Automated Environment Audit generated from Nix configuration on $(date).*

      ## 🛠️ Comprehensive Toolstack
      $(echo "${
        lib.concatStringsSep "\n" (
          map (
            p: "- **${p.pname or p.name}**: ${p.version or "Nix Managed"} (${lib.getBin p}/bin)"
          ) corePackages
        )
      }")

      ## 👥 Active Agent Registry
      $(echo "${
        lib.concatStringsSep "\n" (
          lib.mapAttrsToList (
            name: agent:
            "- **${name}**: ${agent.role} (Interval: ${agent.interval}, DependsOn: ${lib.concatStringsSep ", " agent.dependsOn})"
          ) cfg.agents
        )
      }")

      ## 🔒 Sandbox Architecture (bwrap)
      - **Runtime Isolation**: Full unshare (--unshare-all)
      - **Networking**: Enabled (--share-net)
      - **Shared Memory**: .nb bound to %h/.nb
      - **Identity persistence**: .gemini bound to %h/.gemini
      - **Credential Guard**: .config/gh (Read-Write), .gitconfig (Read-Only)
      - **Resource Control**: CPUQuota (25%), MemoryMax (2G) [Standard PAO Policy]

      ## 🆔 Standardized Agent Environment
      - **GIT_NAME**: JBot ({AGENT_NAME})
      - **AGENT_ROOT**: {PROJECT_DIR}
      - **CONTEXT_FILE**: {PROMPT_FILE}
      - **MEMORY_INGESTION**: {MEMORY_OUTPUT}

      ## 📖 Quick Reference (tldr)
      - **Audit**: \`just audit\`
      - **Search Memory**: \`nb jbot:q <query>\`
      - **Check Purity**: \`just prune\`
      - **Run Tests**: \`just test\`
      - **Command Help**: \`tldr <command>\`

      ## 📜 Architectural Directives
      1. **Technical Purity**: 100% test coverage and zero technical debt.
      2. **Information Density**: Documentation as executable metadata.
      3. **Internal Cohesion**: Single-user organization model.
      EOF
      )

      # Push to nb (Overwrite existing if any)
      NB_BIN="${pkgs.nb}/bin/nb"
      if [ -x "$NB_BIN" ]; then
        export EDITOR=cat
        echo "$AUDIT_CONTENT" | NB_USER_NAME="System" NB_USER_EMAIL="root@nixos" "$NB_BIN" jbot:add --title "ADR: Environment and Tool Registry" --overwrite --force || true
      fi
    '';

    systemd.user.services =
      (lib.mapAttrs' (
        name: agent:
        lib.nameValuePair "jbot-agent-${name}" (
          lib.mkIf agent.enable {
            Unit = {
              Description = "Scheduled JBot AI Developer: ${agent.role}";
              After = map (n: "jbot-agent-${n}.service") agent.dependsOn;
              Wants = map (n: "jbot-agent-${n}.service") agent.dependsOn;
            };
            Service = {
              CPUQuota = agent.cpuQuota;
              MemoryMax = agent.memoryLimit;
              Delegate = true;
              Environment = [
                "PATH=${lib.makeBinPath (corePackages ++ [ agent.geminiPackage ] ++ agent.extraPackages)}"
                "SKIP_VM_TESTS=1"
              ];
              # Systemd sandboxing for extra security
              ProtectSystem = "strict";
              ProtectHome = "read-only";
              BindPaths = [
                agent.projectDir
                "${config.home.homeDirectory}/.gemini"
                "${config.home.homeDirectory}/.config/gh"
                "${config.home.homeDirectory}/.nb"
              ];
              ExecStart = "${pkgs.writeShellScript "jbot-launcher-${name}" ''
                set -euo pipefail

                PROJECT_DIR="${agent.projectDir}"
                mkdir -p "$PROJECT_DIR/.jbot/queues"
                mkdir -p "$PROJECT_DIR/.jbot/outbox"

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

                # Pre-configure identity to bypass nb/git interactive setup
                export NB_DIR="${config.home.homeDirectory}/.nb"
                export GIT_AUTHOR_NAME="JBot (${name})"
                export GIT_AUTHOR_EMAIL="jbot-${name}@internal.jbot"
                export GIT_COMMITTER_NAME="$GIT_AUTHOR_NAME"
                export GIT_COMMITTER_EMAIL="$GIT_AUTHOR_EMAIL"
                export NB_USER_NAME="$GIT_AUTHOR_NAME"
                export NB_USER_EMAIL="$GIT_AUTHOR_EMAIL"

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
                  --ro-bind-try "$PROJECT_DIR/.jbot/memory.log" "$PROJECT_DIR/.jbot/memory.log" \
                  --ro-bind-try "$PROJECT_DIR/.jbot/agents.json" "$PROJECT_DIR/.jbot/agents.json" \
                  --ro-bind-try "$PROJECT_DIR/.jbot/messages" "$PROJECT_DIR/.jbot/messages" \
                  --ro-bind-try "$PROJECT_DIR/.jbot/directives" "$PROJECT_DIR/.jbot/directives" \
                  --bind "$PROJECT_DIR/.jbot/queues" "$PROJECT_DIR/.jbot/queues" \
                  --bind "$PROJECT_DIR/.jbot/outbox" "$PROJECT_DIR/.jbot/outbox" \
                  --bind "${config.home.homeDirectory}/.gemini" "${config.home.homeDirectory}/.gemini" \
                  --bind-try "${config.home.homeDirectory}/.config/gh" "${config.home.homeDirectory}/.config/gh" \
                  --bind "${config.home.homeDirectory}/.nb" "${config.home.homeDirectory}/.nb" \
                  --ro-bind-try "${config.home.homeDirectory}/.gitconfig" "${config.home.homeDirectory}/.gitconfig" \
                  --ro-bind-try "$HM_PROFILE" "$HM_PROFILE" \
                  --ro-bind "/run/user/$USER_ID/bus" "/run/user/$USER_ID/bus" \
                  --setenv HOME "${config.home.homeDirectory}" \
                  --setenv PATH "$PATH" \
                  --setenv NB_DIR "$NB_DIR" \
                  --setenv NB_USER_NAME "$NB_USER_NAME" \
                  --setenv NB_USER_EMAIL "$NB_USER_EMAIL" \
                  --setenv GIT_AUTHOR_NAME "$GIT_AUTHOR_NAME" \
                  --setenv GIT_AUTHOR_EMAIL "$GIT_AUTHOR_EMAIL" \
                  --setenv GIT_COMMITTER_NAME "$GIT_COMMITTER_NAME" \
                  --setenv GIT_COMMITTER_EMAIL "$GIT_COMMITTER_EMAIL" \
                  --setenv EDITOR "cat" \
                  --setenv DBUS_SESSION_BUS_ADDRESS "unix:path=/run/user/$USER_ID/bus" \
                  --chdir "$PROJECT_DIR" \
                  --unshare-all \
                  --share-net \
                  --die-with-parent \
                  ${jbot-cli}/bin/jbot agent \
                    --name "${name}" \
                    --role "${agent.role}" \
                    --desc "${agent.description}" \
                    --prompt "${agent.promptFile}" \
                    --gemini "${agent.geminiPackage}/bin/gemini"
              ''}";

              WorkingDirectory = agent.projectDir;
            };
          }
        )
      ) cfg.agents)
      // {
        jbot-maintenance = {
          Unit = {
            Description = "JBot Infrastructure Maintenance Service";
          };
          Service = {
            Environment = [
              "PATH=${
                lib.makeBinPath [
                  pkgs.coreutils
                  pkgs.bash
                  pkgs.git
                  pkgs.python3
                  pkgs.findutils
                  pkgs.gnused
                  pkgs.gawk
                  jbot-cli
                ]
              }"
              "PROJECT_DIR=${maintenanceProjectDir}"
            ];
            ExecStart = "${jbot-cli}/bin/jbot maintenance";
            WorkingDirectory = maintenanceProjectDir;
          };
        };
      };

    systemd.user.timers =
      (lib.mapAttrs' (
        name: agent:
        lib.nameValuePair "jbot-agent-${name}" (
          lib.mkIf agent.enable {
            Timer.OnCalendar = agent.interval;
            Install.WantedBy = [ "timers.target" ];
          }
        )
      ) cfg.agents)
      // {
        jbot-maintenance = {
          Timer.OnCalendar = cfg.maintenanceInterval;
          Install.WantedBy = [ "timers.target" ];
        };
      };

  };
}
