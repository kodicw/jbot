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
            pkgs.ruff
            pkgs.gemini-cli
            pkgs.python3
            pkgs.python3Packages.pytest
            pkgs.python3Packages.pytest-cov
            pkgs.python3Packages.pytest-mock
            pkgs.jq
          ];

          shellHook = ''
            git config core.hooksPath .githooks
            echo "Git hooks activated from .githooks/"
          '';
        };

        checks = {
          # Format & Lint Checks
          nixfmt-check = pkgs.runCommand "nixfmt-check" { nativeBuildInputs = [ pkgs.nixfmt-rfc-style ]; } ''
            find ${./.} -name "*.nix" -not -path "*/.*" -exec nixfmt --check {} +
            touch $out
          '';
          statix-check = pkgs.runCommand "statix-check" { nativeBuildInputs = [ pkgs.statix ]; } ''
            statix check ${./.}
            touch $out
          '';
          ruff-check = pkgs.runCommand "ruff-check" { nativeBuildInputs = [ pkgs.ruff ]; } ''
            ruff check ${./.}
            ruff format --check ${./.}
            touch $out
          '';

          python-tests = pkgs.runCommand "python-tests" { 
            nativeBuildInputs = [ 
              pkgs.python3 
              pkgs.python3Packages.pytest 
              pkgs.python3Packages.pytest-cov 
              pkgs.python3Packages.pytest-mock
              pkgs.git
            ]; 
          } ''
            mkdir -p scripts tests
            cp ${./scripts}/*.py scripts/
            cp ${./tests}/*.py tests/
            export PYTHONPATH=$PYTHONPATH:$(pwd)/scripts
            # Run pytest on all python tests with coverage for the scripts directory
            pytest --cov=scripts --cov-report=term-missing tests/
            touch $out
          '';

          unit-test = pkgs.callPackage ./tests/unit-test.nix {
            jbot-scripts = ./scripts;
            jbot_prompt_txt = ./jbot_prompt.txt;
          };
          multi-agent-unit-test = pkgs.callPackage ./tests/multi-agent-unit-test.nix {
            jbot-scripts = ./scripts;
            jbot_prompt_txt = ./jbot_prompt.txt;
          };
          handover-unit-test = pkgs.callPackage ./tests/handover-unit-test.nix {
            jbot-scripts = ./scripts;
            jbot_prompt_txt = ./jbot_prompt.txt;
          };
          directive-expiration-test = pkgs.callPackage ./tests/directive-expiration-test.nix {
            jbot-scripts = ./scripts;
            jbot_prompt_txt = ./jbot_prompt.txt;
          };
          directive-purge-test = pkgs.callPackage ./tests/directive-purge-test.nix {
            jbot-purge-py = ./scripts/jbot-purge.py;
          };
          memory-rotation-test = pkgs.callPackage ./tests/memory-rotation-test.nix {
            jbot-rotate-py = ./scripts/jbot-rotate.py;
          };
          task-rotation-test = pkgs.callPackage ./tests/task-rotation-test.nix {
            jbot-rotate-tasks-py = ./scripts/jbot-rotate-tasks.py;
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
