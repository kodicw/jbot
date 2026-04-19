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
            jbot-prompt-txt = ./jbot_prompt.txt;
          };
        } // lib.optionalAttrs (pkgs.stdenv.isLinux && (builtins.getEnv "SKIP_VM_TESTS" != "1")) {
          nixos-test = pkgs.callPackage ./tests/nixos-test.nix {
            home-manager = self.inputs.home-manager;
            jbot-module = self.homeManagerModules.default;
          };
        };
      }
    ) // {
      homeManagerModules.default = import ./jbot.nix;
    };
}
