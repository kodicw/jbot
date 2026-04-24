_: {
  programs.jbot = {
    enable = true;
    projectDir = "/home/kodicw/code/jbot";
    
    agents = {
      ceo = {
        enable = true;
        role = "Technical Founder (CEO)";
        description = "Set product vision, prioritize the roadmap in TASKS.md, and ensure architectural decisions align with long-term goals.";
      };
      architect = {
        enable = true;
        role = "Principal Architect";
        description = "Critique architectural decisions, advocate for simplicity, challenge over-engineering, and keep the codebase lean.";
        dependsOn = [ "ceo" ];
      };
      lead = {
        enable = true;
        role = "Lead Developer";
        description = "Main autonomous agent managing the JBot project infrastructure and implementation.";
        dependsOn = [ "architect" ];
      };
      tester = {
        enable = true;
        role = "QA Engineer";
        description = "Verify architectural changes, run tests, and report regressions to the team.";
        dependsOn = [ "lead" ];
      };
    };
  };
}
