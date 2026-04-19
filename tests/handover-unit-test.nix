{
  pkgs,
  jbot-agent-py,
  jbot-prompt-txt,
  ...
}:
let
  mockGemini = pkgs.writeShellScriptBin "gemini" ''
    # Find the prompt in the arguments (passed via -p)
    PROMPT=""
    while [[ $# -gt 0 ]]; do
      case $1 in
        -p)
          PROMPT="$2"
          shift 2
          ;;
        *)
          shift
          ;;
      esac
    done

    # Save the prompt content for inspection
    mkdir -p .jbot/prompts
    echo "$PROMPT" > ".jbot/prompts/prompt_$AGENT_NAME.txt"
    
    case "$AGENT_NAME" in
      agent1)
        # Verify it's Lead Dev
        if ! echo "$PROMPT" | grep -q "Lead Developer"; then
           echo "Error: agent1 is not Lead Developer in prompt"
           exit 1
        fi
        # Simulate agent1 updating TASKS.md to assign task to agent2
        echo "- [ ] Test task handover (Agent: agent2)" >> TASKS.md
        # Simulate agent1 issuing a directive
        mkdir -p .jbot/directives
        echo "Strictly follow the handover protocol." > .jbot/directives/2026-04-19_protocol.txt
        ;;
      agent2)
        # Verify it sees the task
        if ! echo "$PROMPT" | grep -q "Test task handover (Agent: agent2)"; then
           echo "Error: agent2 did not see its task in prompt"
           exit 1
        fi
        # Verify it sees the directive
        if ! echo "$PROMPT" | grep -q "Strictly follow the handover protocol."; then
           echo "Error: agent2 did not see the directive in prompt"
           exit 1
        fi
        ;;
    esac

    echo '{"scope": "local", "status": "success", "summary": "Finished work as '$AGENT_NAME'", "next_step": "None"}' > "$MEMORY_OUTPUT"
  '';
in
pkgs.runCommand "jbot-handover-unit-test"
{
  nativeBuildInputs = [
    pkgs.python3
    pkgs.coreutils
    pkgs.findutils
    pkgs.jq
    mockGemini
  ];
} ''
  export PROJECT_DIR=$TMPDIR/project
  mkdir -p $PROJECT_DIR
  cd $PROJECT_DIR

  # Initial files
  echo "Goal: Test multi-agent handover and directives" > .project_goal
  echo "# Task Board" > TASKS.md
  mkdir -p .jbot
  echo '{"agent1": {"role": "Lead Dev", "description": "Lead Developer", "projectDir": "'$PROJECT_DIR'"}, "agent2": {"role": "QA", "description": "QA Engineer", "projectDir": "'$PROJECT_DIR'"}}' > .jbot/agents.json

  export PROMPT_FILE="${jbot-prompt-txt}"
  export GEMINI_PACKAGE="gemini"

  # 1. Run agent1 - it will create a task for agent2 and a directive
  export AGENT_NAME="agent1"
  export AGENT_ROLE="Lead Dev"
  export AGENT_DESCRIPTION="Lead Developer"
  export MEMORY_OUTPUT=".jbot/queues/agent1.json"
  python3 ${jbot-agent-py}

  if [ ! -f TASKS.md ] || ! grep -q "Agent: agent2" TASKS.md; then
    echo "Error: TASKS.md was not updated by agent1"
    exit 1
  fi

  if [ ! -f .jbot/directives/2026-04-19_protocol.txt ]; then
    echo "Error: directive was not created by agent1"
    exit 1
  fi

  # 2. Run agent2 - it should see agent1's task and directive in its prompt
  export AGENT_NAME="agent2"
  export AGENT_ROLE="QA"
  export AGENT_DESCRIPTION="QA Engineer"
  export MEMORY_OUTPUT=".jbot/queues/agent2.json"
  python3 ${jbot-agent-py}

  # Verification
  if ! grep -q "agent1" .jbot/memory.log; then
    echo "Error: agent1's memory not found in agent2's consolidated memory log"
    exit 1
  fi

  echo "Multi-agent handover and directives test passed!"
  touch $out
''
