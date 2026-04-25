_: {
  programs.jbot = {
    enable = true;
    projectDir = "/home/kodicw/code/jbot";

    agents = {
      lead = {
        enable = true;
        role = "Lead Developer";
        description = "Main autonomous agent managing the JBot project infrastructure and implementation.";
        interval = "hourly"; # 1h
      };
      architect = {
        enable = true;
        role = "Principal Architect";
        description = "Critique architectural decisions, advocate for simplicity, challenge over-engineering, and keep the codebase lean.";
        interval = "*-*-* 00/2:00:00"; # 2h
        dependsOn = [ "lead" ];
      };
      tester = {
        enable = true;
        role = "QA Engineer";
        description = "Verify architectural changes, run tests, and report regressions to the team.";
        interval = "*-*-* 00/4:00:00"; # 4h
        dependsOn = [ "lead" ];
      };
      ceo = {
        enable = true;
        role = "Technical Founder (CEO)";
        description = "Set product vision, prioritize the roadmap in TASKS.md, and ensure architectural decisions align with long-term goals.";
        interval = "*-*-* 00/8:00:00"; # 8h
        dependsOn = [ "architect" ];
      };
    };
  };
}
