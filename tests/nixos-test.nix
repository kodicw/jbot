{
  pkgs,
  home-manager,
  jbot-module,
  ...
}:
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
  '';
}
