{ config, pkgs, ... }:
{
  # Example configuration for a JBot "Company" structure.
  # This can be included in your home.nix or another Home Manager module.

  programs.jbot = {
    enable = true;
    agents = {
      # The CEO agent oversees project goals and assigns tasks.
      ceo = {
        enable = true;
        role = "CEO";
        description = "Strategic visionary. Defines project goals and oversees team execution.";
        projectDir = "/home/youruser/yourproject";
        interval = "daily";
      };

      # The Lead Developer manages the infrastructure and architecture.
      lead = {
        enable = true;
        role = "Lead Developer";
        description = "Core architect and lead developer. Implements foundational infrastructure.";
        projectDir = "/home/youruser/yourproject";
        interval = "hourly";
        supervisor = "ceo"; # Reports to the CEO
        dependsOn = [ "ceo" ];
      };

      # The QA Engineer verifies changes and ensures quality.
      tester = {
        enable = true;
        role = "QA Engineer";
        description = "Quality Assurance. Verifies features and reports regressions.";
        projectDir = "/home/youruser/yourproject";
        interval = "hourly";
        supervisor = "ceo"; # Reports to the CEO
        dependsOn = [ "lead" ]; # Waits for lead developer to finish changes
      };
    };
  };
}
