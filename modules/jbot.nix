{
  config,
  lib,
  pkgs,
  ...
}:
let
  cfg = config.programs.jbot;

  # We expect the package to be passed in or use the one from corePackages
  jbot-cli = pkgs.callPackage ../pkgs/jbot-cli.nix { scripts = ../scripts; };
  jbotPython = jbot-cli.python;

  bwrap = "${pkgs.bubblewrap}/bin/bwrap";
  timeout = "${pkgs.coreutils}/bin/timeout";
  mkdir = "${pkgs.coreutils}/bin/mkdir";
  cp = "${pkgs.coreutils}/bin/cp";
  id = "${pkgs.coreutils}/bin/id";
  date = "${pkgs.coreutils}/bin/date";
  mktemp = "${pkgs.coreutils}/bin/mktemp";

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
        default = cfg.projectDir;
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
      opencodePackage = lib.mkOption {
        type = lib.types.package;
        default = pkgs.hello; # Placeholder until provided or used
        description = "The OpenCode CLI package to use for this agent.";
      };
      cliType = lib.mkOption {
        type = lib.types.enum [
          "gemini"
          "opencode"
        ];
        default = "gemini";
        description = "The type of AI CLI interface to use.";
      };
      promptFile = lib.mkOption {
        type = lib.types.path;
        default = cfg.promptFile;
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
      timeoutStartSec = lib.mkOption {
        type = lib.types.str;
        default = "30min";
        description = "Systemd TimeoutStartSec for this agent.";
      };
      timeoutStopSec = lib.mkOption {
        type = lib.types.str;
        default = "5min";
        description = "Systemd TimeoutStopSec for this agent.";
      };
      killMode = lib.mkOption {
        type = lib.types.str;
        default = "mixed";
        description = "Systemd KillMode for this agent.";
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
    pkgs.gnugrep
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
    pkgs.nmap
    pkgs.w3m
    jbotPython
    jbot-cli
  ];

  # Pick a representative project directory for maintenance if multiple exist
  firstAgent = lib.head (lib.attrValues cfg.agents ++ [ { projectDir = "/dev/null"; } ]);
  maintenanceProjectDir = firstAgent.projectDir;
in
{
  options.programs.jbot = {
    enable = lib.mkEnableOption "JBot AI Agent Scheduler";
    projectDir = lib.mkOption {
      type = lib.types.path;
      default = config.home.homeDirectory + "/code/jbot";
      description = "The default project directory for all agents.";
    };
    promptFile = lib.mkOption {
      type = lib.types.path;
      default = ../jbot_prompt.txt;
      description = "The default base prompt file for all agents.";
    };
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
      jbotPython
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

      #type:adr

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

      ## 📜 Architectural Directives
      1. **Technical Purity**: 100% test coverage and zero technical debt.
      2. **Information Density**: Documentation as executable metadata.
      3. **Internal Cohesion**: Single-user organization model.
      EOF
      )

      # Push to nb stably via jbot CLI
      JBOT_BIN="${jbot-cli}/bin/jbot"
      if [ -x "$JBOT_BIN" ]; then
        export EDITOR=cat
        export PATH="$PATH:${lib.makeBinPath [ pkgs.git ]}"
        export NB_USER_NAME="System"
        export NB_USER_EMAIL="root@nixos"
        echo "$AUDIT_CONTENT" | "$JBOT_BIN" maintenance push-note --title "ADR: Environment and Tool Registry" --tags "type:adr,type:audit" || true
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
              TimeoutStartSec = agent.timeoutStartSec;
              TimeoutStopSec = agent.timeoutStopSec;
              KillMode = agent.killMode;
              Delegate = true;
              Environment = [
                "PATH=${
                  lib.makeBinPath (
                    corePackages
                    ++ [
                      pkgs.bubblewrap
                      pkgs.coreutils
                      agent.geminiPackage
                      agent.opencodePackage
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
                "${config.home.homeDirectory}/.nb"
              ];
              ExecStart = "${pkgs.writeShellScript "jbot-launcher-${name}" ''
                set -euo pipefail

                PROJECT_DIR="${agent.projectDir}"
                ${mkdir} -p "$PROJECT_DIR/.jbot/queues"
                ${mkdir} -p "$PROJECT_DIR/.jbot/outbox"

                # Provide the agent registry to the project directory
                ${cp} ${agentsJson} "$PROJECT_DIR/.jbot/agents.json"

                # Calculate home manager profile path for Nix commands inside sandbox
                HM_PROFILE="${config.home.homeDirectory}/.nix-profile"
                USER_ID=$(${id} -u)

                export AGENT_NAME="${name}"
                export AGENT_ROLE="${agent.role}"
                export AGENT_DESCRIPTION="${agent.description}"
                export PROJECT_DIR="$PROJECT_DIR"
                export PROMPT_FILE="${agent.promptFile}"
                export CLI_BIN="${
                  if agent.cliType == "gemini" then
                    "${agent.geminiPackage}/bin/gemini"
                  else
                    "${agent.opencodePackage}/bin/opencode"
                }"
                export CLI_TYPE="${agent.cliType}"

                # Pre-configure identity to bypass nb/git interactive setup
                export NB_DIR="${config.home.homeDirectory}/.nb"
                export GIT_AUTHOR_NAME="JBot (${name})"
                export GIT_AUTHOR_EMAIL="jbot-${name}@internal.jbot"
                export GIT_COMMITTER_NAME="$GIT_AUTHOR_NAME"
                export GIT_COMMITTER_EMAIL="$GIT_AUTHOR_EMAIL"
                export NB_USER_NAME="$GIT_AUTHOR_NAME"
                export NB_USER_EMAIL="$GIT_AUTHOR_EMAIL"

                # Create a minimal fake passwd file to satisfy Node.js os.userInfo()
                FAKE_PASSWD=$(${mktemp})
                echo "${name}:x:$USER_ID:$USER_ID:JBot Agent:${config.home.homeDirectory}:/bin/bash" > "$FAKE_PASSWD"

                echo "[$(${date})] JBot (${name}): Launching agent runner in sandbox..."

                ${timeout} 30m ${bwrap} \
                  --ro-bind /nix/store /nix/store \
                  --ro-bind /etc/resolv.conf /etc/resolv.conf \
                  --ro-bind /etc/hosts /etc/hosts \
                  --ro-bind /etc/ssl/certs /etc/ssl/certs \
                  --ro-bind-try /etc/static/charsets /etc/static/charsets \
                  --ro-bind "$FAKE_PASSWD" /etc/passwd \
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
                  --ro-bind-try "${config.home.homeDirectory}/.nbrc" "${config.home.homeDirectory}/.nbrc" \
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
                  --setenv CLI_BIN "$CLI_BIN" \
                  --setenv CLI_TYPE "$CLI_TYPE" \
                  --setenv EDITOR "cat" \
                  --setenv TERM "dumb" \
                  --setenv PAGER "cat" \
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
                    --cli-bin "$CLI_BIN" \
                    --cli-type "$CLI_TYPE"
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
                  pkgs.gnugrep
                  pkgs.gawk
                  pkgs.which
                  jbot-cli
                ]
              }"
              "PROJECT_DIR=${maintenanceProjectDir}"
            ];
            ExecStart = "${jbot-cli}/bin/jbot maintenance";
            WorkingDirectory = maintenanceProjectDir;
          };
        };
        jbot-knowledge-base = {
          Unit = {
            Description = "JBot Knowledge Base HTTP Server (nb browse)";
            After = [ "network.target" ];
          };
          Service = {
            Environment = [
              "PATH=${lib.makeBinPath corePackages}"
              "NB_DIR=${config.home.homeDirectory}/.nb"
              "HOME=${config.home.homeDirectory}"
            ];
            ExecStart = "${pkgs.nb}/bin/nb jbot:browse --serve";
            Restart = "always";
            RestartSec = "10";
            WorkingDirectory = config.home.homeDirectory;
          };
          Install.WantedBy = [ "default.target" ];
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
