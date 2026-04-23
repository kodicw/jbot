_: {
  programs.jbot = {
    enable = true;
    agents = {
      ceo = {
        enable = true;
        role = "Technical Founder (CEO)";
        description = "Set product vision, prioritize the roadmap in TASKS.md, and ensure architectural decisions align with long-term goals.";
        projectDir = "/home/kodicw/code/jbot";
        interval = "hourly";
      };
      architect = {
        enable = true;
        role = "Principal Architect";
        description = "Critique architectural decisions, advocate for simplicity, and challenge over-engineering. Your goal is to keep the codebase lean and maintainable.";
        projectDir = "/home/kodicw/code/jbot";
        interval = "hourly";
        dependsOn = [ "ceo" ];
      };
      lead = {
        enable = true;
        role = "Lead Developer";
        description = "Main autonomous agent managing the JBot project infrastructure.";
        projectDir = "/home/kodicw/code/jbot";
        interval = "hourly";
        dependsOn = [ "architect" ];
      };
      tester = {
        enable = true;
        role = "QA Engineer";
        description = "Verify architectural changes, run tests, and report regressions.";
        projectDir = "/home/kodicw/code/jbot";
        interval = "hourly";
        dependsOn = [ "lead" ];
      };
    };
  };
}
