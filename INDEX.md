# JBot Dashboard

*Last Updated: 2026-04-26 16:08:27*

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
- [ ] **Enhance agent-to-agent message threading in dashboard** (Agent: architect)
- [ ] **Markdown Scratchpads: document intent in hidden directory before execution**

## ✅ Recently Completed
- [x] **Audit hierarchical logic and prune redundant code** (Agent: architect)
- [x] **Automated memory rotation integration and locking** (Agent: lead)
- [x] **Consolidate rotation scripts into unified module** (Agent: lead)
- [x] **Enforce single Linux user account constraint in `jbot.nix` and `flake.nix`** (Agent: lead)
- [x] **Establish and implement Architecture Visualization in INDEX.md dashboard** (Agent: architect)

## 📜 Recent ADRs
- [[nb:85]] ADR: Knowledge Base Structure (adr/, research/, benchmarks/)
- [[nb:57]] ADR: Per-Task Note Model for Scaling
- [[nb:53]] Reflection: [lead] - Evaluation of Flat Scaling Efficiency and Tool Robustness
- [[nb:49]] Reflection: [architect] - Architectural Evaluation of Flat Scaling Efficiency
- [[nb:7]] ADR: Environment and Tool Registry

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

### Jbot Rotation
```mermaid
graph TD
    A[Start Rotation Loop] --> B[Purge Directives]
    B --> C[Rotate Messages]
    C --> D[Rotate nb Notes]
    D --> E[End Rotation]

    subgraph "Purge Directives"
        B1[Check Expiration Date]
        B2{Expired?}
        B2 -->|Yes| B3[Move to archive/]
        B2 -->|No| B4[Keep in directives/]
    end

    subgraph "Rotate Messages"
        C1[List .jbot/messages]
        C2{Count > Limit?}
        C2 -->|Yes| C3[Move oldest to archive/]
    end

    subgraph "Rotate NB (Knowledge Base)"
        D1[Filter by Tag]
        D2[Sort by Stable ID Desc]
        D3{Count > Tag Limit?}
        D3 -->|Yes| D4[Delete Oldest Notes]
        D1 --> D1_ADR[ADR Limit: 50]
        D1 --> D1_MEM[Memory Limit: 10]
    end
```

### Jbot Tasks
```mermaid
graph TD
    A[Task Operation] --> B{Fetch Task Data}
    B --> B1[Fetch Strategic Vision]
    B --> B2[Fetch Granular Tasks]
    B2 -->|nb ls tags:type:task| C[Process Each Task Note]
    C --> D{Action Type}
    
    D -->|add_task| E[Create New Task Note]
    D -->|update_task| F[Update Task Note]
    D -->|complete_task| G[Mark Note Completed]
    
    E -->|nb add| H[Update Technical Memory]
    F -->|nb edit| H
    G -->|nb edit status| H
    
    subgraph "Granular Per-Task Model"
        C1[Check status:active/backlog/completed]
        C2[Extract Agent Assignments]
        C1 --> C
        C2 --> C
    end
    
    subgraph "Strategic Alignment"
        B1 -->|nb show type:vision| S1[Parse Vision Section]
    end
```

## 📈 Status & Progress
- **Tasks Completed:** 16
- **Milestones Achieved:** 18

### 📊 Technical ROI (Engineering Metrics)
- **Engineering Velocity:** 0.89 tasks/milestone
- **Architectural Density:** 0.56 ADRs/milestone
- **Knowledge Base Growth:** 54 records
- **Completion Ratio:** 72.7%

## ✅ Recent Milestones
- **Architectural Evaluation of Flat Scaling:** Validated the efficiency of the flat organization model and single-user sandbox for long-term technical purity (ADR-210).
- **Flat Organization Scaling Efficiency (ADR-210):** Implemented granular per-task note model and increased ADR retention to 50 for long-term stability.
- **NB Client Robustness:** Fixed pagination issues in `NbClient.ls` by ensuring the `-a` flag is used for tag-based listings.
- **Infrastructure CLI Integration:** Integrated `maintenance`, `purge`, `rotate`, `dashboard`, and `send-message` as subcommands in the `jbot` CLI.
- **Modularized Infrastructure Logic:** Moved core logic for purging, rotation, and dashboard generation into `scripts/jbot_utils.py` for architectural purity.

