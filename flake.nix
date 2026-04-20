{
  description = "JBot — Nix-based AI agent scheduler and Home Manager module";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
    home-manager = {
      url = "github:nix-community/home-manager";
      inputs.nixpkgs.follows = "nixpkgs";
    };
  };

  outputs =
    {
      self,
      nixpkgs,
      flake-utils,
      home-manager,
    }:
    flake-utils.lib.eachSystem [ "x86_64-linux" "aarch64-linux" "x86_64-darwin" "aarch64-darwin" ] (
      system:
      let
        pkgs = import nixpkgs { inherit system; };
        inherit (pkgs) lib;
      in
      {
        devShells.default = pkgs.mkShell {
          packages = [
            pkgs.nixfmt-rfc-style
            pkgs.statix
            pkgs.gemini-cli
            pkgs.python3
            pkgs.jq
          ];
        };

        checks = {
          unit-test = pkgs.callPackage ./tests/unit-test.nix {
            jbot-agent-py = ./jbot-agent.py;
            jbot-dashboard-py = ./jbot-dashboard.py;
            jbot-prompt-txt = ./jbot_prompt.txt;
          };
          multi-agent-unit-test = pkgs.callPackage ./tests/multi-agent-unit-test.nix {
            jbot-agent-py = ./jbot-agent.py;
            jbot-dashboard-py = ./jbot-dashboard.py;
            jbot-prompt-txt = ./jbot_prompt.txt;
          };
          handover-unit-test = pkgs.callPackage ./tests/handover-unit-test.nix {
            jbot-agent-py = ./jbot-agent.py;
            jbot-dashboard-py = ./jbot-dashboard.py;
            jbot-prompt-txt = ./jbot_prompt.txt;
          };
          directive-expiration-test = pkgs.callPackage ./tests/directive-expiration-test.nix {
            jbot-agent-py = ./jbot-agent.py;
            jbot-dashboard-py = ./jbot-dashboard.py;
            jbot-prompt-txt = ./jbot_prompt.txt;
          };
          directive-purge-test = pkgs.callPackage ./tests/directive-purge-test.nix {
            jbot-purge-py = ./jbot-purge.py;
          };
          memory-rotation-test = pkgs.callPackage ./tests/memory-rotation-test.nix {
            jbot-rotate-py = ./jbot-rotate.py;
          };
          task-rotation-test = pkgs.callPackage ./tests/task-rotation-test.nix {
            jbot-rotate-tasks-py = ./jbot-rotate-tasks.py;
          };
        }
        // lib.optionalAttrs (pkgs.stdenv.isLinux && (builtins.getEnv "SKIP_VM_TESTS" != "1")) {
          nixos-test = pkgs.callPackage ./tests/nixos-test.nix {
            inherit (self.inputs) home-manager;
            jbot-module = self.homeManagerModules.default;
          };
        };
      }
    )
    // {
      homeManagerModules.default = import ./jbot.nix;
    };
}
