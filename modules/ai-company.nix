_: {
  programs.jbot = {
    enable = true;
    projectDir = "/home/kodicw/code/jbot";

    agents = {
      # --- IMPLEMENTATION TIER (1h) ---
      lead = {
        enable = true;
        role = "Lead Developer";
        description = "Main coordinator and implementer for core JBot infrastructure.";
        interval = "hourly";
      };

      # --- FEATURE SPECIALISTS (2h) ---
      dev-memory = {
        enable = true;
        role = "Memory Specialist";
        description = "Expert in RAG, knowledge base (nb) integration, and memory consolidation logic.";
        interval = "*-*-* 00/2:00:00";
        dependsOn = [ "lead" ];
      };

      dev-scheduler = {
        enable = true;
        role = "Scheduling Specialist";
        description = "Expert in systemd integration, agent orchestration, and NixOS module design.";
        interval = "*-*-* 00/2:00:00";
        dependsOn = [ "lead" ];
      };

      dev-research = {
        enable = true;
        role = "Research Specialist";
        description = "Investigate new AI models, NixOS patterns, and emerging technologies to keep the organization at the cutting edge.";
        interval = "*-*-* 00/2:00:00";
        dependsOn = [ "lead" ];
      };

      # --- STRATEGIC SUPPORT (2h) ---
      dev-alignment = {
        enable = true;
        role = "Alignment Specialist";
        description = "Ensure technical implementations perfectly map to strategic goals and formal directives in nb.";
        interval = "*-*-* 01/2:00:00";
        dependsOn = [ "lead" ];
      };

      dev-docs = {
        enable = true;
        role = "Technical Writer";
        description = "Maintain high-density documentation, Mermaid diagrams, and ADR clarity across the repo.";
        interval = "*-*-* 01/2:00:00";
        dependsOn = [ "lead" ];
      };

      dev-cleanup = {
        enable = true;
        role = "Maintenance Engineer (Janitor)";
        description = "Proactively prune unused Nix code, stale memory notes, and technical debt using purity tools.";
        interval = "*-*-* 01/2:00:00";
        dependsOn = [ "lead" ];
      };

      # --- VERIFICATION & MANAGEMENT TIER (4h) ---
      tester = {
        enable = true;
        role = "QA Engineer";
        description = "Verify specialized feature implementations, run tests, and report regressions.";
        interval = "*-*-* 00/4:00:00";
        dependsOn = [
          "dev-memory"
          "dev-scheduler"
          "dev-cleanup"
        ];
      };

      architect = {
        enable = true;
        role = "Principal Architect";
        description = "Review feature specialization logic, ensure modularity, and challenge over-engineering.";
        interval = "*-*-* 00/4:00:00";
        dependsOn = [
          "dev-alignment"
          "dev-docs"
          "dev-research"
        ];
      };

      manager = {
        enable = true;
        role = "Conflict & Alignment Manager";
        description = "Monitor agent outputs for strategic drift or non-compliance. Intervene when specialized agents fail to align with the organization's goals.";
        interval = "*-*-* 00/4:00:00";
        dependsOn = [ "dev-alignment" ];
      };

      # --- STRATEGIC TIER (8h) ---
      ceo = {
        enable = true;
        role = "Technical Founder (CEO)";
        description = "Set product vision, prioritize the roadmap, and ensure all specialized agents align with long-term goals.";
        interval = "*-*-* 00/8:00:00";
        dependsOn = [
          "architect"
          "manager"
        ];
      };
    };
  };
}
