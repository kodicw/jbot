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
    pkgs.shellcheck
    pkgs.bats
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
    assertions = [
      {
        assertion = lib.all (agent: lib.hasPrefix config.home.homeDirectory (toString agent.projectDir)) (
          lib.attrValues cfg.agents
        );
        message = "JBot agents must operate within the user's home directory (${config.home.homeDirectory}) to maintain single-user isolation.";
      }
    ];

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
        export NB_USER_NAME="JBot (${config.home.username})"
        export NB_USER_EMAIL="${config.home.username}@nixos"
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

                # Export all required environment variables for the standalone launcher
                export AGENT_NAME="${name}"
                export AGENT_ROLE="${agent.role}"
                export AGENT_DESCRIPTION="${agent.description}"
                export PROJECT_DIR="${agent.projectDir}"
                export PROMPT_FILE="${agent.promptFile}"
                export CLI_BIN="${
                  if agent.cliType == "gemini" then
                    "${agent.geminiPackage}/bin/gemini"
                  else
                    "${agent.opencodePackage}/bin/opencode"
                }"
                export CLI_TYPE="${agent.cliType}"
                export AGENTS_JSON="${agentsJson}"
                export JBOT_CLI_BIN="${jbot-cli}/bin/jbot"

                # Binaries
                export MKDIR_BIN="${mkdir}"
                export CP_BIN="${cp}"
                export ID_BIN="${id}"
                export DATE_BIN="${date}"
                export MKTEMP_BIN="${mktemp}"
                export TIMEOUT_BIN="${timeout}"
                export BWRAP_BIN="${bwrap}"

                # Environment paths
                export HM_PROFILE="${config.home.homeDirectory}/.nix-profile"
                export USER_ID=$(${id} -u)
                export NB_DIR="${config.home.homeDirectory}/.nb"

                # Standard Identity
                export GIT_AUTHOR_NAME="JBot (${name})"
                export GIT_AUTHOR_EMAIL="jbot-${name}@internal.jbot"
                export GIT_COMMITTER_NAME="$GIT_AUTHOR_NAME"
                export GIT_COMMITTER_EMAIL="$GIT_AUTHOR_EMAIL"
                export NB_USER_NAME="$GIT_AUTHOR_NAME"
                export NB_USER_EMAIL="$GIT_AUTHOR_EMAIL"

                # Call the formally verified standalone launcher
                exec "${jbot-cli}/scripts/jbot-launcher.sh"
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
