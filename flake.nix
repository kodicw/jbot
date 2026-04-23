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
      ...
    }:
    flake-utils.lib.eachSystem [ "x86_64-linux" "aarch64-linux" "x86_64-darwin" "aarch64-darwin" ] (
      system:
      let
        pkgs = import nixpkgs { inherit system; };
        jbot-cli = pkgs.callPackage ./pkgs/jbot-cli.nix { scripts = ./scripts; };
      in
      {
        packages.default = jbot-cli;
        packages.jbot-cli = jbot-cli;

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
            pkgs.python3Packages.jinja2
            pkgs.jq
            pkgs.gnugrep
            pkgs.which
            jbot-cli
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

          python-tests =
            pkgs.runCommand "python-tests"
              {
                nativeBuildInputs = [
                  pkgs.python3
                  pkgs.python3Packages.pytest
                  pkgs.python3Packages.pytest-cov
                  pkgs.python3Packages.pytest-mock
                  pkgs.git
                  jbot-cli.python
                ];
              }
              ''
                mkdir -p scripts tests
                cp ${./scripts}/*.py scripts/
                cp ${./tests}/*.py tests/
                export PYTHONPATH=$PYTHONPATH:$(pwd)/scripts
                pytest --cov=scripts --cov-report=term-missing tests/
                touch $out
              '';
        };
      }
    )
    // {
      homeManagerModules = {
        jbot = import ./modules/jbot.nix;
        ai-company = import ./modules/ai-company.nix;
        default = self.homeManagerModules.jbot;
      };
    };
}
