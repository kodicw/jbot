import os
import subprocess
import jbot_core as core
import jbot_infra as infra
import jbot_utils as utils
from jbot_memory_interface import get_memory_client


def init_project(project_dir: str, name: str = None) -> bool:
    """
    Initializes a new JBot organization project.

    Context: [[nb:jbot:115]], [[nb:jbot:116]]
    """
    if not name:
        name = os.path.basename(os.path.abspath(project_dir))

    core.log(f"Initializing JBot organization: {name} in {project_dir}", "Init")

    # 1. Create Infrastructure Directories
    infra.initialize_infrastructure(project_dir)

    # 2. Initialize .jbot/notebook if it doesn't exist
    nb_path = os.path.join(project_dir, ".jbot/notebook")
    if not os.path.exists(nb_path):
        os.makedirs(nb_path, exist_ok=True)
        # We don't necessarily need 'nb notebooks init' if we use 'nb notebooks add'

    # Register the notebook globally so it's accessible by name
    try:
        core.log(f"Registering nb notebook '{name}' at {nb_path}", "Init")
        # Check if it already exists
        res = subprocess.run(
            ["nb", "notebooks", "show", name], capture_output=True, text=True
        )
        if res.returncode != 0:
            subprocess.run(["nb", "notebooks", "add", name, nb_path], check=True)
    except Exception as e:
        core.log(f"Warning: Failed to register nb notebook: {e}", "Init")

    # 3. Create .jbot/notebook local config
    core.write_file(os.path.join(project_dir, ".jbot/notebook"), name)

    # 4. Create .project_goal
    goal_path = os.path.join(project_dir, ".project_goal")
    if not os.path.exists(goal_path):
        default_goal = (
            f"# {name.title()} Project Goal\n\nDefine your strategic vision here."
        )
        core.write_file(goal_path, default_goal)

    # 5. Create .jbot/agents.json
    agents_path = os.path.join(project_dir, ".jbot/agents.json")
    if not os.path.exists(agents_path):
        default_agents = {
            "ceo": {
                "role": "CEO",
                "description": "Strategic visionary. Defines project goals and oversees team execution.",
            },
            "lead": {
                "role": "Lead Developer",
                "description": "Core lead developer. Implements foundational infrastructure.",
            },
        }
        core.save_json(agents_path, default_agents)

    # 6. Create VERSION and CHANGELOG.md
    version_path = os.path.join(project_dir, "VERSION")
    if not os.path.exists(version_path):
        core.write_file(version_path, "0.1.0")

    changelog_path = os.path.join(project_dir, "CHANGELOG.md")
    if not os.path.exists(changelog_path):
        default_changelog = f"# Changelog\n\nAll notable changes to this project will be documented in this file.\n\n## [Unreleased]\n\n### Added\n- Initialized JBot organization '{name}'.\n"
        core.write_file(changelog_path, default_changelog)

    # 7. Create flake.nix template
    flake_path = os.path.join(project_dir, "flake.nix")
    if not os.path.exists(flake_path):
        flake_template = """{
  description = "A new JBot AI organization";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
    jbot.url = "github:kodicw/jbot"; # Point to the core jbot repository
  };

  outputs = { self, nixpkgs, flake-utils, jbot, ... }:
    flake-utils.lib.eachSystem [ "x86_64-linux" "aarch64-linux" ] (system:
      let
        pkgs = import nixpkgs { inherit system; };
      in
      {
        devShells.default = pkgs.mkShell {
          packages = [
            jbot.packages.${system}.default
            pkgs.nb
            pkgs.git
          ];
        };
      }
    );
}
"""
        core.write_file(flake_path, flake_template)

    # 8. Push Initial Notes to Technical Memory (nb)
    try:
        env = os.environ.copy()
        env["JBOT_NOTEBOOK"] = name
        client = get_memory_client(env=env)

        # Push Goal
        client.add(
            f"Vision: {name.title()}",
            f"#type:goal\n\n{core.read_file(goal_path)}",
            tags=["type:goal", "vision"],
        )

        # Push Team Registry
        agents = core.load_json(agents_path)
        team_content = "# Team Registry\n\n"
        for agent_name, info in agents.items():
            team_content += (
                f"- **{agent_name}**: {info['role']} ({info['description']})\n"
            )
        client.add("Team Registry", team_content, tags=["type:registry", "team"])

        core.log("Initial notes pushed to technical memory.", "Init")
    except Exception as e:
        core.log(f"Warning: Failed to push initial notes to nb: {e}", "Init")

    # 9. Generate Initial Dashboard
    utils.generate_dashboard(project_dir=project_dir)

    core.log(f"Successfully initialized JBot organization '{name}'.", "Init")
    return True
