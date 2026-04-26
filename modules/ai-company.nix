_: {
  programs.jbot = {
    enable = true;
    projectDir = "/home/kodicw/code/jbot";

    agents = {
      # --- JBot Flat Organization (Core Peers) ---

      lead = {
        enable = true;
        role = "Lead Developer";
        description = "Main coordinator and implementer for core JBot infrastructure.";
        interval = "hourly";
      };

      tester = {
        enable = true;
        role = "QA Engineer";
        description = "Verify feature implementations, run tests, and report regressions.";
        interval = "*-*-* 00/4:00:00";
        dependsOn = [ "lead" ];
      };

      architect = {
        enable = true;
        role = "Principal Architect";
        description = "Review architectural integrity, ensure modularity, and challenge over-engineering.";
        interval = "*-*-* 00/4:00:00";
        dependsOn = [ "lead" ];
      };

      ceo = {
        enable = true;
        role = "Technical Founder (CEO)";
        description = "Set product vision, prioritize the roadmap, and ensure strategic alignment.";
        interval = "*-*-* 00/8:00:00";
        dependsOn = [ "architect" ];
      };
    };
  };
}
