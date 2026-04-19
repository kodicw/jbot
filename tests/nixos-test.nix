{
  pkgs,
  home-manager,
  jbot-module,
  ...
}:
let
  mockGemini = pkgs.writeShellScriptBin "gemini" ''
    # Find the prompt argument
    while [[ $# -gt 0 ]]; do
      case "$1" in
        -p)
          echo "$2" > .test_prompt
          shift 2
          ;;
        *)
          shift
          ;;
      esac
    done
    # Simulate agent writing to memory queue
    echo '{"scope": "local", "status": "success", "summary": "Mock agent ran", "next_step": "Verification"}' > .memory_queue.json
  '';
in
pkgs.testers.nixosTest {
  name = "jbot-test";
  nodes.machine =
    { config, pkgs, ... }:
    {
      imports = [ home-manager.nixosModules.home-manager ];

      users.users.testuser = {
        isNormalUser = true;
        home = "/home/testuser";
      };

      home-manager.useGlobalPkgs = true;
      home-manager.useUserPackages = true;
      home-manager.users.testuser =
        { ... }:
        {
          imports = [ jbot-module ];
          programs.jbot = {
            enable = true;
            projectDir = "/home/testuser/project";
            interval = "*-*-* *:*:*"; # Every second for testing
            geminiPackage = mockGemini;
          };
          home.stateVersion = "23.11";
        };
    };

  testScript = ''
    machine.wait_for_unit("home-manager-testuser.service")
    machine.wait_until_succeeds("systemctl --user -M testuser status jbot-agent.timer")
    
    # Check if the service file contains the expected sandboxing
    machine.succeed("systemctl --user -M testuser cat jbot-agent.service | grep ProtectSystem=strict")
    machine.succeed("systemctl --user -M testuser cat jbot-agent.service | grep ProtectHome=read-only")
    machine.succeed("systemctl --user -M testuser cat jbot-agent.service | grep BindPaths=/home/testuser/project")

    # Initial setup: create project directory and required files
    machine.succeed("mkdir -p /home/testuser/project")
    machine.succeed("echo 'Test Goal' > /home/testuser/project/.project_goal")
    machine.succeed("cp ${../jbot_prompt.txt} /home/testuser/project/jbot_prompt.txt")
    machine.succeed("chown -R testuser:users /home/testuser/project")

    # Start the service manually to trigger the loop
    machine.succeed("systemctl --user -M testuser start jbot-agent.service")
    machine.wait_until_succeeds("test -f /home/testuser/project/.test_prompt")

    # Verify prompt injection
    machine.succeed("grep 'Project Goal: Test Goal' /home/testuser/project/.test_prompt")
    machine.succeed("grep 'Current File Tree: /jbot_prompt.txt' /home/testuser/project/.test_prompt")

    # Verify memory persistence on NEXT run
    # On the first run, mock wrote to .memory_queue.json
    # We need to wait for the service to finish so the loop can move it to .memory.log
    machine.wait_until_succeeds("! systemctl --user -M testuser is-active jbot-agent.service")
    
    # Check if .memory.log was created
    machine.succeed("test -f /home/testuser/project/.memory.log")
    machine.succeed("grep 'Mock agent ran' /home/testuser/project/.memory.log")

    # Trigger second run
    machine.succeed("rm /home/testuser/project/.test_prompt")
    machine.succeed("systemctl --user -M testuser start jbot-agent.service")
    machine.wait_until_succeeds("test -f /home/testuser/project/.test_prompt")

    # Verify memory injection in the second run's prompt
    machine.succeed("grep 'Retrieved Vector Memory:.*Mock agent ran' /home/testuser/project/.test_prompt")
  '';
}
