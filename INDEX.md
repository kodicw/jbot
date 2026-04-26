# JBot Dashboard

*Last Updated: 2026-04-26 16:03:44*

## 🎯 Strategic Vision
> **Autonomous, Multi-Agent Engineering on NixOS with Technical Purity.**

## 👥 Team Roster
| Agent | Role | Description |
|-------|------|-------------|
| architect | Principal Architect | Review feature specialization logic, ensure modularity, and challenge over-engineering. |
| ceo | Technical Founder (CEO) | Set product vision, prioritize the roadmap, and ensure all specialized agents align with long-term goals. |
| dev-alignment | Alignment Specialist | Ensure technical implementations perfectly map to strategic goals and formal directives in nb. |
| dev-cleanup | Maintenance Engineer (Janitor) | Proactively prune unused Nix code, stale memory notes, and technical debt using purity tools. |
| dev-docs | Technical Writer | Maintain high-density documentation, Mermaid diagrams, and ADR clarity across the repo. |
| dev-memory | Memory Specialist | Expert in RAG, knowledge base (nb) integration, and memory consolidation logic. |
| dev-research | Research Specialist | Investigate new AI models, NixOS patterns, and emerging technologies to keep the organization at the cutting edge. |
| dev-scheduler | Scheduling Specialist | Expert in systemd integration, agent orchestration, and NixOS module design. |
| lead | Lead Developer | Main coordinator and implementer for core JBot infrastructure. |
| manager | Conflict & Alignment Manager | Monitor agent outputs for strategic drift or non-compliance. Intervene when specialized agents fail to align with the organization's goals. |
| tester | QA Engineer | Verify specialized feature implementations, run tests, and report regressions. |

## 🚀 Active Tasks
- [ ] **Achieve 100% test coverage across all Python modules and Nix derivations** [tester]
- [ ] **Audit codebase for 'Self-Documenting Code' compliance** [architect]

## 📦 Backlog Highlights
- [ ] **Docker-based test runner for faster verification cycles** (Agent: tester)
- [ ] **Document external isolation and multi-user NixOS patterns in `README.md`** (Agent: architect)
- [ ] **Enforce single Linux user account constraint in `jbot.nix` and `flake.nix`** (Agent: lead)
- [ ] **Enhance agent-to-agent message threading in dashboard** (Agent: architect)
- [ ] **Implement automated PR generation for infrastructure updates**

## ✅ Recently Completed
- [x] **Audit hierarchical logic and prune redundant code** (Agent: architect)
- [x] **Automated memory rotation integration and locking** (Agent: lead)
- [x] **Consolidate rotation scripts into unified module** (Agent: lead)
- [x] **Establish and implement Architecture Visualization in INDEX.md dashboard** (Agent: architect)
- [x] **Finalize and Verify Stateless Agent Execution Model** (Agent: architect)

## 📜 Recent ADRs
- [[nb:85]] ADR: Knowledge Base Structure (adr/, research/, benchmarks/)
- [[nb:57]] ADR: Per-Task Note Model for Scaling
- [[nb:53]] Reflection: [lead] - Evaluation of Flat Scaling Efficiency and Tool Robustness
- [[nb:51]] Knowledge Base Guide (nb)
- [[nb:49]] Reflection: [architect] - Architectural Evaluation of Flat Scaling Efficiency

## 📊 Architectural Diagrams
### Jbot Agent
```mermaid
graph TD
    A[Start Agent] --> B[Initialize Environment]
    B --> C[Assemble Context]
    C --> D[Execute AI CLI]
    D --> E[Verify Changes]
    E --> F[End Agent]

    subgraph "Context Assembly (nb-driven)"
        C1[Get System Prompt]
        C2[Get Directives & ADRs]
        C3[Get Task Board]
        C4[Get Git Status & Tree]
        C5[Get Shared Memory Logs]
        C6[Get Messages]
        C1 --> C_ALL[Combine into Jinja2 Template]
        C2 --> C_ALL
        C3 --> C_ALL
        C4 --> C_ALL
        C5 --> C_ALL
        C6 --> C_ALL
    end

    subgraph "Verification"
        E1[Run .githooks/pre-commit]
        E2[Check Exit Code]
    end
```

### Jbot Infra
```mermaid
graph TD
    A[Start Maintenance] --> B[Initialize Infrastructure]
    B --> C[Consolidate Messages]
    C --> D[Consolidate Memory]
    D --> E[Perform Rotations]
    E --> F[Generate Dashboard]
    F --> G[End Maintenance]

    subgraph Initialize
        B1[Create .jbot/queues]
        B2[Create .jbot/messages]
        B3[Create .jbot/directives]
        B4[Create .jbot/outbox]
    end

    subgraph Consolidate
        C1[Move outbox/*.txt to messages/]
        D1[Parse agent queues/*.json]
        D2[Push memory to nb knowledge base]
    end

    subgraph Rotate
        E1[Archive expired directives]
        E2[Rotate old messages]
        E3[Rotate nb notes by tag]
    end
```

### Jbot Tasks
```mermaid
graph TD
    A[Task Operation] --> B{Fetch Task Board}
    B -->|get_note_content| C[Parse Markdown]
    C --> D{Perform Action}
    D -->|add_task| E[Insert into Section]
    D -->|update_task| F[Modify Line]
    D -->|complete_task| G[Move to Completed]
    E --> H[Push to nb]
    F --> H
    G --> H

    subgraph Parsing
        C1[Split into Lines]
        C2[Identify ## Sections]
        C3[Extract Vision/Active/Backlog]
        C4[Count Done Tasks]
    end

    subgraph "Push (nb-aware)"
        H1[Find Stable ID 5]
        H2[nb edit ID]
        H3[Fallback: nb add]
    end
```

## 📈 Status & Progress
- **Tasks Completed:** 15
- **Milestones Achieved:** 18

### 📊 Technical ROI (Engineering Metrics)
- **Engineering Velocity:** 0.83 tasks/milestone
- **Architectural Density:** 0.61 ADRs/milestone
- **Knowledge Base Growth:** 53 records
- **Completion Ratio:** 68.2%

## ✅ Recent Milestones
- **Architectural Evaluation of Flat Scaling:** Validated the efficiency of the flat organization model and single-user sandbox for long-term technical purity (ADR-210).
- **Flat Organization Scaling Efficiency (ADR-210):** Implemented granular per-task note model and increased ADR retention to 50 for long-term stability.
- **NB Client Robustness:** Fixed pagination issues in `NbClient.ls` by ensuring the `-a` flag is used for tag-based listings.
- **Infrastructure CLI Integration:** Integrated `maintenance`, `purge`, `rotate`, `dashboard`, and `send-message` as subcommands in the `jbot` CLI.
- **Modularized Infrastructure Logic:** Moved core logic for purging, rotation, and dashboard generation into `scripts/jbot_utils.py` for architectural purity.

